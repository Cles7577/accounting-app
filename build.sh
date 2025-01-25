#!/bin/bash

# Create and activate virtual environment
python -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Create the functions directory if it doesn't exist
mkdir -p functions

# Copy necessary files to functions directory
cp -r app.py templates static functions/
cp -r requirements.txt functions/
cp .env functions/

# Create the worker script
cat > functions/_worker.js << 'EOL'
export default {
  async fetch(request, env) {
    const corsHeaders = {
      'Access-Control-Allow-Origin': '*',
      'Access-Control-Allow-Methods': 'GET, POST, PUT, DELETE, OPTIONS',
      'Access-Control-Allow-Headers': 'Content-Type, Authorization',
      'Content-Type': 'text/html;charset=UTF-8'
    };

    // Handle OPTIONS requests
    if (request.method === 'OPTIONS') {
      return new Response(null, {
        headers: corsHeaders
      });
    }

    try {
      // Use env.ASSETS to serve static files
      return env.ASSETS.fetch(request);
    } catch (error) {
      return new Response(`Server Error: ${error.message}`, {
        status: 500,
        headers: corsHeaders
      });
    }
  }
};
EOL

# Create a basic _routes.json file for routing
cat > functions/_routes.json << 'EOL'
{
  "version": 1,
  "include": ["/*"],
  "exclude": []
}
EOL
