import jwt
from django.conf import settings
from django.contrib.auth.models import AnonymousUser
from channels.middleware import BaseMiddleware
from channels.db import database_sync_to_async
from urllib.parse import parse_qs
from users.models import CustomUser


@database_sync_to_async
def get_user_from_token(token):
    """
    Get user from JWT token
    """
    try:
        # Decode the JWT token
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=['HS256'])
        user_id = payload.get('user_id')
        
        if user_id:
            user = CustomUser.objects.get(id=user_id)
            return user
    except (jwt.ExpiredSignatureError, jwt.InvalidTokenError, jwt.DecodeError, CustomUser.DoesNotExist):
        pass
    
    return AnonymousUser()


class JWTAuthMiddleware(BaseMiddleware):
    """
    JWT Authentication middleware for WebSocket connections
    """
    
    async def __call__(self, scope, receive, send):
        # Get token from query string
        query_string = scope.get('query_string', b'').decode()
        query_params = parse_qs(query_string)
        token = query_params.get('token', [None])[0]
        
        if token:
            # Get user from token
            user = await get_user_from_token(token)
            scope['user'] = user
        else:
            scope['user'] = AnonymousUser()
        
        return await super().__call__(scope, receive, send)