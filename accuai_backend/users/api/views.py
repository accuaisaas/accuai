import logging

from django.contrib.auth import get_user_model, login
from django.urls import reverse
from rest_framework import status
from rest_framework.decorators import action, api_view
from rest_framework.mixins import ListModelMixin, RetrieveModelMixin, UpdateModelMixin
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.viewsets import GenericViewSet, ModelViewSet
from rest_framework_simplejwt.tokens import RefreshToken

from .serializers import LoginSerializer, UserSerializer

log = logging.getLogger(__name__)

User = get_user_model()


def get_tokens_for_user(user):
    refresh = RefreshToken.for_user(user)

    return {
        "access": str(refresh.access_token),
        "refresh": str(refresh),
    }


class UserViewSet(RetrieveModelMixin, ListModelMixin, UpdateModelMixin, GenericViewSet):
    serializer_class = UserSerializer
    queryset = User.objects.all()
    lookup_field = "pk"

    def get_queryset(self, *args, **kwargs):
        assert isinstance(self.request.user.id, int)
        return self.queryset.filter(id=self.request.user.id)

    @action(detail=False)
    def me(self, request):
        serializer = UserSerializer(request.user, context={"request": request})
        return Response(status=status.HTTP_200_OK, data=serializer.data)


class LoginApiViewSet(GenericViewSet, APIView):
    permission_classes = (AllowAny,)
    #User Login
    serializer_class = LoginSerializer
    redirect_url = None

    def get_success_url(self):
        #success url
        redirect_url = self.request.data.get("next", "")
        redirect_url = redirect_url
        if not redirect_url:
            return reverse("homepage")
        return redirect_url

    @api_view(["POST"])
    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        #   get the user
        user = serializer.get_user()
        login(request, user)

        if user is None or not user:
            return Response({"detail": "Invalid email or password."}, status=status.HTTP_404_NOT_FOUND)

        # set status to online
        # SET THE STATUS TO ONLINE
        return Response({"url": self.get_success_url()}, status=status.HTTP_200_OK)


class HelloWorldView(ModelViewSet):
    permission_classes = [AllowAny]

    @api_view(["GET"])
    def get(self, request):
        return Response({"message": "Hello, World!"}, status=status.HTTP_200_OK)
