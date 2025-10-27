# ChatApp Subscription System Documentation

## Overview

This documentation covers the complete subscription system for ChatApp with Stripe integration, message limits, and user management.

## Features

- **Basic Plan**: Free plan with 50 messages per day
- **Pro Plans**: Paid plans with unlimited messages
  - 1 Day: $2.99
  - 7 Days: $9.99
  - 15 Days: $19.99
  - 30 Days: $29.99
- **Stripe Integration**: Secure payment processing
- **Message Limits**: Automatic enforcement in chat system
- **Admin Panel**: Full subscription management

## Setup Instructions

### 1. Environment Configuration

Add these variables to your `.env` file:

```env
# Stripe Configuration
STRIPE_PUBLISHABLE_KEY=pk_test_your_publishable_key_here
STRIPE_SECRET_KEY=sk_test_your_secret_key_here
STRIPE_WEBHOOK_SECRET=whsec_your_webhook_secret_here
```

### 2. Stripe Setup

1. Create a Stripe account at https://stripe.com
2. Get your API keys from the Stripe Dashboard
3. Set up webhooks pointing to: `https://your-ngrok-url/api/subscriptions/webhook/`
4. Enable these webhook events:
   - `payment_intent.succeeded`
   - `payment_intent.payment_failed`
   - `invoice.payment_succeeded`

### 3. Database Setup

```bash
python manage.py makemigrations subscriptions
python manage.py migrate
python manage.py create_plans
```

## API Endpoints

### Authentication Required
All subscription endpoints require JWT authentication via `Authorization: Bearer <token>` header.

### Plans Endpoints

#### GET `/api/subscriptions/plans/`
Get all available plans.

**Response:**
```json
[
  {
    "id": 1,
    "name": "Basic Plan",
    "plan_type": "basic",
    "duration_days": null,
    "duration_display": null,
    "price": "0.00",
    "message_limit": 50,
    "is_active": true,
    "created_at": "2025-10-27T05:30:00Z"
  },
  {
    "id": 2,
    "name": "Pro 1 Day",
    "plan_type": "pro",
    "duration_days": 1,
    "duration_display": "1 Day",
    "price": "2.99",
    "message_limit": -1,
    "is_active": true,
    "created_at": "2025-10-27T05:30:00Z"
  }
]
```

### Subscription Endpoints

#### GET `/api/subscriptions/status/`
Get current user's subscription status.

**Response:**
```json
{
  "id": 1,
  "plan": 2,
  "plan_details": {
    "id": 2,
    "name": "Pro 1 Day",
    "plan_type": "pro",
    "duration_days": 1,
    "price": "2.99",
    "message_limit": -1
  },
  "status": "active",
  "start_date": "2025-10-27T05:30:00Z",
  "end_date": "2025-10-28T05:30:00Z",
  "is_active": true,
  "days_remaining": 1,
  "is_expired": false
}
```

#### GET `/api/subscriptions/subscriptions/`
Get user's subscription history.

#### POST `/api/subscriptions/subscriptions/{id}/cancel/`
Cancel a subscription.

### Payment Endpoints

#### POST `/api/subscriptions/create-payment-intent/`
Create a Stripe Payment Intent for purchasing a plan.

**Request:**
```json
{
  "plan_id": 2
}
```

**Response:**
```json
{
  "client_secret": "pi_xxx_secret_xxx",
  "payment_id": 1,
  "amount": "2.99"
}
```

### Message Usage Endpoints

#### GET `/api/subscriptions/message-usage/`
Get user's message usage statistics.

**Response:**
```json
{
  "messages_sent_today": 25,
  "total_messages_sent": 150,
  "last_reset_date": "2025-10-27",
  "can_send_message": true,
  "remaining_messages": 25
}
```

#### GET `/api/subscriptions/status/`
Get comprehensive user status (subscription + message usage).

**Response:**
```json
{
  "id": 1,
  "email": "user@example.com",
  "subscription": {
    "id": 1,
    "plan_details": {
      "name": "Pro 1 Day",
      "price": "2.99"
    },
    "status": "active",
    "days_remaining": 1
  },
  "message_usage": {
    "messages_sent_today": 25,
    "can_send_message": true,
    "remaining_messages": "unlimited"
  }
}
```

### Webhook Endpoint

#### POST `/api/subscriptions/webhook/`
Stripe webhook endpoint for payment processing.

This endpoint automatically:
- Activates subscriptions on successful payment
- Handles payment failures
- Updates subscription status

## Frontend Integration

### 1. Include Stripe.js

```html
<script src="https://js.stripe.com/v3/"></script>
```

### 2. Initialize Stripe

```javascript
const stripe = Stripe('pk_test_your_publishable_key');
const elements = stripe.elements();
const cardElement = elements.create('card');
cardElement.mount('#card-element');
```

### 3. Create Payment Intent

```javascript
async function purchasePlan(planId) {
    const response = await fetch('/api/subscriptions/create-payment-intent/', {
        method: 'POST',
        headers: {
            'Authorization': `Bearer ${authToken}`,
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ plan_id: planId })
    });
    
    const { client_secret } = await response.json();
    
    // Confirm payment
    const { error } = await stripe.confirmPayment({
        elements,
        clientSecret: client_secret,
        confirmParams: {
            return_url: window.location.href,
        },
    });
    
    if (error) {
        console.error('Payment failed:', error.message);
    } else {
        console.log('Payment succeeded!');
    }
}
```

## Chat System Integration

The chat system automatically enforces message limits:

### WebSocket Messages

When a user exceeds their message limit, they receive:

```json
{
  "type": "error",
  "message": "Message limit reached. Please upgrade to Pro plan for unlimited messages.",
  "error_code": "MESSAGE_LIMIT_EXCEEDED"
}
```

### Message Counting

- Messages are counted per user per day
- Counts reset at midnight
- Pro users with unlimited plans can send infinite messages
- Basic users are limited to 50 messages per day

## Admin Panel

Access the Django admin panel to manage:

- **Plans**: Create, edit, and manage subscription plans
- **Subscriptions**: View and manage user subscriptions
- **Payments**: Track payment history and status
- **Message Usage**: Monitor user message consumption

## Testing

### 1. Test Cards (Stripe)

Use these test card numbers:

- **Success**: 4242424242424242
- **Declined**: 4000000000000002
- **Insufficient Funds**: 4000000000009995

### 2. Test Workflow

1. Register a new user
2. Send 50 messages (should work)
3. Try to send the 51st message (should be blocked)
4. Purchase a Pro plan
5. Send unlimited messages

## Error Handling

### Common Error Codes

- `MESSAGE_LIMIT_EXCEEDED`: User has reached daily message limit
- `INVALID_PLAN`: Plan ID doesn't exist or is inactive
- `PAYMENT_FAILED`: Stripe payment processing failed
- `SUBSCRIPTION_EXPIRED`: User's subscription has expired

### Error Responses

```json
{
  "error": "Message limit reached",
  "error_code": "MESSAGE_LIMIT_EXCEEDED",
  "details": {
    "messages_sent_today": 50,
    "limit": 50,
    "subscription_required": true
  }
}
```

## Security Considerations

1. **JWT Authentication**: All endpoints require valid JWT tokens
2. **Stripe Webhooks**: Verify webhook signatures
3. **Rate Limiting**: Implement rate limiting for payment endpoints
4. **Input Validation**: All inputs are validated and sanitized
5. **HTTPS Only**: All payment operations require HTTPS

## Deployment Notes

### ngrok URL Configuration

When using ngrok, update your Stripe webhook URL to:
```
https://your-ngrok-url.ngrok-free.app/api/subscriptions/webhook/
```

### Environment Variables

Ensure all Stripe keys are properly configured in production:

```env
STRIPE_PUBLISHABLE_KEY=pk_live_your_live_key
STRIPE_SECRET_KEY=sk_live_your_live_key
STRIPE_WEBHOOK_SECRET=whsec_your_webhook_secret
```

## Support

For issues with the subscription system:

1. Check Django logs for errors
2. Verify Stripe webhook delivery in Stripe Dashboard
3. Ensure proper JWT authentication
4. Validate environment variables

## Example Usage

Check `subscription_demo.html` for a complete frontend implementation example.