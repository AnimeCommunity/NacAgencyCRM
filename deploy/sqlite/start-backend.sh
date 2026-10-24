#!/bin/sh
set -eu

: "${PORT:=8000}"
: "${WEB_CONCURRENCY:=1}"
: "${SQLITE_NAME:=/var/data/nacagencycrm/db.sqlite3}"

export PORT WEB_CONCURRENCY SQLITE_NAME

case "$SQLITE_NAME" in
  /*) sqlite_path="$SQLITE_NAME" ;;
  *) sqlite_path="$(pwd)/$SQLITE_NAME" ;;
esac

mkdir -p "$(dirname "$sqlite_path")"

python manage.py migrate --noinput
python manage.py collectstatic --noinput

exec gunicorn CRM.wsgi:application \
  --bind "0.0.0.0:${PORT}" \
  --workers "${WEB_CONCURRENCY}" \
  --timeout 60
