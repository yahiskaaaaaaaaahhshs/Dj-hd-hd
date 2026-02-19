#!/bin/bash
pip install -r requirements.txt
gunicorn bot:app
