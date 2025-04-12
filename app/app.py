from prometheus_client import MetricsHandler, Gauge
from datetime import datetime, timedelta
import logging
import os
import requests
import threading
import time
from http.server import HTTPServer
from dns_metric import dns_metric

logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')
logging.getLogger("requests").setLevel(logging.WARNING)

version = "0.0.5"
gauges = {}

metric_map = {}
date_tracker = datetime.now().isoformat(timespec='seconds')

prom_port = int(os.environ.get('PROM_PORT', 9130))
dns_api_key = os.environ.get('DNS_API_KEY')
dns_host = os.environ.get('DNS_HOST', '127.0.0.1')
dns_ui_port = int(os.environ.get('DNS_PORT', 5380))
interval = int(os.environ.get('INTERVAL', 60))

class PrometheusEndpointServer(threading.Thread):
    def __init__(self, httpd, *args, **kwargs):
        self.httpd = httpd
        super(PrometheusEndpointServer, self).__init__(*args, **kwargs)

    def run(self):
        self.httpd.serve_forever()


def start_prometheus_server():
    try:
        httpd = HTTPServer(("0.0.0.0", prom_port), MetricsHandler)
    except (OSError) as e:
        logging.error("Failed to start Prometheus server: %s", str(e))
        return

    thread = PrometheusEndpointServer(httpd)
    thread.daemon = True
    thread.start()
    logging.info("Exporting Prometheus /metrics/ on port %s", prom_port)

def validate_token():
    if not dns_api_key:
        logging.error("No DNS API key provided. Please set the DNS_API_KEY environment variable.")
        exit(1)

def get_stats(start_time, end_time):
    validate_token()
    url = "http://{}:{}/api/dashboard/stats/get?token={}&type=Custom&start={}&end={}".format(dns_host, dns_ui_port, dns_api_key, start_time, end_time)
    logging.debug("Fetching stats from URL: %s", url)
    try:
        response = requests.get(url)
        if response.status_code == 200:
            data = response.json()
            logging.debug("Fetched stats from DNS server: %s", data)

            for key, value in data['response']['stats'].items():
                if key not in metric_map:
                    metric_map[key] = dns_metric(key, value, value, datetime.now())
                    logging.info("Created new metric: %s", key)
                else:
                    if metric_map[key].last_updated.date() != datetime.now().date():
                        metric_map[key].total_today = 0
                    metric_map[key].current_value = value
                    metric_map[key].total_today += value
                    metric_map[key].last_updated = datetime.now()
                    logging.debug("Updated existing metric: %s", key)
        else:
            logging.error("Failed to fetch stats from DNS server: %s", response.status_code)
            return None
    except requests.exceptions.RequestException as e:
        logging.error("Error fetching stats from DNS server: %s", str(e))
        return None

def update_metrics():
    count=0
    for key, metric in metric_map.items():
        if metric.current_value != 0:
            update_gauge(key, metric.current_value)
            logging.debug("Updated gauge for %s: %s", key, metric.current_value)
            count += 1
        else:
            logging.debug("No update for %s: %s", key, metric.current_value)

        if metric.total_today != 0:
            update_gauge(key + "_today", metric.total_today)
            logging.debug("Updated total_today for %s: %s", key, metric.total_today)

    logging.info("Total metrics updated: {}".format(count))


def server():

    #preload the gauges from midnight
    date_tracker = datetime.now().isoformat(timespec='seconds')
    get_stats(datetime.now().replace(hour=0, minute=0, second=0).isoformat(timespec='seconds'), date_tracker)
    logging.info("Preloaded metrics from midnight")

    time.sleep(interval)

    while True:
        start_time = (date_tracker)
        end_time = datetime.now().isoformat(timespec='seconds')
        date_tracker = end_time

        get_stats(start_time, end_time)
        update_metrics()
        logging.debug("Updated metrics for all keys")

        time.sleep(interval)

def update_gauge(key, value):
    key = "technitium_dns_{}".format(key)
    if key not in gauges:
        gauges[key] = Gauge(key, 'DNS gauge')
    gauges[key].set(value)


if __name__ == '__main__':
    logging.info("Technitium DNS Stats Exporter by JRP - Version {}".format(version))
    start_prometheus_server()
    server()

    time.sleep(100)
