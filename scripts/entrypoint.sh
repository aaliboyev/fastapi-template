#! /usr/bin/env bash
set -e

APP_MODULE="src.main:app"
PORT="${SERVER_PORT:-8000}"

if [ -f "/.dockerenv" ]; then
  HOST="0.0.0.0"
  IN_DOCKER=true
else
  IN_DOCKER=false
  HOST="${SERVER_HOST:-127.0.0.1}"
fi

# Base command changes based on debug mode
if [ "$ENABLE_DEBUG" = "true" ]; then
  # Use debugpy to wrap uvicorn
  CMD="python -Xfrozen_modules=off -m debugpy --listen 0.0.0.0:$DEBUG_PORT --wait-for-client -m uvicorn $APP_MODULE --port $PORT --host $HOST"
else
  CMD="uvicorn $APP_MODULE --port $PORT --host $HOST"
fi

case "${ENVIRONMENT:-local}" in
  local|remote)
    CMD="$CMD --reload --reload-dir src"
    ;;
esac

if [ -n "$SSL_CERT_FILE" ] && [ -n "$SSL_KEY_FILE" ]; then
  CMD="$CMD --ssl-certfile $SSL_CERT_FILE --ssl-keyfile $SSL_KEY_FILE"
fi

echo ""
echo "🚀   ENVIRONMENT:   ${ENVIRONMENT:-local}"
echo "🌐   Host:          $HOST"
if [ "$ENABLE_DEBUG" = "true" ]; then
  echo "🐛   Debug Mode:    ENABLED (port $DEBUG_PORT)"
  echo "⏸️    Waiting for debugger to attach..."
fi
echo "🔧   Command:       $CMD"

exec $CMD
