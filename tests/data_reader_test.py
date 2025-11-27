# ============================================================================
# data_reader.py - Client application that reads data from API server
# ============================================================================

import requests
import time
import logging
import sys

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger_reader = logging.getLogger('data_reader')

API_BASE_8080 = 'http://127.0.0.1:8080'
API_BASE_9001 = 'http://127.0.0.1:9001'


def list_metrics():
    """Get list of all metrics"""
    try:
        response = requests.get(f'{API_BASE_8080}/telemetry/ListMetrics', timeout=5)
        if response.status_code == 200:
            data = response.json()
            metrics_data = data['metrics']
            logger_reader.info(f"ListMetrics: Found {len(metrics_data)} metrics")

            for metric in metrics_data:
                metric_name = metric['metric_name']
                unit = metric['unit']
                values_count = len(metric['values'])
                logger_reader.info(f"  - {metric_name} ({unit}): {values_count} servers")
                for val in metric['values']:
                    logger_reader.info(f"      {val['server_name']}: {val['value']} @ {val['timestamp']}")

            return metrics_data
        else:
            logger_reader.error(f"ListMetrics failed: {response.status_code}")
            return []
    except requests.exceptions.RequestException as e:
        logger_reader.error(f"ListMetrics error: {e}")
        return []

def get_metric(metric_name):
    """Get latest value for a specific metric"""
    try:
        response = requests.get(
            f'{API_BASE_8080}/telemetry/GetMetric',
            params={'name': metric_name},
            timeout=5
        )
        if response.status_code == 200:
            data = response.json()
            logger_reader.info(
                f"GetMetric '{metric_name}': {data['server_name']} = {data['value']} {data['unit']} @ {data['timestamp']}"
            )
            return data
        else:
            logger_reader.warning(f"GetMetric '{metric_name}' failed: {response.status_code}")
            return None
    except requests.exceptions.RequestException as e:
        logger_reader.error(f"GetMetric '{metric_name}' error: {e}")
        return None


def get_counters_csv(server_name=None):
    """Get CSV export of counters"""
    try:
        params = {'server': server_name} if server_name else {}
        response = requests.get(f'{API_BASE_9001}/counters', params=params, timeout=10)

        if response.status_code == 200:
            csv_data = response.text
            lines = csv_data.strip().split('\n')
            logger_reader.info(f"GetCounters CSV: Received {len(lines)} lines (including header)")
            logger_reader.info(f"CSV Header: {lines[0]}")
            if len(lines) > 1:
                logger_reader.info(f"First data row: {lines[1][:100]}...")

            # Save to file
            filename = f"counters_{server_name or 'all'}_{int(time.time())}.csv"
            with open(filename, 'w') as f:
                f.write(csv_data)
            logger_reader.info(f"CSV saved to: {filename}")
            return csv_data
        else:
            logger_reader.error(f"GetCounters failed: {response.status_code}")
            return None
    except requests.exceptions.RequestException as e:
        logger_reader.error(f"GetCounters error: {e}")
        return None


def get_api_stats():
    """Get API performance statistics"""
    try:
        response = requests.get(f'{API_BASE_8080}/stats', timeout=5)
        if response.status_code == 200:
            stats = response.json()
            logger_reader.info("=== API Performance Statistics ===")
            for endpoint, data in stats.items():
                if isinstance(data, dict):
                    logger_reader.info(f"{endpoint}: {data}")
                else:
                    logger_reader.info(f"{endpoint}: {data}")
            return stats
        else:
            logger_reader.warning(f"Stats request failed: {response.status_code}")
            return None
    except requests.exceptions.RequestException as e:
        logger_reader.error(f"Stats error: {e}")
        return None


def run_reader():
    """Main reader application logic"""
    logger_reader.info("=== Data Reader Application Started ===")
    logger_reader.info("Waiting 15 seconds for system to initialize and collect data...")
    time.sleep(15)

    # 1. List all metrics (once) - now returns full metric data with values
    logger_reader.info("\n--- Step 1: Listing all metrics with values ---")
    metrics_data = list_metrics()

    if not metrics_data:
        logger_reader.error("No metrics found. Exiting.")
        return

    # Extract metric names for later use
    metric_names = [m['metric_name'] for m in metrics_data]

    time.sleep(2)

    # 2. Get specific metric values (10 times)
    logger_reader.info("\n--- Step 2: Getting specific metric values (10 times) ---")
    for i in range(10):
        # Pick a random metric or cycle through available ones
        metric_to_query = metric_names[i % len(metric_names)]
        logger_reader.info(f"Query {i + 1}/10:")
        get_metric(metric_to_query)
        time.sleep(1)  # Small delay between queries

    time.sleep(2)

    # 3. Get CSV export (once)
    logger_reader.info("\n--- Step 3: Getting CSV export ---")
    get_counters_csv()  # Get all servers

    time.sleep(2)

    # 4. Get performance statistics
    logger_reader.info("\n--- Step 4: API Performance Statistics ---")
    get_api_stats()

    logger_reader.info("\n=== Data Reader Application Completed ===")

if __name__ == '__main__':
    sys.path.insert(0, '..')
    try:
        run_reader()
    except KeyboardInterrupt:
        logger_reader.info("Reader stopped by user")
    except Exception as e:
        logger_reader.error(f"Unexpected error: {e}")