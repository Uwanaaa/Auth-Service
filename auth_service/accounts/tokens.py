from rest_framework_simplejwt.tokens import RefreshToken

def create_jwt_token(user):
    refresh = RefreshToken.for_user(user)
    return {
        'refresh': str(refresh),
        'access': str(refresh.access_token),
    }

def get_user_from_token(token):
    try:
        from rest_framework_simplejwt.tokens import AccessToken
        return AccessToken(token).payload['user_id']
    except Exception:
        return None