from rest_framework import serializers

from product.models import ProductModel


class ProductDataSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductModel
        fields = ("name", "description")
