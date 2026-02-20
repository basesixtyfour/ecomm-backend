from django.db.models import Prefetch, prefetch_related_objects
from rest_framework import status
from rest_framework.generics import GenericAPIView, get_object_or_404
from rest_framework.mixins import CreateModelMixin, RetrieveModelMixin, DestroyModelMixin
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .models import Cart, CartItem
from .serializers import CartSerializer, CartItemSerializer

_CART_ITEMS_PREFETCH = Prefetch(
    'items',
    queryset=CartItem.objects.select_related('product').prefetch_related('product__categories'),
)


def _prefetch_and_serialize(cart):
    """Attach prefetched items/products/categories to an already-loaded Cart, then serialize."""
    prefetch_related_objects([cart], _CART_ITEMS_PREFETCH)
    return CartSerializer(cart).data


class CartView(RetrieveModelMixin, GenericAPIView):
    """
    GET    /cart/  → return the authenticated user's cart
    DELETE /cart/  → remove all items and return the empty cart
    """
    serializer_class = CartSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        cart, _ = Cart.objects.get_or_create(user=self.request.user)
        prefetch_related_objects([cart], _CART_ITEMS_PREFETCH)
        return cart

    def get(self, request, *args, **kwargs):
        return self.retrieve(request, *args, **kwargs)

    def delete(self, request, *args, **kwargs):
        cart = self.get_object()
        cart.items.all().delete()
        prefetch_related_objects([cart], _CART_ITEMS_PREFETCH)
        return Response(CartSerializer(cart).data)


class CartItemView(CreateModelMixin,
                   DestroyModelMixin,
                   GenericAPIView):
    """
    POST   /cart/items/              → add item to cart
    PATCH  /cart/items/{item_id}/    → update item quantity
    DELETE /cart/items/{item_id}/    → remove item from cart

    All mutations return the full serialized Cart so the client
    can update in one round-trip instead of re-fetching.
    """
    serializer_class = CartItemSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return CartItem.objects.select_related('cart').filter(cart__user=self.request.user)

    def get_object(self):
        return get_object_or_404(self.get_queryset(), pk=self.kwargs['item_id'])

    def perform_create(self, serializer):
        cart, _ = Cart.objects.get_or_create(user=self.request.user)
        serializer.save(cart=cart)

    def post(self, request, *args, **kwargs):
        if 'product_id' not in request.data:
            return Response(
                {'product_id': ['This field is required.']},
                status=status.HTTP_400_BAD_REQUEST,
            )
        self.create(request, *args, **kwargs)
        cart, _ = Cart.objects.get_or_create(user=request.user)
        return Response(_prefetch_and_serialize(cart), status=status.HTTP_201_CREATED)

    def patch(self, request, *args, **kwargs):
        item = self.get_object()
        serializer = self.get_serializer(item, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(_prefetch_and_serialize(item.cart))

    def delete(self, request, *args, **kwargs):
        item = self.get_object()
        cart = item.cart
        item.delete()
        return Response(_prefetch_and_serialize(cart))
