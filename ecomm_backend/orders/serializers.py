from rest_framework import serializers
from .models import Order, OrderItem


class OrderItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderItem
        fields = ['id', 'product', 'quantity', 'price']
        read_only_fields = ['price']


class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(source='orderitem_set', many=True)

    class Meta:
        model = Order
        fields = ['id', 'user', 'total_price', 'items', 'created_at', 'updated_at']
        read_only_fields = ['id', 'user', 'total_price', 'created_at', 'updated_at']

    def create(self, validated_data):
        items_data = validated_data.pop('orderitem_set')

        total_price = sum(
            item['product'].price * item['quantity'] for item in items_data
        )

        order = Order.objects.create(
            user=self.context['request'].user,
            total_price=total_price,
        )

        OrderItem.objects.bulk_create([
            OrderItem(
                order=order,
                product=item['product'],
                quantity=item['quantity'],
                price=item['product'].price,
            )
            for item in items_data
        ])

        return order
