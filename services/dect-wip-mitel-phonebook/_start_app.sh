#!/usr/bin/env bash

echo "working in $(pwd)"

./_setup_venv.sh

source venv/bin/activate
gunicorn phonebook:init_wsgi\(\)
