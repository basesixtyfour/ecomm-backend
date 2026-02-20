from rest_framework import viewsets
from .models import Product
from .serializers import ProductSerializer
from .filters import ProductFilter
from django_filters.rest_framework import DjangoFilterBackend
from .filters import CustomOrderingFilter
from rest_framework.filters import SearchFilter

class ProductViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Product.objects.prefetch_related('categories').distinct()
    serializer_class = ProductSerializer
    filterset_class = ProductFilter
    filter_backends = [
        DjangoFilterBackend,
        SearchFilter,
        CustomOrderingFilter,
    ]
    search_fields = ['name', 'description', 'categories__name']
    ordering_fields = ['price']
