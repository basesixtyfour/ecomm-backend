from rest_framework import serializers
from products.serializers import ProductSerializer
from products.models import Product
from .models import Cart, CartItem

class CartItemSerializer(serializers.ModelSerializer):
    product = ProductSerializer(read_only=True)
    product_id = serializers.PrimaryKeyRelatedField(
        queryset=Product.objects.all(),
        source='product',
        write_only=True,
        required=False,
    )

    class Meta:
        model = CartItem
        fields = ['id', 'product', 'product_id', 'quantity', 'subtotal']
        read_only_fields = ['subtotal']

class CartSerializer(serializers.ModelSerializer):
    items = CartItemSerializer(many=True)
    class Meta:
        model = Cart
        fields = ['id', 'user', 'items', 'total_price']
        read_only_fields = ['user', 'total_price']