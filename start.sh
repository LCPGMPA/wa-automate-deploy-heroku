#!/bin/sh

# Start the wa-automate server
npx @open-wa/wa-automate --disable-spins --port $PORT --popup --in-docker --qr-timeout 0 --keep-alive --keep-updated --executable-path='/app/.apt/usr/bin/google-chrome' &

# Start the Python app
python3 app.py
