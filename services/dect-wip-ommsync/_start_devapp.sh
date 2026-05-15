#!/usr/bin/env bash

echo "working in $(pwd)"

./_setup_venv.sh

source venv/bin/activate
python3 dect-wip-ommsync.py
