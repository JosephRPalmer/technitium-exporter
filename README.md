# Technitium Exporter

Exporter for Technitium DNS stats for Prometheus scraping

## How to Use
Make use of the docker compose example below or the example in the repo

Set the following env vars

- DNS_HOST - DNS hostname (defaults to localhost)
- DNS_UI_PORT - UI port of your Technitium instance (defaults to 5380)
- DNS_API_KEY - Api key from Technitium DNS
- PROM_PORT - Port to expose prometheus metrics on (defaults to 9130)
- INTERVAL - scraping interval from Technitium (defaults to 60 seconds)

### Docker Compose Example
```
version: "3.3"

services:
  technitium-exporter:
    image: ghcr.io/josephrpalmer/technitium-exporter:latest
    container_name: technitium-exporter
    restart: always
    environment:
      - DNS_HOST=127.0.0.1
      - DNS_API_KEY=abc123


```
