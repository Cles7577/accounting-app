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
cp .env functions/

# Create the worker script
cat > functions/_worker.js << 'EOL'
export default {
  async fetch(request, env) {
    try {
      // Forward the request to your Flask app
      const url = new URL(request.url);
      const response = await fetch(`http://127.0.0.1:5000${url.pathname}${url.search}`, {
        method: request.method,
        headers: request.headers,
        body: request.body
      });
      
      return response;
    } catch (error) {
      return new Response(`Server Error: ${error.message}`, { status: 500 });
    }
  }
};
EOL
