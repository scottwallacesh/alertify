#!/usr/bin/env bash

SERVER=${1:-'localhost:8080'}

NAME=testAlert-$RANDOM
FINGERPRINT=$(date +%s | md5sum | cut -f1 -d' ')
URL="http://${SERVER}/alert"
BOLD=$(tput bold)
NORMAL=$(tput sgr0)

call_alertmanager() {
    VALUE=${1}
    curl -v "${URL}" --header 'Expect:' --header 'Content-type: application/json' --data @<(cat <<EOF
{
  "receiver": "alertify",
  "status": "${STATUS}",
  "alerts": [
    {
      "status": "${STATUS}",
      "labels": {
        "alertname": "${NAME}",
        "id": "01ba4719c80b6fe911b091a7c05124b64eeece964e09c058ef8f9805daca546b",
        "instance": "localhost:1234",
        "job": "test_job",
        "name": "testserver",
        "priority": "1",
        "severity": "low",
        "value": "${VALUE}"
      },
      "annotations": {
        "description": "testserver: unhealthy",
        "summary": "Server unhealthy"
      },
      "startsAt": "${START}",
      "endsAt": "${END}",
      "generatorURL": "http://example.com/some/url",
      "fingerprint": "${FINGERPRINT}"
    }
  ],
  "groupLabels": {
    "alertname": "${NAME}",
    "id": "01ba4719c80b6fe911b091a7c05124b64eeece964e09c058ef8f9805daca546b",
    "instance": "localhost:1234",
    "job": "test_job",
    "name": "testserver",
    "priority": "1",
    "severity": "low",
    "value": "${VALUE}"
  },
  "commonLabels": {
    "alertname": "${NAME}",
    "id": "01ba4719c80b6fe911b091a7c05124b64eeece964e09c058ef8f9805daca546b",
    "instance": "localhost:1234",
    "job": "test_job",
    "name": "testserver",
    "priority": "1",
    "severity": "low",
    "value": "${VALUE}"
  },
  "commonAnnotations": {
    "description": "testserver: unhealthy",
    "summary": "Server unhealthy"
  },
  "externalURL": "http://1ff297bc31a0:9093",
  "version": "4",
  "groupKey": "{}:{alertname=\"${NAME}\", id=\"01ba4719c80b6fe911b091a7c05124b64eeece964e09c058ef8f9805daca546b\", instance=\"localhost:1234\", job=\"test_job\", name=\"testserver\", priority=\"1\", severity=\"low\", value=\"${VALUE}\"}",
  "truncatedAlerts": 0
}
EOF
)
}

echo "${BOLD}Firing alert ${NAME} ${NORMAL}"
STATUS='firing'
START=$(date --rfc-3339=seconds | sed 's/ /T/')
END="0001-01-01T00:00:00Z"
call_alertmanager 42
echo -e "\n"

echo "${BOLD}Press enter to resolve alert ${NAME} ${NORMAL}"
read -r


echo "${BOLD}Sending resolved ${NORMAL}"
STATUS='resolved'
END=$(date --rfc-3339=seconds | sed 's/ /T/')
call_alertmanager 0
echo -e "\n"
