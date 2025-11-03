#!/bin/bash

source ./venv/bin/activate
cd src/backend || exit 1
fastapi dev app/main.py