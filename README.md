# Technitium Exporter

Exporter for Technitium DNS stats for Prometheus scraping

## How to Use
Make use of the docker compose example below or the example in the repo

Set the following env vars

- DNS_HOST - DNS hostname
- DNS_UI_PORT - UI port of your Technitium instance
- DNS_API_KEY - Api key from Technitium DNS
- PROM_PORT - Port to expose prometheus metrics on
- INTERVAL - scraping interval from Technitium

### Docker Compose Example
```
version: "3.3"

services:
  bin-canary:
    image: ghcr.io/josephrpalmer/bin-canary:latest
    container_name: bin-canary
    restart: always
    environment:
      - COUNCIL=South-Ribble
      - ADDRESS=1
      - POSTCODE=AA123ZZ

```
