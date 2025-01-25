#!/bin/bash

# Create and activate virtual environment
python -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Create the functions directory if it doesn't exist
mkdir -p functions

# Copy the entire Flask application structure
cp -r app.py config.py auth.py models templates static functions/
cp -r requirements.txt .env functions/

# Create necessary directories
mkdir -p flask_session
mkdir -p static

# Copy static files to the correct location
cp -r static/* static/
cp -r templates/* templates/

# Create the worker script to handle Flask routes
cat > functions/_worker.js << 'EOL'
export default {
  async fetch(request, env) {
    try {
      const url = new URL(request.url);
      
      // Serve static files directly
      if (url.pathname.startsWith('/static/')) {
        return env.ASSETS.fetch(request);
      }

      // Forward all other requests to Flask application
      const response = await env.ASSETS.fetch(request);
      return response;
    } catch (error) {
      return new Response(`Server Error: ${error.message}`, {
        status: 500,
        headers: { 'Content-Type': 'text/plain' }
      });
    }
  }
};
EOL

# Create a routes file for Cloudflare Pages
cat > functions/_routes.json << 'EOL'
{
  "version": 1,
  "include": ["/static/*"],
  "exclude": []
}
EOL
