import jwt
from django.conf import settings
from django.contrib.auth.models import AnonymousUser
from channels.middleware import BaseMiddleware
from channels.db import database_sync_to_async
from urllib.parse import parse_qs
from users.models import CustomUser

@database_sync_to_async
def get_user_from_token(token):
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=['HS256'])
        user_id = payload.get('user_id')
        
        if user_id:
            user = CustomUser.objects.get(id=user_id)
            return user
    except (jwt.ExpiredSignatureError, jwt.InvalidTokenError, jwt.DecodeError, CustomUser.DoesNotExist):
        pass
    
    return AnonymousUser()

class JWTAuthMiddleware(BaseMiddleware):
    async def __call__(self, scope, receive, send):
        query_string = scope.get('query_string', b'').decode()
        query_params = parse_qs(query_string)
        token = query_params.get('token', [None])[0]
        
        print(f"🔐 JWT Middleware - Query string: {query_string}")
        print(f"🔑 JWT Middleware - Token present: {'Yes' if token else 'No'}")
        
        if token:
            user = await get_user_from_token(token)
            scope['user'] = user
            print(f"👤 JWT Middleware - User: {user.email if hasattr(user, 'email') else 'Anonymous'}")
        else:
            scope['user'] = AnonymousUser()
            print("👤 JWT Middleware - No token, setting anonymous user")
        
        return await super().__call__(scope, receive, send)