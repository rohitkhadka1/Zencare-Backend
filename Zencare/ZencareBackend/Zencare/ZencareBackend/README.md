# Zencare Backend API Documentation

## Base URL
```
http://127.0.0.1:8000
```

## Authentication

The API uses JWT (JSON Web Token) for authentication. All authenticated endpoints require a valid JWT token in the Authorization header.

### Headers for Authenticated Requests
```
Authorization: Bearer <access_token>
Content-Type: application/json
```

## Endpoints

### 1. User Registration
Register a new user in the system.

**Endpoint:** `POST /auth/register/`

**Request Body:**
```json
{
    "email": "user@example.com",
    "username": "username",
    "password": "your_password",
    "password2": "your_password",
    "user_type": "patient",  // Options: "patient", "doctor", "admin"
    "phone_number": "1234567890",
    "date_of_birth": "1990-01-01",
    "address": "Your address"
}
```

**Response (200 OK):**
```json
{
    "user": {
        "email": "user@example.com",
        "username": "username",
        "user_type": "patient",
        "phone_number": "1234567890",
        "date_of_birth": "1990-01-01",
        "address": "Your address"
    },
    "refresh": "<refresh_token>",
    "access": "<access_token>"
}
```

**Error Response (400 Bad Request):**
```json
{
    "email": ["This field is required."],
    "password": ["Password fields didn't match."],
    // ... other validation errors
}
```

### 2. User Login
Authenticate a user and receive JWT tokens.

**Endpoint:** `POST /auth/login/`

**Request Body:**
```json
{
    "email": "user@example.com",
    "password": "your_password"
}
```

**Response (200 OK):**
```json
{
    "refresh": "<refresh_token>",
    "access": "<access_token>"
}
```

**Error Response (401 Unauthorized):**
```json
{
    "error": "Invalid credentials"
}
```

## Token Management

### Access Token
- Used for authenticating API requests
- Valid for 60 minutes
- Must be included in the Authorization header for protected endpoints

### Refresh Token
- Used to obtain new access tokens
- Valid for 1 day
- Should be stored securely

## Error Handling

### Common HTTP Status Codes
- 200: Success
- 201: Created (for registration)
- 400: Bad Request (validation errors)
- 401: Unauthorized (invalid credentials)
- 403: Forbidden (valid token but insufficient permissions)

### Error Response Format
```json
{
    "error": "Error message",
    // or
    "field_name": ["Error message"]
}
```

## Frontend Implementation Guide

1. **Token Storage**
   ```javascript
   // Store tokens in localStorage or secure storage
   localStorage.setItem('access_token', response.access);
   localStorage.setItem('refresh_token', response.refresh);
   ```

2. **Making Authenticated Requests**
   ```javascript
   const headers = {
       'Authorization': `Bearer ${localStorage.getItem('access_token')}`,
       'Content-Type': 'application/json'
   };

   fetch('http://127.0.0.1:8000/protected-endpoint/', {
       headers: headers
   });
   ```

3. **Token Refresh Implementation**
   ```javascript
   async function refreshToken() {
       const response = await fetch('http://127.0.0.1:8000/auth/token/refresh/', {
           method: 'POST',
           headers: {
               'Content-Type': 'application/json'
           },
           body: JSON.stringify({
               refresh: localStorage.getItem('refresh_token')
           })
       });
       
       const data = await response.json();
       localStorage.setItem('access_token', data.access);
   }
   ```

## Security Best Practices

1. Always use HTTPS in production
2. Store tokens securely (preferably in HTTP-only cookies)
3. Implement token refresh logic before access token expires
4. Clear tokens on logout
5. Never store sensitive data in localStorage in production

## Example Usage

### Registration
```javascript
async function registerUser(userData) {
    try {
        const response = await fetch('http://127.0.0.1:8000/auth/register/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(userData)
        });
        
        const data = await response.json();
        if (response.ok) {
            // Store tokens
            localStorage.setItem('access_token', data.access);
            localStorage.setItem('refresh_token', data.refresh);
            return data;
        } else {
            throw new Error(data.error || 'Registration failed');
        }
    } catch (error) {
        console.error('Registration error:', error);
        throw error;
    }
}
```

### Login
```javascript
async function loginUser(credentials) {
    try {
        const response = await fetch('http://127.0.0.1:8000/auth/login/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(credentials)
        });
        
        const data = await response.json();
        if (response.ok) {
            // Store tokens
            localStorage.setItem('access_token', data.access);
            localStorage.setItem('refresh_token', data.refresh);
            return data;
        } else {
            throw new Error(data.error || 'Login failed');
        }
    } catch (error) {
        console.error('Login error:', error);
        throw error;
    }
}
```

## Support

For any questions or issues, please contact the backend team. 