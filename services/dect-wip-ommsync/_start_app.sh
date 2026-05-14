#!/usr/bin/env bash

echo "working in $(pwd)"

./_setup_venv.sh

source venv/bin/activate
gunicorn dect-wip-ommsync:init_wsgi\(\)
