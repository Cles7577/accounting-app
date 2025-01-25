#!/bin/bash

# Create and activate virtual environment
python -m venv .venv
source .venv/bin/activate

# Debug: Print current directory
echo "Current directory: $(pwd)"

# Install Node.js and npm
curl -fsSL https://deb.nodesource.com/setup_18.x | bash -
apt-get install -y nodejs

# Install Python dependencies
pip install -r requirements.txt

# Create necessary directories
mkdir -p flask_session
mkdir -p static/css/dist
mkdir -p static/js

# Install Node dependencies
echo "Installing Node dependencies..."
npm install

# Build Tailwind CSS
echo "Building Tailwind CSS..."
NODE_ENV=production npx tailwindcss -i ./static/css/main.css -o ./static/css/dist/main.css --minify

# Debug: Show the contents and permissions of directories
echo "Contents of current directory:"
ls -la

echo "Contents of static directory:"
ls -la static/

echo "Contents of static/css directory:"
ls -la static/css/

echo "Contents of static/css/dist directory:"
ls -la static/css/dist/

echo "File permissions and content of main.css:"
ls -la static/css/dist/main.css
cat static/css/dist/main.css

# Copy the entire Flask application structure
cp -r app.py config.py auth.py models templates static functions/
cp -r requirements.txt .env functions/

# Copy static files to the correct location
cp -r static/* static/
cp -r templates/* templates/

# Ensure correct permissions
chmod -R 755 static
chmod -R 755 templates

# Verify permissions after chmod
echo "Permissions after chmod:"
ls -la static/css/dist/main.css

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
