#!/bin/bash

# Set DNS servers
echo "nameserver 8.8.8.8" > /etc/resolv.conf
echo "nameserver 1.1.1.1" >> /etc/resolv.conf

# Set environment variables
export SUPABASE_URL="https://ppmhmbcmbqhgqelfdnvk.supabase.co"
export SUPABASE_KEY="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InBwbWhtYmNtYnFoZ3FlbGZkbnZrIiwicm9sZSI6ImFub24iLCJpYXQiOjE3ODY1MjkxMjcsImV4cCI6MjEwMjEwNTEyN30.uUceevaFmeMUbZvRyqz6XK_mMOjQ7BBPnj4THMNZbho"
export SECRET_KEY="df89c312430a47299f02e493b972250b"
export FLASK_ENV="production"
export DEBUG="false"
export PYTHONUNBUFFERED="1"
export RENDER="true"

echo "Starting RAAWA Approval System..."
echo "SUPABASE_URL: ${SUPABASE_URL}"
echo "SUPABASE_KEY: ${SUPABASE_KEY:0:30}..."
echo "FLASK_ENV: ${FLASK_ENV}"
echo "PORT: ${PORT:-10000}"

# Start the application
exec gunicorn app:app --worker-class eventlet --workers 1 --timeout 120 --bind 0.0.0.0:${PORT:-10000}
