from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.mixins import ListModelMixin, RetrieveModelMixin, UpdateModelMixin
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet

from product.models import ProductModel

from .serializer import ProductDataSerializer

# Create your views here.


class ProductViewSet(RetrieveModelMixin, ListModelMixin, UpdateModelMixin, GenericViewSet):
    permission_classes = [AllowAny]

    @api_view(["GET"])
    def getData(request):
        queryset = ProductModel.objects.all()
        serializer = ProductDataSerializer(queryset, many=True)
        return Response(status=status.HTTP_200_OK, data=serializer.data)

    def get_queryset(self):
        # Override get_queryset to provide dynamic control over the queryset
        return ProductModel.objects.all()

    def get_serializer_class(self):
        # Override get_serializer_class to provide dynamic control over the serializer class
        return ProductDataSerializer
