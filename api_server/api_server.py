# ============================================================================
# api_server.py - Ports 8080 & 9001 - Query telemetry data
# ============================================================================

from flask import Flask, request, jsonify, Response

from contextlib import closing
import logging
import time
from threading import Thread
import io
import csv
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from telemetry_db.telemetry_db import TelemetryDb

app_api = Flask(__name__)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('api_server')

# Performance tracking
api_stats = {
    'get_metric_requests': 0,
    'get_metric_time': 0,
    'list_metrics_requests': 0,
    'list_metrics_time': 0,
    'counters_requests': 0,
    'counters_time': 0,
    'errors': 0
}


# ==================== Port 8080 Endpoints ====================

@app_api.route('/telemetry/GetMetric', methods=['GET'])
def get_metric():
    """Get latest value for a specific metric"""
    start_time = time.time()
    api_stats['get_metric_requests'] += 1

    try:
        metric_name = request.args.get('name')
        server_name = request.args.get('server')

        if not metric_name or not server_name:
            api_stats['errors'] += 1
            return jsonify({'error': 'Metric and server name parameters are required'}), 400

        with closing(TelemetryDb.get_db()) as conn:
            with closing(conn.cursor()) as cursor:
                cursor.execute('''
                    SELECT md.metric_name, md.unit, mv.server_name, mv.value, mv.timestamp
                    FROM metric_values mv
                    JOIN metric_definitions md ON mv.metric_id = md.id
                    WHERE (md.metric_name = ? ) AND (mv.server_name = ?)
                    ORDER BY mv.timestamp DESC
                    LIMIT 1
                ''', (metric_name,server_name,))

                result = cursor.fetchone()

        elapsed = time.time() - start_time
        api_stats['get_metric_time'] += elapsed

        if not result:
            logger.warning(f"Metric not found: {metric_name} ({elapsed:.4f}s)")
            return jsonify({'error': 'Metric not found'}), 404

        response = {
            'metric_name': result['metric_name'],
            'unit': result['unit'],
            'server_name': result['server_name'],
            'value': result['value'],
            'timestamp': result['timestamp']
        }

        logger.info(f"GetMetric: {metric_name} ({elapsed:.4f}s)")
        return jsonify(response), 200

    except Exception as e:
        api_stats['errors'] += 1
        logger.error(f"GetMetric error: {str(e)}")
        return jsonify({'error': str(e)}), 500


@app_api.route('/telemetry/ListMetrics', methods=['GET'])
def list_metrics():
    """
    Fetch a list of metric values for all switches/servers, grouped by metric
    """
    start_time = time.time()
    api_stats['list_metrics_requests'] += 1

    try:
        with closing(TelemetryDb.get_db()) as conn:
            with closing(conn.cursor()) as cursor:
                # Get all metrics with their latest values for each server
                cursor.execute('''
                    SELECT 
                        md.metric_name,
                        md.unit,
                        mv.server_name,
                        mv.value,
                        mv.timestamp
                    FROM metric_definitions md
                    LEFT JOIN metric_values mv ON md.id = mv.metric_id
                    WHERE mv.id IN (
                        SELECT MAX(id)
                        FROM metric_values
                        GROUP BY metric_id, server_name
                    )
                    ORDER BY md.metric_name, mv.server_name
                ''')

                results = cursor.fetchall()

        # Group results by metric
        metrics_dict = {}
        for row in results:
            metric_name = row['metric_name']
            if metric_name not in metrics_dict:
                metrics_dict[metric_name] = {
                    'metric_name': metric_name,
                    'unit': row['unit'],
                    'values': []
                }

            metrics_dict[metric_name]['values'].append({
                'server_name': row['server_name'],
                'value': row['value'],
                'timestamp': row['timestamp']
            })

        metrics_list = list(metrics_dict.values())

        elapsed = time.time() - start_time
        api_stats['list_metrics_time'] += elapsed

        total_values = sum(len(m['values']) for m in metrics_list)
        logger.info(f"ListMetrics: {len(metrics_list)} metrics with {total_values} values ({elapsed:.4f}s)")

        return jsonify({'metrics': metrics_list}), 200

    except Exception as e:
        api_stats['errors'] += 1
        logger.error(f"ListMetrics error: {str(e)}")
        return jsonify({'error': str(e)}), 500


# ==================== Port 9001 Endpoints ====================

@app_api.route('/counters', methods=['GET'])
def get_counters():
    """
    Export telemetry data as CSV
    """
    start_time = time.time()
    api_stats['counters_requests'] += 1

    try:
        server_name = request.args.get('server')

        with closing(TelemetryDb.get_db()) as conn:
            with closing(conn.cursor()) as cursor:

                if server_name:
                    # Format: timestamp as rows, metrics as columns (for specific server)
                    # Get all unique timestamps for this server
                    cursor.execute('''
                        SELECT DISTINCT timestamp
                        FROM metric_values
                        WHERE (server_name = ? and metric_id = (
                        ORDER BY timestamp
                    ''', (server_name,))
                    timestamps = [row['timestamp'] for row in cursor.fetchall()]

                    # Get all metrics
                    cursor.execute('SELECT metric_name FROM metric_definitions ORDER BY metric_name')
                    metrics = [row['metric_name'] for row in cursor.fetchall()]

                    # Get all data for this server
                    cursor.execute('''
                        SELECT md.metric_name, mv.timestamp, mv.value
                        FROM metric_values mv
                        JOIN metric_definitions md ON mv.metric_id = md.id
                        WHERE mv.server_name = ?
                    ''', (server_name,))

                    # Build data dictionary
                    data_dict = {}
                    for row in cursor.fetchall():
                        key = (row['timestamp'], row['metric_name'])
                        data_dict[key] = row['value']

                    # Create CSV
                    output = io.StringIO()
                    writer = csv.writer(output)

                    # Header
                    writer.writerow(['timestamp'] + metrics)

                    # Data rows
                    for ts in timestamps:
                        row = [ts]
                        for metric in metrics:
                            value = data_dict.get((ts, metric), '')
                            row.append(value)
                        writer.writerow(row)

                else:
                    # Format: server_name + timestamp as rows, metrics as columns (all servers)
                    # Get all unique server+timestamp combinations
                    cursor.execute('''
                        SELECT DISTINCT server_name, timestamp
                        FROM metric_values
                        ORDER BY server_name, timestamp
                    ''')
                    server_timestamps = [(row['server_name'], row['timestamp']) for row in cursor.fetchall()]

                    # Get all metrics
                    cursor.execute('SELECT metric_name FROM metric_definitions ORDER BY metric_name')
                    metrics = [row['metric_name'] for row in cursor.fetchall()]

                    # Get all data
                    cursor.execute('''
                        SELECT md.metric_name, mv.server_name, mv.timestamp, mv.value
                        FROM metric_values mv
                        JOIN metric_definitions md ON mv.metric_id = md.id
                    ''')

                    # Build data dictionary
                    data_dict = {}
                    for row in cursor.fetchall():
                        key = (row['server_name'], row['timestamp'], row['metric_name'])
                        data_dict[key] = row['value']

                    # Create CSV
                    output = io.StringIO()
                    writer = csv.writer(output)

                    # Header
                    writer.writerow(['server_name', 'timestamp'] + metrics)

                    # Data rows
                    for server, ts in server_timestamps:
                        row = [server, ts]
                        for metric in metrics:
                            value = data_dict.get((server, ts, metric), '')
                            row.append(value)
                        writer.writerow(row)

                csv_data = output.getvalue()
                output.close()

        elapsed = time.time() - start_time
        api_stats['counters_time'] += elapsed

        logger.info(f"Counters: server={server_name or 'all'} ({elapsed:.4f}s)")

        return Response(
            csv_data,
            mimetype='text/csv',
            headers={'Content-Disposition': f'attachment; filename=counters_{server_name or "all"}.csv'}
        )

    except Exception as e:
        api_stats['errors'] += 1
        logger.error(f"Counters error: {str(e)}")
        return jsonify({'error': str(e)}), 500


@app_api.route('/stats', methods=['GET'])@app_api.route('/stats', methods=['GET'])
def get_api_stats():
    """Return API performance statistics as JSON.

    The response includes per-endpoint totals and average latencies (in milliseconds),
    computed from the cumulative timing and request counters stored in the module-level
    `api_stats` dictionary.

    Response format:
    {
        "GetMetric": {
            "total_requests": int,
            "avg_latency_ms": float
        },
        "ListMetrics": {
            "total_requests": int,
            "avg_latency_ms": float
        },
        "Counters": {
            "total_requests": int,
            "avg_latency_ms": float
        },
        "total_errors": int
    }

    Note: Average latencies are 0 when the corresponding request count is 0 to avoid
    division-by-zero.
    """
    stats = {
        'GetMetric': {
            'total_requests': api_stats['get_metric_requests'],
            'avg_latency_ms': round(api_stats['get_metric_time'] / api_stats['get_metric_requests'] * 1000, 2) if
            api_stats['get_metric_requests'] > 0 else 0
        },
        'ListMetrics': {
            'total_requests': api_stats['list_metrics_requests'],
            'avg_latency_ms': round(api_stats['list_metrics_time'] / api_stats['list_metrics_requests'] * 1000, 2) if
            api_stats['list_metrics_requests'] > 0 else 0
        },
        'Counters': {
            'total_requests': api_stats['counters_requests'],
            'avg_latency_ms': round(api_stats['counters_time'] / api_stats['counters_requests'] * 1000, 2)
                if api_stats['counters_requests'] > 0 else 0
        },
        'total_errors': api_stats['errors']
    }
    return jsonify(stats)



def run_on_port(port):
    """Run Flask app on specific port"""
    app_api.run(host='127.0.0.1', port=port, debug=False, threaded=True)


if __name__ == '__main__':
    logger.info("Starting API Server on ports 8080 and 9001")

    # Start port 8080 in separate thread
    thread_8080 = Thread(target=run_on_port, args=(8080,))
    thread_8080.daemon = True
    thread_8080.start()

    # Run port 9001 in main thread
    run_on_port(9001)

