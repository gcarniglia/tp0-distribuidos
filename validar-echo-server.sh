#!/bin/bash

MSG="mensaje_prueba_echo"

RESPONSE=$(docker compose run --rm -T tester sh -c "echo '$MSG' | nc server 12345 2>/dev/null" | tr -d '\r\n')

if [ "$RESPONSE" = "$MSG" ]; then
  echo "action: test_echo_server | result: success"
else
  echo "action: test_echo_server | result: fail"
fi