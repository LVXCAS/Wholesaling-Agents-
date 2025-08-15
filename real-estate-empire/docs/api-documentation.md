# Real Estate Empire - API Documentation

## Table of Contents

1. [Overview](#overview)
2. [Authentication](#authentication)
3. [Rate Limiting](#rate-limiting)
4. [Error Handling](#error-handling)
5. [Data Formats](#data-formats)
6. [API Endpoints](#api-endpoints)
7. [Webhooks](#webhooks)
8. [SDKs and Libraries](#sdks-and-libraries)
9. [Examples](#examples)
10. [Changelog](#changelog)

## Overview

The Real Estate Empire API provides programmatic access to all platform features including property analysis, lead management, portfolio tracking, and more. The API follows REST principles and uses JSON for data exchange.

### Base URL
```
Production: https://api.realestate-empire.com/v1
Staging: https://staging-api.realestate-empire.com/v1
```

### API Version
Current version: `v1`

### Content Type
All requests and responses use `application/json` content type.

## Authentication

### API Key Authentication

The API uses API key authentication. Include your API key in the `Authorization` header:

```http
Authorization: Bearer your_api_key_here
```

### Getting an API Key

1. Log into your Real Estate Empire account
2. Go to **Settings** > **API Keys**
3. Click **"Create New Key"**
4. Set permissions and expiration
5. Copy and securely store the generated key

### JWT Token Authentication

For user-specific operations, use JWT tokens obtained through login:

```http
POST /auth/login
Content-Type: application/json

{
  "username": "your_username",
  "password": "your_password"
}
```

Response:
```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "token_type": "bearer",
  "expires_in": 1800
}
```

Use the access token in subsequent requests:
```http
Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...
```

## Rate Limiting

### Limits

- **API Key**: 1000 requests per hour
- **User Token**: 100 requests per minute
- **Webhook**: 10 requests per second

### Headers

Rate limit information is included in response headers:

```http
X-RateLimit-Limit: 1000
X-RateLimit-Remaining: 999
X-RateLimit-Reset: 1640995200
```

### Exceeding Limits

When rate limits are exceeded, the API returns:

```http
HTTP/1.1 429 Too Many Requests
Content-Type: application/json

{
  "error": {
    "code": "RATE_LIMIT_EXCEEDED",
    "message": "Rate limit exceeded. Try again in 60 seconds.",
    "retry_after": 60
  }
}
```

## Error Handling

### HTTP Status Codes

- `200` - Success
- `201` - Created
- `400` - Bad Request
- `401` - Unauthorized
- `403` - Forbidden
- `404` - Not Found
- `422` - Validation Error
- `429` - Rate Limit Exceeded
- `500` - Internal Server Error

### Error Response Format

```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Invalid input data",
    "details": {
      "field": "email",
      "issue": "Invalid email format"
    },
    "timestamp": "2024-01-01T12:00:00Z"
  }
}
```

### Common Error Codes

- `INVALID_API_KEY` - API key is invalid or expired
- `INSUFFICIENT_PERMISSIONS` - API key lacks required permissions
- `VALIDATION_ERROR` - Request data validation failed
- `RESOURCE_NOT_FOUND` - Requested resource doesn't exist
- `DUPLICATE_RESOURCE` - Resource already exists
- `RATE_LIMIT_EXCEEDED` - Too many requests

## Data Formats

### Date/Time Format

All dates use ISO 8601 format in UTC:
```json
{
  "created_at": "2024-01-01T12:00:00Z",
  "updated_at": "2024-01-01T12:30:00Z"
}
```

### Pagination

List endpoints support pagination:

```http
GET /properties?page=1&limit=20&sort=created_at&order=desc
```

Response includes pagination metadata:
```json
{
  "data": [...],
  "pagination": {
    "page": 1,
    "limit": 20,
    "total": 150,
    "pages": 8,
    "has_next": true,
    "has_prev": false
  }
}
```

### Filtering and Sorting

Most list endpoints support filtering and sorting:

```http
GET /properties?city=Miami&property_type=SFR&min_price=100000&max_price=500000
GET /leads?status=interested&created_after=2024-01-01&sort=score&order=desc
```

## API Endpoints

### Authentication Endpoints

#### Login
```http
POST /auth/login
```

Request:
```json
{
  "username": "user@example.com",
  "password": "password123",
  "remember_me": false
}
```

#### Refresh Token
```http
POST /auth/refresh
```

Request:
```json
{
  "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
}
```

#### Logout
```http
POST /auth/logout
```

### Property Analysis Endpoints

#### Analyze Property
```http
POST /properties/analyze
```

Request:
```json
{
  "address": "123 Main St, Miami, FL 33101",
  "property_type": "SFR",
  "bedrooms": 3,
  "bathrooms": 2,
  "square_feet": 1500,
  "purchase_price": 250000,
  "repair_cost": 25000,
  "strategy": "buy_and_hold"
}
```

Response:
```json
{
  "property_id": "prop_123456",
  "analysis": {
    "arv": 320000,
    "cap_rate": 8.5,
    "cash_flow": 450,
    "cash_on_cash_return": 12.3,
    "roi": 15.7
  },
  "comparables": [
    {
      "address": "456 Oak St",
      "sale_price": 315000,
      "sale_date": "2024-01-15",
      "square_feet": 1480
    }
  ],
  "created_at": "2024-01-01T12:00:00Z"
}
```

#### Get Property Analysis
```http
GET /properties/{property_id}
```

#### List Properties
```http
GET /properties?page=1&limit=20
```

#### Update Property
```http
PUT /properties/{property_id}
```

#### Delete Property
```http
DELETE /properties/{property_id}
```

### Lead Management Endpoints

#### Create Lead
```http
POST /leads
```

Request:
```json
{
  "property_address": "789 Pine St, Orlando, FL 32801",
  "owner_name": "John Smith",
  "owner_email": "john@example.com",
  "owner_phone": "+1234567890",
  "source": "public_records",
  "motivation_score": 7
}
```

#### Get Lead
```http
GET /leads/{lead_id}
```

#### List Leads
```http
GET /leads?status=new&city=Miami&page=1&limit=20
```

#### Update Lead Status
```http
PATCH /leads/{lead_id}/status
```

Request:
```json
{
  "status": "contacted",
  "notes": "Initial contact made via email"
}
```

#### Contact Lead
```http
POST /leads/{lead_id}/contact
```

Request:
```json
{
  "method": "email",
  "template": "initial_inquiry",
  "custom_message": "I'm interested in your property..."
}
```

### Communication Endpoints

#### Send Email
```http
POST /communications/email
```

Request:
```json
{
  "to": "owner@example.com",
  "subject": "Property Inquiry",
  "template": "property_inquiry",
  "variables": {
    "property_address": "123 Main St",
    "investor_name": "Jane Doe"
  }
}
```

#### Send SMS
```http
POST /communications/sms
```

Request:
```json
{
  "to": "+1234567890",
  "message": "Hi, I'm interested in your property at 123 Main St. Can we discuss?"
}
```

#### Get Communication History
```http
GET /communications/history?lead_id=lead_123&page=1&limit=20
```

### Portfolio Management Endpoints

#### Add Property to Portfolio
```http
POST /portfolio/properties
```

Request:
```json
{
  "property_id": "prop_123456",
  "acquisition_date": "2024-01-01",
  "acquisition_cost": 275000,
  "strategy": "buy_and_hold"
}
```

#### Get Portfolio Summary
```http
GET /portfolio/summary
```

Response:
```json
{
  "total_properties": 15,
  "total_value": 4250000,
  "total_equity": 1850000,
  "monthly_cash_flow": 3200,
  "average_cap_rate": 7.8,
  "average_coc_return": 11.2
}
```

#### Get Portfolio Performance
```http
GET /portfolio/performance?period=12m
```

### Contract Management Endpoints

#### Generate Contract
```http
POST /contracts/generate
```

Request:
```json
{
  "template": "purchase_agreement",
  "property_id": "prop_123456",
  "buyer": {
    "name": "Jane Investor",
    "email": "jane@example.com"
  },
  "seller": {
    "name": "John Owner",
    "email": "john@example.com"
  },
  "terms": {
    "purchase_price": 250000,
    "earnest_money": 5000,
    "closing_date": "2024-02-15"
  }
}
```

#### Send for Signature
```http
POST /contracts/{contract_id}/sign
```

Request:
```json
{
  "signers": [
    {
      "name": "Jane Investor",
      "email": "jane@example.com",
      "role": "buyer"
    },
    {
      "name": "John Owner",
      "email": "john@example.com",
      "role": "seller"
    }
  ]
}
```

### Reporting Endpoints

#### Generate Report
```http
POST /reports/generate
```

Request:
```json
{
  "type": "portfolio_performance",
  "period": {
    "start": "2024-01-01",
    "end": "2024-12-31"
  },
  "format": "pdf",
  "email_to": "investor@example.com"
}
```

#### Get Report Status
```http
GET /reports/{report_id}/status
```

#### Download Report
```http
GET /reports/{report_id}/download
```

### Webhook Endpoints

#### List Webhooks
```http
GET /webhooks
```

#### Create Webhook
```http
POST /webhooks
```

Request:
```json
{
  "url": "https://your-app.com/webhooks/real-estate-empire",
  "events": ["property.analyzed", "lead.updated", "contract.signed"],
  "secret": "your_webhook_secret"
}
```

#### Update Webhook
```http
PUT /webhooks/{webhook_id}
```

#### Delete Webhook
```http
DELETE /webhooks/{webhook_id}
```

## Webhooks

### Overview

Webhooks allow your application to receive real-time notifications when events occur in Real Estate Empire.

### Webhook Events

#### Property Events
- `property.created` - New property added
- `property.analyzed` - Property analysis completed
- `property.updated` - Property information updated
- `property.deleted` - Property removed

#### Lead Events
- `lead.created` - New lead added
- `lead.updated` - Lead information updated
- `lead.status_changed` - Lead status changed
- `lead.contacted` - Lead contacted

#### Communication Events
- `email.sent` - Email sent successfully
- `email.delivered` - Email delivered
- `email.opened` - Email opened by recipient
- `sms.sent` - SMS sent successfully
- `sms.delivered` - SMS delivered

#### Contract Events
- `contract.generated` - Contract generated
- `contract.sent` - Contract sent for signature
- `contract.signed` - Contract signed by party
- `contract.completed` - All parties signed

### Webhook Payload

```json
{
  "event": "property.analyzed",
  "timestamp": "2024-01-01T12:00:00Z",
  "data": {
    "property_id": "prop_123456",
    "analysis": {
      "arv": 320000,
      "cap_rate": 8.5,
      "cash_flow": 450
    }
  },
  "webhook_id": "webhook_789"
}
```

### Webhook Security

Verify webhook authenticity using the signature header:

```python
import hmac
import hashlib

def verify_webhook(payload, signature, secret):
    expected_signature = hmac.new(
        secret.encode('utf-8'),
        payload.encode('utf-8'),
        hashlib.sha256
    ).hexdigest()
    
    return hmac.compare_digest(f"sha256={expected_signature}", signature)

# Usage
signature = request.headers.get('X-Signature-256')
is_valid = verify_webhook(request.body, signature, webhook_secret)
```

## SDKs and Libraries

### Official SDKs

#### Python SDK
```bash
pip install realestate-empire-sdk
```

```python
from realestate_empire import Client

client = Client(api_key="your_api_key")

# Analyze property
analysis = client.properties.analyze({
    "address": "123 Main St, Miami, FL",
    "purchase_price": 250000
})

print(f"Cap Rate: {analysis.cap_rate}%")
```

#### JavaScript/Node.js SDK
```bash
npm install realestate-empire-sdk
```

```javascript
const RealEstateEmpire = require('realestate-empire-sdk');

const client = new RealEstateEmpire({
  apiKey: 'your_api_key'
});

// Analyze property
const analysis = await client.properties.analyze({
  address: '123 Main St, Miami, FL',
  purchasePrice: 250000
});

console.log(`Cap Rate: ${analysis.capRate}%`);
```

### Community Libraries

- **PHP**: `realestate-empire/php-sdk`
- **Ruby**: `realestate-empire-ruby`
- **Go**: `go-realestate-empire`
- **C#**: `RealEstateEmpire.NET`

## Examples

### Complete Property Analysis Workflow

```python
import requests

# Configuration
API_BASE = "https://api.realestate-empire.com/v1"
API_KEY = "your_api_key_here"
HEADERS = {
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json"
}

# 1. Analyze property
property_data = {
    "address": "123 Main St, Miami, FL 33101",
    "property_type": "SFR",
    "bedrooms": 3,
    "bathrooms": 2,
    "square_feet": 1500,
    "purchase_price": 250000,
    "repair_cost": 25000,
    "strategy": "buy_and_hold"
}

response = requests.post(
    f"{API_BASE}/properties/analyze",
    json=property_data,
    headers=HEADERS
)

analysis = response.json()
property_id = analysis["property_id"]

print(f"Property analyzed: {property_id}")
print(f"Cap Rate: {analysis['analysis']['cap_rate']}%")
print(f"Monthly Cash Flow: ${analysis['analysis']['cash_flow']}")

# 2. Create lead for property owner
lead_data = {
    "property_address": property_data["address"],
    "owner_name": "John Smith",
    "owner_email": "john@example.com",
    "source": "analysis",
    "motivation_score": 8
}

response = requests.post(
    f"{API_BASE}/leads",
    json=lead_data,
    headers=HEADERS
)

lead = response.json()
lead_id = lead["lead_id"]

print(f"Lead created: {lead_id}")

# 3. Send initial contact email
contact_data = {
    "method": "email",
    "template": "initial_inquiry",
    "custom_message": f"I'm interested in your property at {property_data['address']}"
}

response = requests.post(
    f"{API_BASE}/leads/{lead_id}/contact",
    json=contact_data,
    headers=HEADERS
)

print("Initial contact sent")

# 4. Add to portfolio if deal proceeds
portfolio_data = {
    "property_id": property_id,
    "acquisition_date": "2024-01-01",
    "acquisition_cost": 275000,
    "strategy": "buy_and_hold"
}

response = requests.post(
    f"{API_BASE}/portfolio/properties",
    json=portfolio_data,
    headers=HEADERS
)

print("Property added to portfolio")
```

### Webhook Handler Example

```python
from flask import Flask, request, jsonify
import hmac
import hashlib

app = Flask(__name__)
WEBHOOK_SECRET = "your_webhook_secret"

@app.route('/webhooks/real-estate-empire', methods=['POST'])
def handle_webhook():
    # Verify signature
    signature = request.headers.get('X-Signature-256')
    payload = request.get_data()
    
    expected_signature = hmac.new(
        WEBHOOK_SECRET.encode('utf-8'),
        payload,
        hashlib.sha256
    ).hexdigest()
    
    if not hmac.compare_digest(f"sha256={expected_signature}", signature):
        return jsonify({"error": "Invalid signature"}), 401
    
    # Process webhook
    data = request.get_json()
    event = data['event']
    
    if event == 'property.analyzed':
        property_id = data['data']['property_id']
        cap_rate = data['data']['analysis']['cap_rate']
        
        # Send notification if good deal
        if cap_rate > 8.0:
            send_deal_alert(property_id, cap_rate)
    
    elif event == 'lead.status_changed':
        lead_id = data['data']['lead_id']
        new_status = data['data']['new_status']
        
        # Update CRM system
        update_crm_lead(lead_id, new_status)
    
    return jsonify({"status": "processed"})

def send_deal_alert(property_id, cap_rate):
    # Implementation to send alert
    pass

def update_crm_lead(lead_id, status):
    # Implementation to update CRM
    pass

if __name__ == '__main__':
    app.run(debug=True)
```

## Changelog

### Version 1.0.0 (2024-01-01)
- Initial API release
- Property analysis endpoints
- Lead management endpoints
- Basic authentication

### Version 1.1.0 (2024-02-01)
- Added portfolio management endpoints
- Communication endpoints (email/SMS)
- Webhook support
- Rate limiting implementation

### Version 1.2.0 (2024-03-01)
- Contract management endpoints
- Advanced filtering and sorting
- Bulk operations support
- Enhanced error handling

### Version 1.3.0 (2024-04-01)
- Reporting endpoints
- Data export functionality
- Improved pagination
- Performance optimizations

---

## Support

### API Support
- **Email**: api-support@realestate-empire.com
- **Documentation**: https://docs.realestate-empire.com
- **Status Page**: https://status.realestate-empire.com

### Rate Limit Increases
Contact support for higher rate limits with:
- Use case description
- Expected request volume
- Business justification

### Feature Requests
Submit feature requests through:
- GitHub Issues (for open source components)
- Email: features@realestate-empire.com
- In-app feedback form

---

*This API documentation is regularly updated. For the latest version and interactive API explorer, visit https://docs.realestate-empire.com*