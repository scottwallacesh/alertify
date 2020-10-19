This application bridges [Prometheus Alertmanager](https://prometheus.io/docs/alerting/latest/alertmanager/) alerts to [Gotify](https://gotify.net/).

# Usage
```
usage: alertify.py [-h] [-c CONFIG] [-H]

Bridge between Prometheus Alertmanager and Gotify

optional arguments:
  -h, --help            show this help message and exit
  -c CONFIG, --config CONFIG
                        path to config YAML. (default: alertify.yaml)
  -H, --healthcheck     simply exit with 0 for healthy or 1 when unhealthy

The following environment variables will override any config or default:
  * LISTEN_PORT   (default: 8080)
  * GOTIFY_SERVER (default: localhost)
  * GOTIFY_PORT   (default: 80)
  * GOTIFY_KEY    (default: None)
  * VERBOSE       (default: False)
```


# Notes
* Listens on port 8080 by default.
* Forwards `resolved` alerts, if sent.
* Defaults, if not sent:
  | Field       | Default value |
  |-------------|---------------|
  | Priority    | `5`           |
  | Description | `...`         |
  | Severity    | `Default`     |


# Docker
## Build
```bash
docker build . -t 'alertify:latest'
```

## Run

e.g.
```bash
docker run --name alertify -p 8080:8080 -e TZ=Europe/London -e GOTIFY_KEY=XXXXXXXX -e GOTIFY_SERVER=gotify -e GOTIFY_PORT=80 alertify:latest
```

## Compose:
```yaml
---
version: "2"
services:
  gotify:
    image: gotify/server:latest
    container_name: gotify
    environment:
      - TZ=Europe/London
    volumes:
      - config/config.yml:/etc/gotify/config.yml
      - data:/app/data
    restart: unless-stopped

  alertify:
    image: alertify:latest
    container_name: alertify
    ports:
      - "8080:8080"
    environment:
      - TZ=Europe/London
      - GOTIFY_KEY=XXXXXXXXXXXX
      - GOTIFY_SERVER=gotify
      - GOTIFY_PORT=80
    restart: unless-stopped
```
