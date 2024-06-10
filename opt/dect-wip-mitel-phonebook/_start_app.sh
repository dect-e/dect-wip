#!/bin/bash

APP_DIR='/opt/dect-wip-mitel-phonebook/'
cd $APP_DIR

if [ ! -d "venv/" ]; then
  python3 -mvenv venv
  source venv/bin/activate
  pip3 install --upgrade pip
  pip3 install -r requirements.txt
fi

source venv/bin/activate
python3 phonebook.py