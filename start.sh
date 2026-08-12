#!/bin/bash

# Set environment variables
export SUPABASE_URL="https://ppmhmbcmbqhgqelfdnvk.supabase.co"
export SUPABASE_KEY="sb_publishable_5ComPSfppVJ6lWwpYbwA8A_n7HJn6dG"
export SECRET_KEY="$(python -c 'import secrets; print(secrets.token_urlsafe(32))')"
export FLASK_ENV="production"
export DEBUG="false"
export PYTHONUNBUFFERED="1"

# Print environment (hide sensitive values)
echo "Starting RAAWA Approval System..."
echo "SUPABASE_URL: ${SUPABASE_URL}"
echo "FLASK_ENV: ${FLASK_ENV}"
echo "PORT: ${PORT:-10000}"

# Start the application
exec gunicorn app:app --worker-class eventlet --workers 1 --timeout 120 --bind 0.0.0.0:${PORT:-10000}
