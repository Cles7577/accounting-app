addEventListener('fetch', event => {
  event.respondWith(handleRequest(event.request))
})

async function handleRequest(request) {
  // Add CORS headers
  const corsHeaders = {
    'Access-Control-Allow-Origin': '*',
    'Access-Control-Allow-Methods': 'GET, POST, PUT, DELETE, OPTIONS',
    'Access-Control-Allow-Headers': 'Content-Type',
  }

  // Handle OPTIONS request for CORS
  if (request.method === 'OPTIONS') {
    return new Response(null, {
      headers: corsHeaders
    })
  }

  try {
    // Forward the request to your Flask app
    const url = new URL(request.url)
    const flaskResponse = await fetch(`https://accounting-app.your-domain.workers.dev${url.pathname}${url.search}`, {
      method: request.method,
      headers: request.headers,
      body: request.body
    })

    // Create a new response with CORS headers
    const response = new Response(flaskResponse.body, flaskResponse)
    Object.keys(corsHeaders).forEach(key => {
      response.headers.set(key, corsHeaders[key])
    })

    return response
  } catch (error) {
    return new Response(`Error: ${error.message}`, {
      status: 500,
      headers: corsHeaders
    })
  }
}
