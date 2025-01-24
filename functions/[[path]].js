export async function onRequest(context) {
  const { request, env } = context;
  const url = new URL(request.url);
  
  // Add CORS headers
  const corsHeaders = {
    'Access-Control-Allow-Origin': '*',
    'Access-Control-Allow-Methods': 'GET, POST, PUT, DELETE, OPTIONS',
    'Access-Control-Allow-Headers': 'Content-Type, Authorization',
  };

  // Handle OPTIONS request for CORS
  if (request.method === 'OPTIONS') {
    return new Response(null, { headers: corsHeaders });
  }

  try {
    // Forward the request to the Flask app
    const response = await fetch(`http://127.0.0.1:5000${url.pathname}${url.search}`, {
      method: request.method,
      headers: {
        ...request.headers,
        ...corsHeaders,
      },
      body: ['GET', 'HEAD'].includes(request.method) ? null : request.body,
    });

    // Add CORS headers to the response
    const responseHeaders = new Headers(response.headers);
    Object.keys(corsHeaders).forEach((key) => {
      responseHeaders.set(key, corsHeaders[key]);
    });

    return new Response(response.body, {
      status: response.status,
      statusText: response.statusText,
      headers: responseHeaders,
    });
  } catch (error) {
    return new Response(`Server Error: ${error.message}`, {
      status: 500,
      headers: corsHeaders,
    });
  }
}
