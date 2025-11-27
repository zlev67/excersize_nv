
# ============================================================================
# data_generator.py - Fake telemetry data generator
# ============================================================================

import requests
import random
import time
from datetime import datetime
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger_gen = logging.getLogger('data_generator')

INGEST_URL = 'http://127.0.0.1:9002/ingest'

# Simulated switches/servers
SERVERS = ['switch-01', 'switch-02', 'switch-03', 'server-01', 'server-02']

# Metric definitions with realistic ranges
METRICS = {
    'bandwidth_mbps': {'unit': 'Mbps', 'min': 10, 'max': 1000},
    'latency_ms': {'unit': 'ms', 'min': 1, 'max': 100},
    'packet_loss_percent': {'unit': 'percent', 'min': 0, 'max': 5},
    'cpu_usage_percent': {'unit': 'percent', 'min': 10, 'max': 95},
    'memory_usage_percent': {'unit': 'percent', 'min': 30, 'max': 90},
    'error_count': {'unit': 'count', 'min': 0, 'max': 50},
    'throughput_gbps': {'unit': 'Gbps', 'min': 0.1, 'max': 10},
    'connection_count': {'unit': 'count', 'min': 50, 'max': 5000}
}

class DataGenerator:
    """Simulate realistic metric values with occasional spikes"""

    @staticmethod
    def generate_metric_value(metric_config):
        """Generate realistic metric value with occasional spikes"""
        base_value = random.uniform(metric_config['min'], metric_config['max'])

        # 10% chance of spike
        if random.random() < 0.1:
            spike_factor = random.uniform(1.2, 1.5)
            base_value = min(base_value * spike_factor, metric_config['max'])

        return round(base_value, 2)

    def send_telemetry_data(self):
        """Generate and send telemetry data for all servers"""
        timestamp = datetime.now().isoformat()

        for server in SERVERS:
            for metric_name, metric_config in METRICS.items():
                value = self.generate_metric_value(metric_config)

                data = {
                    'metric_name': metric_name,
                    'server_name': server,
                    'value': value,
                    'unit': metric_config['unit'],
                    'timestamp': timestamp
                }

                try:
                    response = requests.post(INGEST_URL, json=data, timeout=2)
                    if response.status_code == 201:
                        logger_gen.debug(f"Sent: {server} - {metric_name} = {value}")
                    else:
                        logger_gen.warning(f"Failed to send: {response.status_code} - {response.text}")
                except requests.exceptions.RequestException as e:
                    logger_gen.error(f"Connection error: {e}")
                    return False

        return True

    def run_generator(self):
        """Run telemetry generator continuously"""
        logger_gen.info("Starting telemetry data generator")
        logger_gen.info(f"Generating data for {len(SERVERS)} servers with {len(METRICS)} metrics each")
        logger_gen.info(f"Update interval: 10 seconds")

        cycle = 0
        while True:
            cycle += 1
            start_time = time.time()

            success = self.send_telemetry_data()

            elapsed = time.time() - start_time

            if success:
                total_metrics = len(SERVERS) * len(METRICS)
                logger_gen.info(f"Cycle {cycle}: Sent {total_metrics} metrics in {elapsed:.2f}s")
            else:
                logger_gen.error(f"Cycle {cycle}: Failed to send data")

            # Wait for next cycle (10 seconds)
            time.sleep(10)

if __name__ == '__main__':
    # Wait a bit for servers to start
    logger_gen.info("Waiting 5 seconds for servers to start...")
    time.sleep(10)
    
    try:
        DataGenerator().run_generator()
    except KeyboardInterrupt:
        logger_gen.info("Generator stopped by user")