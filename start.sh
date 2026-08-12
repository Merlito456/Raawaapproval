#!/bin/bash

# Set environment variables explicitly
export SUPABASE_URL="https://ppmhmbcmbqhgqelfdnvk.supabase.co"
export SUPABASE_KEY="sb_publishable_5ComPSfppVJ6lWwpYbwA8A_n7HJn6dG"
export SECRET_KEY="df89c312430a47299f02e493b972250b"
export FLASK_ENV="production"
export DEBUG="false"
export PYTHONUNBUFFERED="1"
export RENDER="true"
export DOTENV_LOAD="false"  # Disable dotenv loading

echo "Starting RAAWA Approval System..."
echo "SUPABASE_URL: ${SUPABASE_URL}"
echo "SUPABASE_KEY: ${SUPABASE_KEY:0:20}..."
echo "FLASK_ENV: ${FLASK_ENV}"
echo "PORT: ${PORT:-10000}"

# Test Supabase key
echo "Testing Supabase connection..."
python -c "
import os
from supabase import create_client
try:
    client = create_client(os.environ['SUPABASE_URL'], os.environ['SUPABASE_KEY'])
    print('✅ Supabase client created successfully')
except Exception as e:
    print(f'❌ Supabase connection failed: {e}')
    exit(1)
"

# Start the application
echo "Starting Gunicorn..."
exec gunicorn app:app --worker-class eventlet --workers 1 --timeout 120 --bind 0.0.0.0:${PORT:-10000}
