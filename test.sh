#!/usr/bin/env bash

SERVER=${1:-'localhost:8080'}

name=testAlert-$RANDOM
URL="http://${SERVER}/alert"
bold=$(tput bold)
normal=$(tput sgr0)

call_alertmanager() {
    curl -v "${URL}" --header 'Content-type: application/json' --data @<(cat <<EOF
{
  "version": "4",
  "groupKey": "testGroup",
  "truncatedAlerts": 0,
  "status": "${STATUS}",
  "receiver": "alertify",
  "commonLabels": {
    "alertname": "${name}",
    "service": "testService",
    "severity":"warning",
    "instance": "server.example.net",
    "namespace": "testNamespace",
    "label_costcentre": "testCostCentre"
  },
  "commonAnnotations": {
    "summary": "Testing latency is high!",
    "description": "Testing latency is at ${1}"
  },
  "alerts": [
    {
      "status": "${STATUS}",
      "generatorURL": "http://alertmanager.example.net/$name",
      "startsAt": "${START}",
      "endsAt": "${END}"
    }
  ]
}
EOF
)
}

echo "${bold}Firing alert ${name} ${normal}"
STATUS='firing'
START=$(date --rfc-3339=seconds | sed 's/ /T/')
END="0001-01-01T00:00:00Z"
call_alertmanager 42
echo -e "\n"

echo "${bold}Press enter to resolve alert ${name} ${normal}"
read -r


echo "${bold}Sending resolved ${normal}"
STATUS='resolved'
END=$(date --rfc-3339=seconds | sed 's/ /T/')
call_alertmanager 0
echo -e "\n"
