This application bridges [Prometheus Alertmanager](https://prometheus.io/docs/alerting/latest/alertmanager/) alerts to [Gotify](https://gotify.net/).

# Usage
```
usage: alertify.py [-h] [-c CONFIG] [-H]

Bridge between Prometheus Alertmanager and Gotify

optional arguments:
  -h, --help            show this help message and exit
  -c CONFIG, --config CONFIG
                        path to config YAML. (default: ./alertify.yaml)
  -H, --healthcheck     simply exit with 0 for healthy or 1 when unhealthy

The following environment variables will override any config or default:
  * DELETE_ONRESOLVE (default: False)
  * DISABLE_RESOLVED (default: False)
  * GOTIFY_CLIENT    (default: None)
  * GOTIFY_KEY       (default: None)
  * GOTIFY_PORT      (default: 80)
  * GOTIFY_SERVER    (default: localhost)
  * LISTEN_PORT      (default: 8080)
  * VERBOSE          (default: False)
```


# Notes
* Listens on port 8080 by default.
* Forwards `resolved` alerts, if not disabled.
* Resolved alerts delete the original alert, if enabled.
* Defaults, if not sent:
  | Field       | Default value |
  |-------------|---------------|
  | Description | `[nodata]`    |
  | Instance    | `[unknown]`   |
  | Priority    | `5`           |
  | Severity    | `Warning`     |


# Docker
## Build
```bash
docker build . -t 'alertify:latest'
```

## Run

e.g.
```bash
docker run --name alertify -p 8080:8080 -e TZ=Europe/London -e GOTIFY_KEY=_APPKEY_ -e GOTIFY_SERVER=gotify -e GOTIFY_PORT=80 alertify:latest
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
      - GOTIFY_KEY=_APPKEY_
      - GOTIFY_CLIENT=_CLIENTKEY_
      - GOTIFY_SERVER=gotify
      - GOTIFY_PORT=80
    restart: unless-stopped
```
