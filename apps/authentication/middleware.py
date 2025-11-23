# apps/authentication/middleware.py
from django.contrib.auth.models import AnonymousUser
from rest_framework_simplejwt.tokens import AccessToken
from channels.db import database_sync_to_async
from channels.middleware import BaseMiddleware
from django.contrib.auth import get_user_model
from urllib.parse import parse_qs

@database_sync_to_async
def get_user(token_key):
    try:
        access_token = AccessToken(token_key)
        User = get_user_model()
        return User.objects.get(id=access_token['user_id'])
    except Exception as e:
        print(f"--- [JWT Error] {e}")
        return AnonymousUser()

class JWTAuthMiddleware(BaseMiddleware):
    async def __call__(self, scope, receive, send):
        # Lấy token từ URL: ws://...?token=xxxx
        try:
            query_string = scope.get('query_string', b'').decode()
            query_params = parse_qs(query_string)
            token = query_params.get('token', [None])[0]
            
            if token:
                scope['user'] = await get_user(token)
                print(f"--- [WS AUTH] User identified: {scope['user']}")
            else:
                scope['user'] = AnonymousUser()
        except Exception:
            scope['user'] = AnonymousUser()
            
        return await super().__call__(scope, receive, send)