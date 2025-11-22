# ChatApp - Real-time WebSocket Chat Application

A Django-based real-time chat application with WebSocket support, user authentication, subscription management, and Stripe payment integration.

## 🚀 Features

- **Real-time Chat**: WebSocket-based messaging using Django Channels
- **User Authentication**: JWT-based authentication with email verification
- **Subscription Plans**: Tiered subscription system with message limits
- **Payment Integration**: Stripe integration for subscription purchases
- **Chat Rooms**: Create and join multiple chat rooms
- **Message Management**: Edit and delete your own messages
- **Admin Panel**: Comprehensive Django admin interface
- **REST API**: Full RESTful API for all operations

## 📋 Prerequisites

- Python 3.8+
- Redis (for WebSocket channels)
- Stripe account (for payments)
- Gmail account (for email verification)

## 🔧 Installation

### 1. Clone the Repository

```bash
git clone <repository-url>
cd ChatApp
```

### 2. Create Virtual Environment

```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Install Redis

**Ubuntu/Debian:**
```bash
sudo apt-get install redis-server
sudo systemctl start redis
```

**macOS:**
```bash
brew install redis
brew services start redis
```

**Windows:**
Download and install from [https://redis.io/download](https://redis.io/download)

### 5. Environment Configuration

Copy the example environment file and configure it:

```bash
cp .env.example .env
```

Edit `.env` with your configuration:

```env
SECRET_KEY=your-secret-key-here
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1,a37295076a65.ngrok-free.app
CSRF_TRUSTED_ORIGINS=https://a37295076a65.ngrok-free.app,http://127.0.0.1:8001

# Redis
REDIS_URL=redis://localhost:6379

# Email (Gmail)
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password

# Stripe
STRIPE_PUBLISHABLE_KEY=pk_test_your_key
STRIPE_SECRET_KEY=sk_test_your_key
STRIPE_WEBHOOK_SECRET=whsec_your_secret

# Site URL
SITE_URL=https://a37295076a65.ngrok-free.app
```

### 6. Database Setup

```bash
python manage.py makemigrations
python manage.py migrate
```

### 7. Create Superuser

```bash
python manage.py createsuperuser
```

### 8. Create Subscription Plans (Optional)

```bash
python manage.py shell
```

```python
from payments.models import SubscriptionPlan

# Free tier (default)
# Users get 10 messages/day by default without a subscription

# Basic Plan
SubscriptionPlan.objects.create(
    name="Basic Plan",
    plan_type="basic",
    price=9.99,
    duration_days=30,
    message_limit=100,  # 100 messages per day
    is_active=True
)

# Pro Plan
SubscriptionPlan.objects.create(
    name="Pro Plan",
    plan_type="pro",
    price=19.99,
    duration_days=30,
    message_limit=None,  # Unlimited messages
    is_active=True
)
```

## 🏃 Running the Application

### Development Server

```bash
# Using Daphne (ASGI server for WebSockets)
daphne -b 0.0.0.0 -p 8001 ChatApp.asgi:application

# Or using Django's development server (WebSockets may not work)
python manage.py runserver 8001
```

Visit:
- Application: http://127.0.0.1:8001
- Admin Panel: http://127.0.0.1:8001/admin
- API Root: http://127.0.0.1:8001/api

## 📡 API Documentation

### Authentication Endpoints

#### Register User
```http
POST /api/users/
Content-Type: application/json

{
  "email": "user@example.com",
  "first_name": "John",
  "last_name": "Doe",
  "password": "securepassword",
  "confirm_password": "securepassword"
}
```

#### Login
```http
POST /api/users/login/
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "securepassword"
}

Response:
{
  "user": {...},
  "access": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc..."
}
```

#### Get Current User
```http
GET /api/users/me/
Authorization: Bearer <access_token>
```

#### Verify Email
```http
GET /api/users/verify/?token=<verification_token>
```

#### Change Password
```http
POST /api/users/change-password/
Authorization: Bearer <access_token>
Content-Type: application/json

{
  "current_password": "oldpassword",
  "new_password": "newpassword",
  "confirm_new_password": "newpassword"
}
```

#### Forgot Password
```http
POST /api/users/forgot-password/
Content-Type: application/json

{
  "email": "user@example.com"
}
```

#### Reset Password
```http
POST /api/users/reset-password/
Content-Type: application/json

{
  "token": "<reset_token>",
  "new_password": "newpassword",
  "confirm_new_password": "newpassword"
}
```

### Chat Endpoints

#### List Chat Rooms
```http
GET /api/chat/rooms/
Authorization: Bearer <access_token>
```

#### Create Chat Room
```http
POST /api/chat/rooms/
Authorization: Bearer <access_token>
Content-Type: application/json

{
  "name": "general",
  "display_name": "General Chat",
  "description": "General discussion room",
  "is_private": false
}
```

#### Join Room
```http
POST /api/chat/rooms/{room_id}/join/
Authorization: Bearer <access_token>
```

#### Leave Room
```http
POST /api/chat/rooms/{room_id}/leave/
Authorization: Bearer <access_token>
```

#### Get My Rooms
```http
GET /api/chat/rooms/my_rooms/
Authorization: Bearer <access_token>
```

#### List Messages
```http
GET /api/chat/messages/?room=<room_name>
Authorization: Bearer <access_token>
```

#### Send Message (REST)
```http
POST /api/chat/messages/
Authorization: Bearer <access_token>
Content-Type: application/json

{
  "room_name": "general",
  "content": "Hello, everyone!"
}
```

#### Edit Message
```http
PATCH /api/chat/messages/{message_id}/
Authorization: Bearer <access_token>
Content-Type: application/json

{
  "content": "Updated message content"
}
```

#### Delete Message
```http
DELETE /api/chat/messages/{message_id}/
Authorization: Bearer <access_token>
```

### Payment Endpoints

#### Create Checkout Session
```http
POST /api/payments/create-checkout-session/
Authorization: Bearer <access_token>
Content-Type: application/json

{
  "plan_id": "<subscription_plan_uuid>"
}

Response:
{
  "checkout_url": "https://checkout.stripe.com/...",
  "session_id": "cs_test_..."
}
```

#### Stripe Webhook
```http
POST /api/payments/stripe-webhook/
Stripe-Signature: <signature>

# This endpoint is called by Stripe, not directly by clients
```

### WebSocket Connection

Connect to chat rooms via WebSocket:

```javascript
const token = '<jwt_access_token>';
const roomName = 'general';
const ws = new WebSocket(`ws://127.0.0.1:8001/ws/chat/${roomName}/?token=${token}`);

ws.onopen = () => {
  console.log('Connected to chat room');
};

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log('Message received:', data);
};

// Send a message
ws.send(JSON.stringify({
  message: 'Hello, WebSocket!'
}));

// Or send plain text
ws.send('Hello, WebSocket!');
```

#### WebSocket Message Types

**Connection Established:**
```json
{
  "type": "connection_established",
  "message": "Welcome! You are now connected to room: general",
  "user": "user@example.com",
  "room": "general"
}
```

**Chat Message:**
```json
{
  "type": "chat_message",
  "message": "Hello, everyone!",
  "username": "user@example.com",
  "user_id": 1,
  "timestamp": "2025-11-21T10:30:00Z",
  "message_id": 42
}
```

**Message History:**
```json
{
  "type": "message_history",
  "messages": [
    {
      "id": 1,
      "message": "Previous message",
      "username": "user@example.com",
      "user_id": 1,
      "timestamp": "2025-11-21T10:00:00Z"
    }
  ]
}
```

**Error:**
```json
{
  "type": "error",
  "message": "Message limit reached. Please upgrade to Pro plan.",
  "error_code": "MESSAGE_LIMIT_EXCEEDED"
}
```

## 🏗️ Project Structure

```
ChatApp/
├── ChatApp/              # Project settings
│   ├── settings.py       # Django settings
│   ├── urls.py           # URL configuration
│   ├── asgi.py           # ASGI application
│   └── wsgi.py           # WSGI application
├── users/                # User management app
│   ├── models.py         # User, EmailVerificationToken, PasswordResetToken
│   ├── views.py          # User API views
│   ├── serializers.py    # User serializers
│   ├── permissions.py    # Custom permissions
│   └── utils.py          # Email utilities
├── chat/                 # Chat app
│   ├── models.py         # ChatRoom, Message
│   ├── views.py          # Chat API views
│   ├── consumers.py      # WebSocket consumers
│   ├── routing.py        # WebSocket URL routing
│   ├── middleware.py     # JWT WebSocket middleware
│   └── serializers.py    # Chat serializers
├── payments/             # Payment & subscription app
│   ├── models.py         # SubscriptionPlan, UserSubscription, Payment, MessageUsage
│   ├── views.py          # Payment API views
│   ├── serializers.py    # Payment serializers
│   ├── admin.py          # Admin configuration
│   └── urls.py           # Payment URLs
├── logs/                 # Log files
├── db.sqlite3            # SQLite database
├── manage.py             # Django management script
├── requirements.txt      # Python dependencies
└── .env                  # Environment variables (not in git)
```

## 💳 Subscription System

### Message Limits

- **Free Tier**: 10 messages per day (default)
- **Basic Plan**: 100 messages per day
- **Pro Plan**: Unlimited messages

### Message Usage Tracking

The system automatically:
- Tracks daily message counts per user
- Resets counts at midnight
- Enforces limits based on subscription
- Provides real-time feedback via WebSocket

## 🔒 Security Features

- JWT token authentication
- Email verification for new accounts
- Password reset functionality
- CSRF protection
- CORS configuration
- Secure password hashing
- SQL injection protection (Django ORM)
- XSS protection
- HTTPS redirect in production
- Secure cookies in production

## 🧪 Testing

```bash
# Run all tests
python manage.py test

# Run specific app tests
python manage.py test users
python manage.py test chat
python manage.py test payments
```

## 📊 Admin Panel

Access the Django admin panel at `http://127.0.0.1:8001/admin`

Features:
- User management
- Chat room management
- Message moderation
- Subscription plan management
- Payment tracking
- Message usage monitoring

## 🐛 Troubleshooting

### Redis Connection Error
```bash
# Check if Redis is running
redis-cli ping
# Should respond with: PONG

# If not running, start Redis
sudo systemctl start redis  # Linux
brew services start redis   # macOS
```

### WebSocket Connection Failed
- Ensure you're using Daphne, not Django's development server
- Check that Redis is running
- Verify JWT token is valid and included in WebSocket URL

### Email Not Sending
- Enable "Less secure app access" or create an App Password for Gmail
- Check EMAIL_HOST_USER and EMAIL_HOST_PASSWORD in .env
- Verify firewall isn't blocking SMTP port 587

### Stripe Webhooks Not Working
- Use Stripe CLI for local testing:
  ```bash
  stripe listen --forward-to http://127.0.0.1:8001/api/payments/stripe-webhook/
  ```
- Update STRIPE_WEBHOOK_SECRET with the webhook signing secret

## 📝 License

This project is licensed under the MIT License.

## 👥 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## 📧 Support

For issues and questions, please create an issue in the GitHub repository.

## 🔄 Deployment

### Production Checklist

1. Set `DEBUG=False` in `.env`
2. Set a strong `SECRET_KEY`
3. Configure `ALLOWED_HOSTS` properly
4. Set up PostgreSQL database (recommended)
5. Configure Redis with persistence
6. Set up SSL/TLS certificates
7. Configure Nginx/Apache as reverse proxy
8. Set up static file serving
9. Configure Stripe production keys
10. Set up monitoring and logging

### Environment Variables for Production

```env
DEBUG=False
SECRET_KEY=<strong-random-key>
ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com
CSRF_TRUSTED_ORIGINS=https://yourdomain.com
REDIS_URL=redis://your-redis-host:6379
SITE_URL=https://yourdomain.com
```

## 🚀 Future Enhancements

- [ ] Direct messaging between users
- [ ] File/image sharing in chat
- [ ] Voice/video chat integration
- [ ] Push notifications
- [ ] Mobile app (React Native)
- [ ] Message search functionality
- [ ] User presence/online status
- [ ] Typing indicators
- [ ] Message reactions
- [ ] Rate limiting for API endpoints
