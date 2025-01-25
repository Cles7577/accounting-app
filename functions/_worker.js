import { createExecutionContext } from "@cloudflare/workers-types";

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
      const url = new URL(request.url);
      
      // API routes (Flask backend)
      if (url.pathname.startsWith('/api/')) {
        // Here we'll integrate with Flask routes
        const flaskResponse = await handleFlaskRoute(request, env);
        return new Response(flaskResponse.body, {
          status: flaskResponse.status,
          headers: { ...flaskResponse.headers, ...corsHeaders }
        });
      }
      
      // Serve index.html for the root path
      if (url.pathname === '/') {
        const response = await env.ASSETS.fetch(new Request(url.origin + '/index.html'));
        return new Response(response.body, {
          ...response,
          headers: { ...response.headers, ...corsHeaders }
        });
      }
      
      // For all other paths, use env.ASSETS to serve static files
      return env.ASSETS.fetch(request);
    } catch (error) {
      return new Response(`Server Error: ${error.message}`, {
        status: 500,
        headers: corsHeaders
      });
    }
  }
};

async function handleFlaskRoute(request, env) {
  const url = new URL(request.url);
  const path = url.pathname.replace('/api', '');
  
  // Map Flask routes to their handlers
  const routes = {
    '/login': handleLogin,
    '/register': handleRegister,
    '/dashboard': handleDashboard,
    '/create-team': handleCreateTeam,
    '/new-project': handleNewProject,
    // Add more routes as needed
  };
  
  const handler = routes[path];
  if (handler) {
    return await handler(request, env);
  }
  
  return new Response('Not Found', { status: 404 });
}

// Implement Flask route handlers
async function handleLogin(request, env) {
  if (request.method === 'POST') {
    const data = await request.json();
    // Implement login logic here
    return new Response(JSON.stringify({ status: 'success' }), {
      headers: { 'Content-Type': 'application/json' }
    });
  }
  return new Response('Method not allowed', { status: 405 });
}

async function handleRegister(request, env) {
  if (request.method === 'POST') {
    const data = await request.json();
    // Implement registration logic here
    return new Response(JSON.stringify({ status: 'success' }), {
      headers: { 'Content-Type': 'application/json' }
    });
  }
  return new Response('Method not allowed', { status: 405 });
}

async function handleDashboard(request, env) {
  if (request.method === 'GET') {
    // Implement dashboard logic here
    return new Response(JSON.stringify({ status: 'success' }), {
      headers: { 'Content-Type': 'application/json' }
    });
  }
  return new Response('Method not allowed', { status: 405 });
}

async function handleCreateTeam(request, env) {
  if (request.method === 'POST') {
    const data = await request.json();
    // Implement team creation logic here
    return new Response(JSON.stringify({ status: 'success' }), {
      headers: { 'Content-Type': 'application/json' }
    });
  }
  return new Response('Method not allowed', { status: 405 });
}

async function handleNewProject(request, env) {
  if (request.method === 'POST') {
    const data = await request.json();
    // Implement project creation logic here
    return new Response(JSON.stringify({ status: 'success' }), {
      headers: { 'Content-Type': 'application/json' }
    });
  }
  return new Response('Method not allowed', { status: 405 });
}
