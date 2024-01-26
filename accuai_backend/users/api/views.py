import logging

from django.contrib.auth import get_user_model
from django.contrib.auth.tokens import default_token_generator
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import redirect
from django.http import HttpResponseServerError
from rest_framework import status
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.mixins import CreateModelMixin
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.viewsets import GenericViewSet
from rest_framework_simplejwt.tokens import RefreshToken
from django.template.loader import render_to_string
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes
from django.contrib.sites.shortcuts import get_current_site
from django.core.mail import send_mail
from django.conf import settings
from dotenv import load_dotenv
import os

from .serializers import UserSerializer
from users.constants.constants import (
    USER_REGISTER_SUCCESS_MESSAGE, 
    VERIFICATION_EMAIL_MESSAGE,
    EMAIL_ALREADY_VERIFIED,
    VERIFICATION_EMAIL_ERROR_MESSAGE,
    VERIFICATION_EMAIL_SUBJECT,
    VERIFICATION_EMAIL_TEMPLATE,
    PASSWORD_RESET_SUCCESS_MESSAGE,
    INVALID_TOKEN_ERROR_MESSAGE,
    PASSWORD_RESET_MAIL_SENT,
    USER_NOT_FOUND,
    EMAIL_NOT_VERIFIED,
    INVALID_USER_OR_TOKEN,
    PASSWORD_RESET_SUBJECT,
    PASSWORD_RESET_TEMPLATE,
    INTERNAL_SERVER_ERROR,
    EMAIL_VERIFICATION_ERROR
)

    
######## Custom View ###########

User = get_user_model()

class RegisterViewSet(GenericViewSet, CreateModelMixin):

    queryset= User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [AllowAny]
    load_dotenv()

    """Register a User"""
    @action(detail=False, methods=['post'], permission_classes=[AllowAny])
    def register(self, request):
        serializer= UserSerializer(data= request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()

        # Send verification email
        self.send_verification_email(request, user)
        return Response({"message": USER_REGISTER_SUCCESS_MESSAGE}, status=status.HTTP_201_CREATED)
    
    """Resend verification email"""
    @action(detail=False, methods=['post'], permission_classes=[AllowAny])
    def resend_verification_email(self, request):
        email = request.data.get('email')

        if email:
            # Assume user is fetched using your User model, adjust this accordingly
            user = User.objects.get(email=email)

            if not user.is_verified:
                # Send verification email
                self.send_verification_email(request, user)
                return Response({"message": VERIFICATION_EMAIL_MESSAGE}, status=status.HTTP_200_OK)
            else:
                return Response({"error": EMAIL_ALREADY_VERIFIED}, status=status.HTTP_400_BAD_REQUEST)
        else:
            return Response({"error": VERIFICATION_EMAIL_ERROR_MESSAGE}, status=status.HTTP_400_BAD_REQUEST)

    """Send verification email"""    
    def send_verification_email(self, request, user):
        current_site = get_current_site(request)
        subject = VERIFICATION_EMAIL_SUBJECT
        template_name = VERIFICATION_EMAIL_TEMPLATE
        context = {
            'user': user,
            'protocol': 'https' if request.is_secure() else 'http',
            'domain': current_site.domain,
            'uid': urlsafe_base64_encode(force_bytes(user.pk)),
            'token': RefreshToken.for_user(user),
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
                return Response({"message": PASSWORD_RESET_MAIL_SENT}, status=status.HTTP_200_OK)
            else:
                return Response({"error": EMAIL_NOT_VERIFIED}, status=status.HTTP_400_BAD_REQUEST)
        except User.DoesNotExist:
            return Response({"error": USER_NOT_FOUND}, status=status.HTTP_404_NOT_FOUND)
    
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
                return Response({"message": PASSWORD_RESET_SUCCESS_MESSAGE}, status=status.HTTP_200_OK)
            else:
                return Response({"error": INVALID_TOKEN_ERROR_MESSAGE}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({"error": INVALID_USER_OR_TOKEN}, status=status.HTTP_400_BAD_REQUEST)
    
    """functionto send forgot password email"""
    def send_password_reset_email(self, request, user):
        current_site = get_current_site(request)
        subject = PASSWORD_RESET_SUBJECT
        template_name = PASSWORD_RESET_TEMPLATE

        context = {
            'user': user,
            'protocol': 'https' if request.is_secure() else 'http',
            'frontend_reset_url': os.getenv("FRONTEND_RESET_URL"),
            'uid': urlsafe_base64_encode(force_bytes(user.pk)),
            'token': default_token_generator.make_token(user),
        }

        self.send_email(request, user.email, subject, template_name, context)

    def send_email(self, request, to_email, subject, template_name, context):
        message = render_to_string(template_name, context)
        send_mail(subject, message, settings.EMAIL_HOST_USER, [to_email], fail_silently=False)
    
    """to exempt from csrf protection"""
    @method_decorator(csrf_exempt)
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)


@api_view(['GET'])
@permission_classes([AllowAny])
def verify_email(request, uid, token):
    try:
        uid = urlsafe_base64_decode(uid).decode()
        user = User.objects.get(pk=uid)

        if not user.is_verified:
            try:
                RefreshToken(token).blacklist()
            except Exception as blacklist_error:
                print("Error during token blacklisting:", blacklist_error)

            user.is_verified = True
            user.save()

            # Redirect to frontend
            frontend_login_url = os.getenv("FRONTEND_LOGIN_URL")
            return redirect(frontend_login_url)
        else:
            return Response({"error": EMAIL_ALREADY_VERIFIED}, status=status.HTTP_400_BAD_REQUEST)
    except User.DoesNotExist:
        return Response({"error": USER_NOT_FOUND}, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        print(EMAIL_VERIFICATION_ERROR, e)
        return HttpResponseServerError(INTERNAL_SERVER_ERROR)
