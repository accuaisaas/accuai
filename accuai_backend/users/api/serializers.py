from rest_framework import serializers
from accuai_backend.users.models import User


class UserSerializer(serializers.ModelSerializer):

    class Meta:
        model = User
        fields = ["id", "email", "name", "password"]

    def create(self, validated_data):
        user = User.objects.create(
            email=validated_data['email'],
            name=validated_data['name'],
            is_verified=False
            )
        user.set_password(validated_data['password'])
        user.save()
        return user