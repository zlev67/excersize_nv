# ============================================================================
# ingest_server.py - Port 9002 - Ingest telemetry data
# ============================================================================

from flask import Flask, request, jsonify
from contextlib import closing
import logging
import time
import atexit
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from telemetry_db.telemetry_db import TelemetryDb

app_ingest = Flask(__name__)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('ingest_server')

# Performance tracking
ingest_stats = {
    'total_requests': 0,
    'total_records': 0,
    'total_time': 0,
    'errors': 0
}


@app_ingest.route('/ingest', methods=['POST'])
def ingest_data():
    """Ingest telemetry data"""
    start_time = time.time()
    ingest_stats['total_requests'] += 1

    try:
        data = request.get_json()

        if not data:
            ingest_stats['errors'] += 1
            return jsonify({'error': 'No data provided'}), 400

        # Validate required fields
        required_fields = ['metric_name', 'server_name', 'value', 'timestamp']
        for field in required_fields:
            if field not in data:
                ingest_stats['errors'] += 1
                return jsonify({'error': f'Missing required field: {field}'}), 400

        with closing(TelemetryDb.get_db()) as conn:
            with closing(conn.cursor()) as cursor:
                # Check if metric exists, if not create it
                cursor.execute(
                    'SELECT id FROM metric_definitions WHERE metric_name = ?',
                    (data['metric_name'],)
                )
                result = cursor.fetchone()

                if result:
                    metric_id = result['id']
                else:
                    # Auto-create new metric
                    cursor.execute(
                        'INSERT INTO metric_definitions (metric_name, unit) VALUES (?, ?)',
                        (data['metric_name'], data['unit'] if 'unit' in data else 'unknown')
                    )
                    metric_id = cursor.lastrowid
                    logger.info(f"Created new metric: {data['metric_name']} ({data['unit']})")

                # Insert metric value
                cursor.execute('''
                    INSERT INTO metric_values (metric_id, server_name, value, timestamp)
                    VALUES (?, ?, ?, ?)
                ''', (metric_id, data['server_name'], data['value'], data['timestamp']))

                conn.commit()
                ingest_stats['total_records'] += 1

        elapsed = time.time() - start_time
        ingest_stats['total_time'] += elapsed

        logger.info(f"Ingested: {data['server_name']} - {data['metric_name']} = {data['value']} ({elapsed:.4f}s)")

        return jsonify({'status': 'success', 'metric_id': metric_id}), 201

    except Exception as e:
        ingest_stats['errors'] += 1
        logger.error(f"Ingest error: {str(e)}")
        return jsonify({'error': str(e)}), 500


@app_ingest.route('/stats', methods=['GET'])
def get_stats():
    """Get ingest performance statistics"""
    avg_time = ingest_stats['total_time'] / ingest_stats['total_requests'] if ingest_stats['total_requests'] > 0 else 0
    return jsonify({
        'total_requests': ingest_stats['total_requests'],
        'total_records': ingest_stats['total_records'],
        'total_errors': ingest_stats['errors'],
        'avg_ingest_time_ms': round(avg_time * 1000, 2),
        'success_rate': round(
            (ingest_stats['total_requests'] - ingest_stats['errors']) / ingest_stats['total_requests'] * 100, 2) if
        ingest_stats['total_requests'] > 0 else 0
    })


if __name__ == '__main__':
    atexit.register(TelemetryDb.cleanup_db)

    TelemetryDb.init_db()
    logger.info("Starting Ingest Server on port 9002")
    app_ingest.run(host='127.0.0.1', port=9002, debug=False)

