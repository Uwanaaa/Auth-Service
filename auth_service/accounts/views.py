from rest_framework import generics, permissions
from django.utils.translation import gettext as _
from django.utils.decorators import method_decorator
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import get_user_model
from django.core.mail import send_mail
from django.conf import settings
from drf_spectacular.utils import extend_schema
from .serializers import UserSerializer, LoginSerializer, ForgotPasswordSerializer, ResetPasswordSerializer
from django_ratelimit.decorators import ratelimit
from rest_framework.response import Response
from rest_framework import status
import redis, uuid, os
from dotenv import load_dotenv


load_dotenv()

User = get_user_model()
redis_client = redis.Redis.from_url(os.getenv('REDIS_URL', 'redis://localhost:6379/0'))

class UserRegistrationView(generics.CreateAPIView):
    """
    API view to register a new user.
    """
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [permissions.AllowAny]
 
    @extend_schema(
        summary="Register user",
        description="Endpoint to register a new user with email and password.",
        request=UserSerializer,
        responses={201: UserSerializer}
    )
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        return Response({
            "user": serializer.data,
            "message": _("User registered successfully.")
        }, status=status.HTTP_201_CREATED)


@method_decorator(ratelimit(key='ip', rate='5/m', block=True), name='dispatch')
class UserLoginView(generics.GenericAPIView):
    """
    API view to log in a user and return JWT tokens only if the user is registered.
    """
    serializer_class = LoginSerializer
    permission_classes = [permissions.AllowAny]

    @extend_schema(
        summary="User login",
        description="Endpoint to log in a user and receive JWT tokens.",
        request=LoginSerializer,
        responses={200: {"type": "object", "properties": {"refresh": {"type": "string"}, "access": {"type": "string"}, "message": {"type": "string"}}}}
    )
    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        try:
            serializer.is_valid(raise_exception=True)
            user = serializer.validated_data['user']
        except Exception:
            return Response(
                {"error": "Invalid credentials."},
                status=status.HTTP_401_UNAUTHORIZED
            )

        refresh = RefreshToken.for_user(user)
        return Response({
            "refresh": str(refresh),
            "access": str(refresh.access_token),
            "message": _("Login successful.")
        }, status=status.HTTP_200_OK)


@method_decorator(ratelimit(key='ip', rate='5/m', block=True), name='dispatch')
class ForgotPasswordView(generics.GenericAPIView):
    """
    API view to initiate password reset by sending a token to the user's email.
    """
    permission_classes = [permissions.AllowAny]
    serializer_class = ForgotPasswordSerializer

    @extend_schema(
        summary="Forgot Password",
        description="Endpoint to initiate password reset by sending a token to the user's email.",
        request=ForgotPasswordSerializer,
        responses={200: {"type": "object", "properties": {"message": {"type": "string"}}}, 404: {"type": "object", "properties": {"error": {"type": "string"}}}}
    )
    def post(self, request):
        email = request.data.get('email')
        user = User.objects.filter(email=email).first()
        if not user:
            return Response({"error": "User not found."}, status=status.HTTP_404_NOT_FOUND)
        
        token = str(uuid.uuid4())
        redis_client.setex(f"reset_token:{token}", 600, email)  # 10 minutes expiry
        
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        send_mail(
            'Password Reset',
            f'Your password reset token is: {token}',
            settings.DEFAULT_FROM_EMAIL,
            [email],
            fail_silently=True,
        )

        return Response({"message": "Password reset token sent to email."}, status=status.HTTP_200_OK)


@method_decorator(ratelimit(key='ip', rate='5/m', block=True), name='dispatch')
class ResetPasswordView(generics.GenericAPIView):
    """
    API view to reset password using the token sent to email with ratelimiting.
    """
    permission_classes = [permissions.AllowAny]
    serializer_class = ResetPasswordSerializer


    @extend_schema(
        summary="Reset Password",
        description="Endpoint to reset password using the token sent to email.",
        request=ResetPasswordSerializer,
        responses={200: {"type": "object", "properties": {"message": {"type": "string"}}}, 400: {"type": "object", "properties": {"error": {"type": "string"}}}, 404: {"type": "object", "properties": {"error": {"type": "string"}}}}
    )
    def post(self, request):
        token = request.data.get('token')
        new_password = request.data.get('new_password')
        email = redis_client.get(f"reset_token:{token}")

        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)

        if not email:
            return Response({"error": "Invalid or expired token."}, status=status.HTTP_400_BAD_REQUEST)
        
        user = User.objects.filter(email=email.decode()).first()
        if not user:
            return Response({"error": "User not found."}, status=status.HTTP_404_NOT_FOUND)
        
        user.set_password(new_password)
        user.save()
        redis_client.delete(f"reset_token:{token}")

        return Response({"message": "Password reset successful."}, status=status.HTTP_200_OK)
