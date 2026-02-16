import django_filters
from rest_framework.filters import OrderingFilter
from .models import Product

class ProductFilter(django_filters.FilterSet):
    categories = django_filters.CharFilter(method='filter_categories')

    class Meta:
        model = Product
        fields = []

    def filter_categories(self, queryset, _, value):
        values = value.split(',')
        query = queryset
        for val in values:
            query = query.filter(categories__name__icontains=val)
        return query

class CustomOrderingFilter(OrderingFilter):
    ordering_param = 'sort'