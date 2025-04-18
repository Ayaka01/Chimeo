API_DESCRIPTION = """
# Chimeo Messaging API

This API provides endpoints for user authentication, messaging, and friend management
for the Chimeo messaging application.

## Features

* User registration and authentication
* Friend requests and friend management
* Real-time messaging with WebSockets
* Message delivery status tracking

## Authentication

Most endpoints require authentication using a JWT bearer token.
Get your token by registering a new account or logging in.

```
Authorization: Bearer your_token_here
```
"""

AUTH_ENDPOINTS_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Chimeo API - Auth Endpoints</title>
    <style>
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, 'Open Sans', 'Helvetica Neue', sans-serif;
            line-height: 1.6;
            color: #333;
            max-width: 800px;
            margin: 0 auto;
            padding: 20px;
            background-color: #f9f9f9;
        }
        h1, h2 {
            color: #2c3e50;
            border-bottom: 2px solid #3498db;
            padding-bottom: 10px;
        }
        .endpoint {
            background: white;
            border-radius: 8px;
            padding: 20px;
            margin: 20px 0;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }
        .method {
            display: inline-block;
            padding: 5px 10px;
            border-radius: 4px;
            font-weight: bold;
            margin-right: 10px;
            color: white;
            background-color: #3498db;
        }
        .path {
            font-family: monospace;
            font-size: 1.1em;
            background-color: #f5f5f5;
            padding: 3px 6px;
            border-radius: 3px;
        }
        .description {
            margin: 10px 0;
        }
        .parameters {
            margin-top: 15px;
        }
        .parameter {
            margin-bottom: 5px;
            font-family: monospace;
        }
        .required {
            color: #e74c3c;
            font-weight: bold;
        }
        pre {
            background-color: #f5f5f5;
            padding: 15px;
            border-radius: 5px;
            overflow-x: auto;
        }
        .response {
            margin-top: 15px;
        }
        .back {
            display: inline-block;
            margin-top: 20px;
            color: #3498db;
            text-decoration: none;
        }
        .back:hover {
            text-decoration: underline;
        }
    </style>
</head>
<body>
    <h1>Authentication Endpoints</h1>
    
    <div class="endpoint">
        <div class="method">POST</div>
        <span class="path">/auth/register</span>
        <div class="description">Register a new user and return an access token.</div>
        <div class="parameters">
            <h3>Request Body:</h3>
            <pre>
{
  "username": "string",
  "email": "string",
  "password": "string",
  "display_name": "string"
}
            </pre>
        </div>
        <div class="response">
            <h3>Response:</h3>
            <pre>
{
  "access_token": "string",
  "token_type": "bearer",
  "username": "string",
  "display_name": "string"
}
            </pre>
        </div>
    </div>
    
    <div class="endpoint">
        <div class="method">POST</div>
        <span class="path">/auth/login</span>
        <div class="description">Authenticate a user and return an access token.</div>
        <div class="parameters">
            <h3>Request Body:</h3>
            <pre>
{
  "email": "string",
  "password": "string"
}
            </pre>
        </div>
        <div class="response">
            <h3>Response:</h3>
            <pre>
{
  "access_token": "string",
  "token_type": "bearer",
  "username": "string",
  "display_name": "string"
}
            </pre>
        </div>
    </div>
    
    <div class="endpoint">
        <div class="method">POST</div>
        <span class="path">/auth/token</span>
        <div class="description">OAuth2 compatible token login endpoint used by the FastAPI Swagger UI.</div>
        <div class="parameters">
            <h3>Form Data:</h3>
            <div class="parameter"><span class="required">username</span>: string (email)</div>
            <div class="parameter"><span class="required">password</span>: string</div>
        </div>
        <div class="response">
            <h3>Response:</h3>
            <pre>
{
  "access_token": "string",
  "token_type": "bearer",
  "username": "string",
  "display_name": "string"
}
            </pre>
        </div>
    </div>
    
    <a href="/" class="back">← Back to API Home</a>
</body>
</html>
"""

USERS_ENDPOINTS_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Chimeo API - Users Endpoints</title>
    <style>
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, 'Open Sans', 'Helvetica Neue', sans-serif;
            line-height: 1.6;
            color: #333;
            max-width: 800px;
            margin: 0 auto;
            padding: 20px;
            background-color: #f9f9f9;
        }
        h1, h2 {
            color: #2c3e50;
            border-bottom: 2px solid #3498db;
            padding-bottom: 10px;
        }
        .endpoint {
            background: white;
            border-radius: 8px;
            padding: 20px;
            margin: 20px 0;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }
        .method {
            display: inline-block;
            padding: 5px 10px;
            border-radius: 4px;
            font-weight: bold;
            margin-right: 10px;
            color: white;
            min-width: 50px; /* Ensure consistent width */
            text-align: center;
        }
        .get {
            background-color: #2ecc71;
        }
        .post {
            background-color: #3498db;
        }
        .put {
            background-color: #f39c12;
        }
        .delete {
            background-color: #e74c3c;
        }
        .path {
            font-family: monospace;
            font-size: 1.1em;
            background-color: #f5f5f5;
            padding: 3px 6px;
            border-radius: 3px;
        }
        .description {
            margin: 10px 0;
        }
        .auth-required {
            color: #e74c3c;
            font-weight: bold;
            font-size: 0.9em;
            margin-top: 5px;
        }
        .parameters {
            margin-top: 15px;
        }
        .parameter {
            margin-bottom: 5px;
            font-family: monospace;
        }
        .required {
            color: #e74c3c;
            font-weight: bold;
        }
        pre {
            background-color: #f5f5f5;
            padding: 15px;
            border-radius: 5px;
            overflow-x: auto;
        }
        .response {
            margin-top: 15px;
        }
        .back {
            display: inline-block;
            margin-top: 20px;
            color: #3498db;
            text-decoration: none;
        }
        .back:hover {
            text-decoration: underline;
        }
    </style>
</head>
<body>
    <h1>User Management & Friendship Endpoints</h1>

    <div class="endpoint">
        <div class="method get">GET</div>
        <span class="path">/users/search</span>
        <div class="description">Search for users by username or display name. Minimum query length is 3 characters.</div>
        <div class="auth-required">Authentication Required</div>
        <div class="parameters">
            <h3>Query Parameters:</h3>
            <pre>q: string (required)</pre>
        </div>
        <div class="response">
            <h3>Response:</h3>
            <pre>
[
  {
    "username": "string",
    "display_name": "string",
    "last_seen": "datetime | null", // Adjusted based on schema
    "is_online": "boolean" // Adjusted based on schema if available
  }
]
            </pre>
        </div>
    </div>

    <div class="endpoint">
        <div class="method get">GET</div>
        <span class="path">/users/friends</span>
        <div class="description">Get the current user's list of friends.</div>
        <div class="auth-required">Authentication Required</div>
        <div class="response">
            <h3>Response:</h3>
            <pre>
[
  {
    "username": "string",
    "display_name": "string",
    "last_seen": "datetime | null", // Adjusted based on schema
    "is_online": "boolean" // Adjusted based on schema if available
  }
]
            </pre>
        </div>
    </div>

    <div class="endpoint">
        <div class="method post">POST</div>
        <span class="path">/users/friends/request</span>
        <div class="description">Send a friend request to another user.</div>
        <div class="auth-required">Authentication Required</div>
        <div class="parameters">
            <h3>Request Body:</h3>
            <pre>
{
  "username": "string" // Username of the recipient
}
            </pre>
        </div>
        <div class="response">
            <h3>Response (Success 200 OK):</h3>
            <pre>
{
  "status": "pending" | "accepted" // 'accepted' if the recipient already sent a request
}
            </pre>
            <h3>Response (Error 400 Bad Request):</h3>
            <pre>
{
  "detail": "Error message (e.g., User not found, Already friends, Request already exists)"
}
            </pre>
        </div>
    </div>

    <div class="endpoint">
        <div class="method post">POST</div>
        <span class="path">/users/friends/respond</span>
        <div class="description">Respond to a received friend request (accept or reject).</div>
        <div class="auth-required">Authentication Required</div>
        <div class="parameters">
            <h3>Request Body:</h3>
            <pre>
{
  "request_id": "string", // ID of the friend request
  "action": "accept" | "reject"
}
            </pre>
        </div>
        <div class="response">
            <h3>Response (Success 200 OK):</h3>
            <pre>
// UserResponse of the other user involved in the request
{
  "username": "string",
  "display_name": "string",
  "last_seen": "datetime | null",
  "is_online": "boolean"
}
            </pre>
             <h3>Response (Error 400 Bad Request):</h3>
            <pre>
{
  "detail": "Error message (e.g., Could not accept/reject friend request, Invalid action)"
}
            </pre>
        </div>
    </div>

    <div class="endpoint">
        <div class="method get">GET</div>
        <span class="path">/users/friends/requests/received</span>
        <div class="description">Get friend requests received by the current user. Optionally filter by status.</div>
        <div class="auth-required">Authentication Required</div>
        <div class="parameters">
            <h3>Query Parameters:</h3>
            <pre>status: "pending" | "accepted" | "rejected" (optional)</pre>
        </div>
        <div class="response">
            <h3>Response:</h3>
            <pre>
[
  {
    "id": "string",
    "sender": { "username": "string", "display_name": "string", "last_seen": "datetime | null" },
    "recipient": { "username": "string", "display_name": "string", "last_seen": "datetime | null" },
    "status": "string",
    "created_at": "datetime",
    "updated_at": "datetime"
  }
]
            </pre>
        </div>
    </div>

     <div class="endpoint">
        <div class="method get">GET</div>
        <span class="path">/users/friends/requests/sent</span>
        <div class="description">Get friend requests sent by the current user. Optionally filter by status.</div>
        <div class="auth-required">Authentication Required</div>
        <div class="parameters">
            <h3>Query Parameters:</h3>
            <pre>status: "pending" | "accepted" | "rejected" (optional)</pre>
        </div>
        <div class="response">
            <h3>Response:</h3>
            <pre>
[
  {
    "id": "string",
    "sender": { "username": "string", "display_name": "string", "last_seen": "datetime | null" },
    "recipient": { "username": "string", "display_name": "string", "last_seen": "datetime | null" },
    "status": "string",
    "created_at": "datetime",
    "updated_at": "datetime"
  }
]
            </pre>
        </div>
    </div>

    <a href="/" class="back">← Back to API Home</a>
</body>
</html>
"""

MESSAGES_ENDPOINTS_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Chimeo API - Messages Endpoints</title>
    <style>
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, 'Open Sans', 'Helvetica Neue', sans-serif;
            line-height: 1.6;
            color: #333;
            max-width: 800px;
            margin: 0 auto;
            padding: 20px;
            background-color: #f9f9f9;
        }
        h1, h2 {
            color: #2c3e50;
            border-bottom: 2px solid #3498db;
            padding-bottom: 10px;
        }
        .endpoint {
            background: white;
            border-radius: 8px;
            padding: 20px;
            margin: 20px 0;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }
        .method {
            display: inline-block;
            padding: 5px 10px;
            border-radius: 4px;
            font-weight: bold;
            margin-right: 10px;
            color: white;
        }
        .get {
            background-color: #2ecc71;
        }
        .post {
            background-color: #3498db;
        }
        .ws {
            background-color: #9b59b6;
        }
        .path {
            font-family: monospace;
            font-size: 1.1em;
            background-color: #f5f5f5;
            padding: 3px 6px;
            border-radius: 3px;
        }
        .description {
            margin: 10px 0;
        }
        .auth-required {
            color: #e74c3c;
            font-weight: bold;
            font-size: 0.9em;
            margin-top: 5px;
        }
        .parameters {
            margin-top: 15px;
        }
        pre {
            background-color: #f5f5f5;
            padding: 15px;
            border-radius: 5px;
            overflow-x: auto;
        }
        .response {
            margin-top: 15px;
        }
        .note {
            margin-top: 10px;
            padding: 10px;
            background-color: #f8f9fa;
            border-left: 4px solid #6c757d;
            font-style: italic;
        }
        .back {
            display: inline-block;
            margin-top: 20px;
            color: #3498db;
            text-decoration: none;
        }
        .back:hover {
            text-decoration: underline;
        }
    </style>
</head>
<body>
    <h1>Messaging Endpoints</h1>
    
    <div class="endpoint">
        <div class="method post">POST</div>
        <span class="path">/messages/</span>
        <div class="description">Send a new message to a friend.</div>
        <div class="auth-required">Authentication Required</div>
        <div class="parameters">
            <h3>Request Body:</h3>
            <pre>
{
  "recipient_username": "string",
  "text": "string"
}
            </pre>
        </div>
        <div class="response">
            <h3>Response:</h3>
            <pre>
{
  "id": "string",
  "sender_username": "string",
  "recipient_username": "string",
  "text": "string",
  "created_at": "datetime",
  "is_delivered": "boolean"
}
            </pre>
        </div>
    </div>
    
    <div class="endpoint">
        <div class="method get">GET</div>
        <span class="path">/messages/pending</span>
        <div class="description">Get all pending messages for the current user.</div>
        <div class="auth-required">Authentication Required</div>
        <div class="response">
            <h3>Response:</h3>
            <pre>
[
  {
    "id": "string",
    "sender_username": "string",
    "recipient_username": "string",
    "text": "string",
    "created_at": "datetime",
    "is_delivered": "boolean"
  }
]
            </pre>
        </div>
    </div>
    
    <div class="endpoint">
        <div class="method post">POST</div>
        <span class="path">/messages/delivered/{message_id}</span>
        <div class="description">Mark a message as delivered.</div>
        <div class="auth-required">Authentication Required</div>
        <div class="parameters">
            <h3>Path Parameters:</h3>
            <pre>message_id: string</pre>
        </div>
        <div class="response">
            <h3>Response:</h3>
            <pre>
{
  "status": "success"
}
            </pre>
        </div>
    </div>
    
    <div class="endpoint">
        <div class="method ws">WebSocket</div>
        <span class="path">/messages/ws/{username}</span>
        <div class="description">WebSocket endpoint for real-time messaging.</div>
        <div class="auth-required">Authentication Required (via token in initial message)</div>
        <div class="parameters">
            <h3>Path Parameters:</h3>
            <pre>username: string</pre>
        </div>
        <div class="note">
            <p>After connecting, the client must send an authentication message:</p>
            <pre>
{
  "type": "authenticate",
  "token": "your_access_token"
}
            </pre>
            <p>Once authenticated, the server will send pending messages and then listen for:</p>
            <ul>
                <li>Ping messages to keep the connection alive</li>
                <li>Message delivery confirmations</li>
            </ul>
        </div>
    </div>
    
    <a href="/" class="back">← Back to API Home</a>
</body>
</html>
"""

LANDING_PAGE_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Chimeo API</title>
    <style>
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, 'Open Sans', 'Helvetica Neue', sans-serif;
            line-height: 1.6;
            color: #333;
            max-width: 800px;
            margin: 0 auto;
            padding: 20px;
            background-color: #f9f9f9;
        }
        h1 {
            color: #2c3e50;
            border-bottom: 2px solid #3498db;
            padding-bottom: 10px;
        }
        .card {
            background: white;
            border-radius: 8px;
            padding: 20px;
            margin: 20px 0;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }
        .endpoints {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 15px;
            margin-top: 20px;
        }
        .endpoint {
            background: #e8f4fc;
            padding: 15px;
            border-radius: 6px;
            text-align: center;
            border-left: 4px solid #3498db;
        }
        a {
            color: #3498db;
            text-decoration: none;
            font-weight: 500;
        }
        a:hover {
            text-decoration: underline;
        }
        .version {
            display: inline-block;
            background: #2ecc71;
            color: white;
            padding: 2px 8px;
            border-radius: 4px;
            font-size: 0.8em;
            margin-left: 10px;
        }
    </style>
</head>
<body>
    <h1>Welcome to Chimeo API <span class="version">v1.0.0</span></h1>
    
    <div class="card">
        <p>
            Chimeo is a simple messaging application that provides endpoints for user authentication, 
            messaging, and friend management.
        </p>
        
        <h2>Available Endpoints</h2>
        <div class="endpoints">
            <div class="endpoint">
                <a href="/docs">/docs</a>
                <p>Interactive API documentation</p>
            </div>
            <div class="endpoint">
                <a href="/auth">/auth</a>
                <p>Authentication endpoints</p>
            </div>
            <div class="endpoint">
                <a href="/users">/users</a>
                <p>User management</p>
            </div>
            <div class="endpoint">
                <a href="/messages">/messages</a>
                <p>Messaging endpoints</p>
            </div>
        </div>
    </div>
</body>
</html>
""" 