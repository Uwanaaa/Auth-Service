from django.urls import path
from .views import UserRegistrationView, UserLoginView, ResetPasswordView, ForgotPasswordView

urlpatterns = [
    path('register/', UserRegistrationView.as_view(), name='register'),
    path('login/', UserLoginView.as_view(), name='login'),
    path('forgot-password/', ForgotPasswordView.as_view(), name='forgot_password'),
    path('password-reset/', ResetPasswordView.as_view(), name='password_reset'),
]