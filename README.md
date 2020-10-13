This application bridges Alertmanager alerts to [Gotify](https://gotify.net).

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
## Run

e.g.
```bash
docker run -p 8080:8080 -e TZ=Europe/London -e GOTIFY_KEY=XXXXXXXX -e GOTIFY_SERVER=gotify -e GOTIFY_PORT=80 alertify:latest
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
