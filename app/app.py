from prometheus_client import MetricsHandler, Gauge
from datetime import datetime, timedelta
import logging
import os
import requests
import threading
import time
from http.server import HTTPServer


logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')
logging.getLogger("requests").setLevel(logging.WARNING)

version = "0.0.1"
gauges = {}

prom_port = int(os.environ.get('PROM_PORT', 9130))
dns_api_key = os.environ.get('DNS_API_KEY')
dns_host = os.environ.get('DNS_HOST', 'localhost')
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
            # Update Prometheus gauges with the fetched data['response']['stats']
            update_gauge('totalQueries', data['response']['stats']['totalQueries'])
            update_gauge('totalNoError', data['response']['stats']['totalNoError'])
            update_gauge('totalServerFailure', data['response']['stats']['totalServerFailure'])
            update_gauge('totalNxDomain', data['response']['stats']['totalNxDomain'])
            update_gauge('totalRefused', data['response']['stats']['totalRefused'])
            update_gauge('totalAuthoritative', data['response']['stats']['totalAuthoritative'])
            update_gauge('totalRecursive', data['response']['stats']['totalRecursive'])
            update_gauge('totalCached', data['response']['stats']['totalCached'])
            update_gauge('totalBlocked', data['response']['stats']['totalBlocked'])
            update_gauge('totalDropped', data['response']['stats']['totalDropped'])
            update_gauge('totalClients', data['response']['stats']['totalClients'])
            update_gauge('zones', data['response']['stats']['zones'])
            update_gauge('cachedEntries', data['response']['stats']['cachedEntries'])
            update_gauge('allowedZones', data['response']['stats']['allowedZones'])
            update_gauge('blockedZones', data['response']['stats']['blockedZones'])
            update_gauge('allowListZones', data['response']['stats']['allowListZones'])
            update_gauge('blockListZones', data['response']['stats']['blockListZones'])
        else:
            logging.error("Failed to fetch stats from DNS server: %s", response.status_code)
            return None
    except requests.exceptions.RequestException as e:
        logging.error("Error fetching stats from DNS server: %s", str(e))
        return None

def server():


    while True:
        start_time = (datetime.now() - timedelta(seconds=interval)).isoformat(timespec='seconds')
        end_time = datetime.now().isoformat(timespec='seconds')

        get_stats(start_time, end_time)

        # Sleep for 5 minutes before fetching stats again
        time.sleep(interval)

def update_gauge(key, value):
    if key not in gauges:
        gauges[key] = Gauge(key, 'DNS gauge')
    gauges[key].set(value)


if __name__ == '__main__':
    logging.info("Technitium DNS Stats Exporter by JRP - Version {}".format(version))
    start_prometheus_server()
    server()

    time.sleep(100)
