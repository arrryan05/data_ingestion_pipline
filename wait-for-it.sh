#!/usr/bin/env bash
# wait-for-it.sh 

set -e

HOST="$1"
PORT="$2"
shift 2
TIMEOUT=${WAIT_TIMEOUT:-30}

echo "Waiting for $HOST:$PORT..."

for i in $(seq $TIMEOUT); do
  nc -z "$HOST" "$PORT" && {
    echo "$HOST:$PORT is up!"
    exec "$@"
  }
  sleep 1
done

echo "Timeout after ${TIMEOUT}s waiting for $HOST:$PORT"
exit 1
