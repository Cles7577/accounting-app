export default {
  async fetch(request, env, ctx) {
    const corsHeaders = {
      'Access-Control-Allow-Origin': '*',
      'Access-Control-Allow-Methods': 'GET, POST, PUT, DELETE, OPTIONS',
      'Access-Control-Allow-Headers': 'Content-Type, Authorization'
    };

    // Handle OPTIONS requests
    if (request.method === 'OPTIONS') {
      return new Response(null, {
        headers: corsHeaders
      });
    }

    try {
      const url = new URL(request.url);
      
      // API routes
      if (url.pathname.startsWith('/api')) {
        let response;
        
        if (url.pathname === '/api/health') {
          response = {
            status: 'healthy',
            version: '1.0.0',
            timestamp: new Date().toISOString()
          };
        } else {
          response = {
            error: 'API endpoint not found',
            status: 404,
            path: url.pathname
          };
          return new Response(JSON.stringify(response), {
            status: 404,
            headers: {
              'Content-Type': 'application/json',
              ...corsHeaders
            }
          });
        }

        return new Response(JSON.stringify(response), {
          status: 200,
          headers: {
            'Content-Type': 'application/json',
            ...corsHeaders
          }
        });
      }
      
      // For non-API routes, let the static site handle it
      return env.ASSETS.fetch(request);
      
    } catch (error) {
      const errorResponse = {
        error: error.message,
        status: 'error',
        timestamp: new Date().toISOString()
      };
      
      return new Response(JSON.stringify(errorResponse), {
        status: 500,
        headers: {
          'Content-Type': 'application/json',
          ...corsHeaders
        }
      });
    }
  }
};
