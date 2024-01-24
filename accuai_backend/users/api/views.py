import logging

from django.contrib.auth import get_user_model, login
from django.contrib.auth.tokens import default_token_generator
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.urls import reverse
from rest_framework import status
from rest_framework.decorators import action, api_view
from rest_framework.mixins import ListModelMixin, RetrieveModelMixin, UpdateModelMixin, CreateModelMixin
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.viewsets import GenericViewSet, ModelViewSet
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.permissions import IsAuthenticated
from django.template.loader import render_to_string
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes
from django.contrib.sites.shortcuts import get_current_site
from django.core.mail import send_mail
from django.conf import settings


from .serializers import UserSerializer
#from users.models import User as UserType

    
######## My code ###########

User = get_user_model()

class RegisterViewSet(GenericViewSet, CreateModelMixin):

    queryset= User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [AllowAny]


    """Register a User"""
    @action(detail=False, methods=['post'], permission_classes=[AllowAny])
    def register(self, request):
        serializer= UserSerializer(data= request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()

        # Send verification email
        self.send_verification_email(request, user)
        return Response({"message": "User registered successfully. Check your email for verification."}, status=status.HTTP_201_CREATED)
    
    """Resend verification email"""
    @action(detail=False, methods=['post'], permission_classes=[IsAuthenticated])
    def resend_verification_email(self, request):
        user = request.user
        if not user.is_verified:
            # Send verification email
            self.send_verification_email(request, user)
            return Response({"message": "Verification email resent. Check your email for verification."}, status=status.HTTP_200_OK)
        else:
            return Response({"error": "Email already verified."}, status=status.HTTP_400_BAD_REQUEST)

    """Send verification email"""    
    def send_verification_email(self, request, user):
        current_site = get_current_site(request)
        subject = 'Activate your account'
        template_name = 'verification_email.txt'
        print(current_site, "current site")
        context = {
            'user': user,
            'protocol': 'https' if request.is_secure() else 'http',
            'domain': current_site.domain,
            'uid': urlsafe_base64_encode(force_bytes(user.pk)),
            'token': RefreshToken.for_user(user).access_token,
        }

        self.send_email(request, user.email, subject, template_name, context)

    """Forgot password"""
    @action(detail=False, methods=['post'], permission_classes=[AllowAny])
    def forgot_password(self, request):
        email = request.data.get('email')
        try:
            user= User.objects.get(email=email)
            if user.is_verified:
                self.send_password_reset_email(request, user)
                return Response({"message": "Reset password link sent to your email."}, status=status.HTTP_200_OK)
            else:
                return Response({"error": "User is not verified."}, status=status.HTTP_400_BAD_REQUEST)
        except User.DoesNotExist:
            return Response({"error": "User not found."}, status=status.HTTP_404_NOT_FOUND)
    
    """reset password"""
    @action(detail=False, methods=['post'], permission_classes=[AllowAny])
    def reset_password(self, request):
        uid= request.data.get('uid')
        token = request.data.get('token')
        new_password= request.data.get('new_password')

        try:
            uid= urlsafe_base64_decode(uid).decode()
            user= User.objects.get(pk= uid)
            if default_token_generator.check_token(user, token):
                user.set_password(new_password)
                user.save()
                return Response({"message": "Password reset successfully."}, status=status.HTTP_200_OK)
            else:
                return Response({"error": "Invalid token."}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({"error": "Invalid user or token."}, status=status.HTTP_400_BAD_REQUEST)
    
    """functionto send forgot password email"""
    def send_password_reset_email(self, request, user):
        current_site = get_current_site(request)
        subject = 'Reset your password'
        template_name = 'password_reset_email.txt'

        context = {
            'user': user,
            'protocol': 'https' if request.is_secure() else 'http',
            'domain': current_site.domain,
            'uid': urlsafe_base64_encode(force_bytes(user.pk)),
            'token': RefreshToken.for_user(user).access_token,
        }

        self.send_email(request, user.email, subject, template_name, context)

    def send_email(self, request, to_email, subject, template_name, context):
        message = render_to_string(template_name, context)
        send_mail(subject, message, settings.EMAIL_HOST_USER, [to_email])
    
    """to exempt from csrf protection"""
    @method_decorator(csrf_exempt)
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)


"""Verify Email"""
@api_view(['GET'])
def verify_email(request, uid, token):
    try:
        uid = urlsafe_base64_decode(uid).decode()
        user = User.objects.get(pk=uid)
        if not user.is_verified:
            RefreshToken(token).blacklist()
            user.is_verified = True
            user.save()
            return Response({"message": "Email verified successfully."}, status=status.HTTP_200_OK)
        else:
            return Response({"error": "Email already verified."}, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        return Response({"error": "Invalid token or user not found."}, status=status.HTTP_400_BAD_REQUEST)


""" # Login User
class MyTokenObtainPairView(TokenObtainPairView):
    serializer_class = MyTokenObtainPairSerializer """
