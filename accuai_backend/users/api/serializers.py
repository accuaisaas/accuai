from django.contrib.auth import authenticate, get_user_model
from rest_framework import serializers

from accuai_backend.users.models import User as UserType

User = get_user_model()


class UserSerializer(serializers.ModelSerializer[UserType]):
    class Meta:
        model = User
        fields = ["name", "url"]

        extra_kwargs = {
            "url": {"view_name": "api:user-detail", "lookup_field": "pk"},
        }


class LoginSerializer(serializers.Serializer):
    #Validates login of a Use

    email = serializers.EmailField(allow_blank=False, required=True)
    password = serializers.CharField(allow_blank=False, required=True)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.authed_user = None

    def get_user(self):
        return self.authed_user

    def validate(self, attrs):
        try:
            email = attrs["email"].strip()
            password = attrs["password"]
            try:
                self.authed_user = authenticate(email=email, password=password)
            except ValueError:
                self.authed_user = None

            if self.authed_user:
                return attrs
        except (UserType.DoesNotExist, KeyError):
            pass
        raise serializers.ValidationError("Your login details were incorrect. Please try again.")
