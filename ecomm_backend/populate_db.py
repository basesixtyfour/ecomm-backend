#!/usr/bin/env python3
"""
Populate the database with consistent test data.

Usage:
    python populate_db.py
    python populate_db.py --users 15 --products 40 --orders-per-user 4
"""

import argparse
import os
import random
from decimal import Decimal
from io import BytesIO

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "ecomm_backend.settings")

import django  # noqa: E402

django.setup()

from django.contrib.auth.models import User  # noqa: E402
from django.core.files.base import ContentFile  # noqa: E402
from django.db import transaction  # noqa: E402

from cart.models import Cart, CartItem  # noqa: E402
from orders.models import Order, OrderItem  # noqa: E402
from products.models import Category, Product  # noqa: E402
from users.models import UserProfile  # noqa: E402


SEED_USERNAME_PREFIX = "seed_user_"
SEED_PRODUCT_PREFIX = "Seed Product "
SEED_CATEGORY_PREFIX = "Seed Category "
DEFAULT_PASSWORD = "SeedPass@123"


def create_dummy_image_bytes() -> bytes:
    # 1x1 transparent PNG.
    return (
        b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01"
        b"\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15\xc4\x89"
        b"\x00\x00\x00\x0cIDATx\x9cc```\x00\x00\x00\x04\x00\x01"
        b"\x0b\xe7\x02\x9d\x00\x00\x00\x00IEND\xaeB`\x82"
    )


def decimal_price(base: int) -> Decimal:
    return Decimal(str(base)).quantize(Decimal("0.01"))


@transaction.atomic
def populate_db(
    users_count: int,
    categories_count: int,
    products_count: int,
    orders_per_user: int,
    max_cart_items: int,
    random_seed: int,
) -> None:
    rng = random.Random(random_seed)
    dummy_image = create_dummy_image_bytes()

    users = []
    for idx in range(1, users_count + 1):
        username = f"{SEED_USERNAME_PREFIX}{idx}"
        email = f"{username}@example.com"
        user, created = User.objects.get_or_create(
            username=username,
            defaults={"email": email},
        )
        if not created and user.email != email:
            user.email = email
            user.save(update_fields=["email"])
        user.set_password(DEFAULT_PASSWORD)
        user.save(update_fields=["password"])
        UserProfile.objects.get_or_create(user=user)
        users.append(user)

    categories = []
    for idx in range(1, categories_count + 1):
        name = f"{SEED_CATEGORY_PREFIX}{idx}"
        category, _ = Category.objects.get_or_create(name=name)
        categories.append(category)

    products = []
    for idx in range(1, products_count + 1):
        name = f"{SEED_PRODUCT_PREFIX}{idx}"
        defaults = {
            "description": f"Auto-generated description for {name}",
            "price": decimal_price(99 + idx),
        }
        product, _ = Product.objects.get_or_create(name=name, defaults=defaults)

        product.description = defaults["description"]
        product.price = defaults["price"]
        if not product.image:
            image_name = f"products/seed_product_{idx}.png"
            product.image.save(image_name, ContentFile(dummy_image), save=False)
        product.save()

        assigned_count = rng.randint(1, min(3, len(categories)))
        product.categories.set(rng.sample(categories, k=assigned_count))
        products.append(product)

    seed_users_qs = User.objects.filter(username__startswith=SEED_USERNAME_PREFIX)
    seed_carts_qs = Cart.objects.filter(user__in=seed_users_qs)
    CartItem.objects.filter(cart__in=seed_carts_qs).delete()
    OrderItem.objects.filter(order__user__in=seed_users_qs).delete()
    Order.objects.filter(user__in=seed_users_qs).delete()

    cart_items_created = 0
    orders_created = 0
    order_items_created = 0

    for user in users:
        cart, _ = Cart.objects.get_or_create(user=user)
        cart_item_count = rng.randint(1, max_cart_items)
        cart_products = rng.sample(products, k=min(cart_item_count, len(products)))
        for product in cart_products:
            qty = rng.randint(1, 4)
            CartItem.objects.create(cart=cart, product=product, quantity=qty)
            cart_items_created += 1

        for _ in range(orders_per_user):
            order_item_count = rng.randint(1, 4)
            ordered_products = rng.sample(products, k=min(order_item_count, len(products)))
            line_items = []
            total = Decimal("0.00")
            for product in ordered_products:
                qty = rng.randint(1, 3)
                line_price = product.price * qty
                total += line_price
                line_items.append((product, qty, line_price))

            order = Order.objects.create(user=user, total_price=total.quantize(Decimal("0.01")))
            orders_created += 1
            for product, qty, line_price in line_items:
                OrderItem.objects.create(
                    order=order,
                    product=product,
                    quantity=qty,
                    price=line_price.quantize(Decimal("0.01")),
                )
                order_items_created += 1

    print("Database seeding complete.")
    print(f"Users seeded: {len(users)} (prefix: {SEED_USERNAME_PREFIX})")
    print(f"Categories seeded: {len(categories)} (prefix: {SEED_CATEGORY_PREFIX})")
    print(f"Products seeded: {len(products)} (prefix: {SEED_PRODUCT_PREFIX})")
    print(f"Cart items created: {cart_items_created}")
    print(f"Orders created: {orders_created}")
    print(f"Order items created: {order_items_created}")
    print(f"Seed users password: {DEFAULT_PASSWORD}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Populate test data for ecomm backend.")
    parser.add_argument("--users", type=int, default=10, help="Number of seed users.")
    parser.add_argument("--categories", type=int, default=8, help="Number of seed categories.")
    parser.add_argument("--products", type=int, default=30, help="Number of seed products.")
    parser.add_argument(
        "--orders-per-user",
        type=int,
        default=3,
        help="Number of orders to create per seed user.",
    )
    parser.add_argument(
        "--max-cart-items",
        type=int,
        default=5,
        help="Maximum number of unique products in each cart.",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Random seed for repeatable generated data.",
    )
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()

    if min(
        args.users,
        args.categories,
        args.products,
        args.orders_per_user,
        args.max_cart_items,
    ) < 1:
        raise ValueError("All numeric arguments must be >= 1.")

    populate_db(
        users_count=args.users,
        categories_count=args.categories,
        products_count=args.products,
        orders_per_user=args.orders_per_user,
        max_cart_items=args.max_cart_items,
        random_seed=args.seed,
    )
