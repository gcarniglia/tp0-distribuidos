#!/bin/bash

MSG="hola"

RESPONSE=$(docker compose -f docker-compose-dev.yaml run --rm -T tester -c "echo '$MSG' | nc server 12345" 2>/dev/null | tr -d '\r\n')

if [ "$RESPONSE" = "$MSG" ]; then
  echo "action: test_echo_server | result: success"
else
  echo "action: test_echo_server | result: fail"
fi