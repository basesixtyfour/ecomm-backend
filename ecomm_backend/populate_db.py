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

from django.contrib.auth import get_user_model  # noqa: E402
from django.core.files.base import ContentFile  # noqa: E402
from django.db import transaction  # noqa: E402

from cart.models import Cart, CartItem  # noqa: E402
from orders.models import Order, OrderItem  # noqa: E402
from products.models import Category, Product  # noqa: E402
from users.models import UserProfile  # noqa: E402

User = get_user_model()


SEED_USERNAME_PREFIX = "seed_user_"
DEFAULT_PASSWORD = "SeedPass@123"

# Real-world categories
CATEGORIES = [
    "Electronics",
    "Clothing & Fashion",
    "Home & Kitchen",
    "Books & Stationery",
    "Sports & Outdoors",
    "Beauty & Personal Care",
    "Toys & Games",
    "Automotive",
]

# Real-world products with realistic names, descriptions, and price ranges
PRODUCTS = [
    # Electronics
    {
        "name": "Sony WH-1000XM5 Wireless Headphones",
        "description": "Industry-leading noise canceling with premium sound quality. 30-hour battery life, lightweight design, and multipoint connection.",
        "price": 399.99,
        "categories": ["Electronics"],
    },
    {
        "name": "Samsung Galaxy Tab S9 Tablet",
        "description": "11-inch AMOLED display, Snapdragon 8 Gen 2 processor, S Pen included. Perfect for work and entertainment.",
        "price": 799.99,
        "categories": ["Electronics"],
    },
    {
        "name": "Logitech MX Master 3S Wireless Mouse",
        "description": "Advanced ergonomic wireless mouse with ultra-fast scrolling and customizable buttons. Compatible with multiple devices.",
        "price": 99.99,
        "categories": ["Electronics"],
    },
    {
        "name": "Apple AirPods Pro (2nd Generation)",
        "description": "Active noise cancellation, adaptive audio, and personalized spatial audio. USB-C charging case included.",
        "price": 249.99,
        "categories": ["Electronics"],
    },
    {
        "name": "Anker PowerCore 26800mAh Power Bank",
        "description": "Ultra-high capacity portable charger with 3 USB ports. Fast charging technology for smartphones and tablets.",
        "price": 59.99,
        "categories": ["Electronics"],
    },
    # Clothing & Fashion
    {
        "name": "Levi's 501 Original Fit Jeans",
        "description": "Classic straight leg jeans with button fly. Made from premium denim with authentic details.",
        "price": 89.99,
        "categories": ["Clothing & Fashion"],
    },
    {
        "name": "Nike Air Max 270 Running Shoes",
        "description": "Lightweight cushioning and breathable mesh upper. Max Air unit for ultimate comfort.",
        "price": 159.99,
        "categories": ["Clothing & Fashion", "Sports & Outdoors"],
    },
    {
        "name": "Patagonia Better Sweater Fleece Jacket",
        "description": "Warm, lightweight fleece jacket made from recycled polyester. Full-zip design with multiple pockets.",
        "price": 139.99,
        "categories": ["Clothing & Fashion", "Sports & Outdoors"],
    },
    {
        "name": "Ray-Ban Aviator Classic Sunglasses",
        "description": "Iconic teardrop shape with crystal lenses and metal frame. 100% UV protection.",
        "price": 179.99,
        "categories": ["Clothing & Fashion"],
    },
    {
        "name": "Carhartt Canvas Work Jacket",
        "description": "Durable cotton canvas jacket with quilted lining. Multiple tool pockets and adjustable cuffs.",
        "price": 119.99,
        "categories": ["Clothing & Fashion"],
    },
    # Home & Kitchen
    {
        "name": "Ninja Air Fryer Max XL",
        "description": "5.5-quart capacity air fryer with 7 cooking functions. Crisps, roasts, and dehydrates with little to no oil.",
        "price": 149.99,
        "categories": ["Home & Kitchen"],
    },
    {
        "name": "Keurig K-Elite Coffee Maker",
        "description": "Single serve coffee maker with iced coffee capability. Large 75oz water reservoir and strong brew option.",
        "price": 169.99,
        "categories": ["Home & Kitchen"],
    },
    {
        "name": "Instant Pot Duo 7-in-1 Electric Pressure Cooker",
        "description": "Multi-functional 6-quart cooker: pressure cook, slow cook, rice cooker, steamer, sauté, yogurt maker, and warmer.",
        "price": 99.99,
        "categories": ["Home & Kitchen"],
    },
    {
        "name": "Dyson V11 Cordless Vacuum Cleaner",
        "description": "Powerful suction with intelligent cleaning modes. Up to 60 minutes runtime and advanced filtration.",
        "price": 599.99,
        "categories": ["Home & Kitchen"],
    },
    {
        "name": "Lodge Cast Iron Skillet 12-Inch",
        "description": "Pre-seasoned cast iron pan for superior heat retention. Oven safe and compatible with all cooktops.",
        "price": 39.99,
        "categories": ["Home & Kitchen"],
    },
    # Books & Stationery
    {
        "name": "Moleskine Classic Notebook Large",
        "description": "Hard cover ruled notebook with elastic closure. Ivory paper, ribbon bookmark, and expandable inner pocket.",
        "price": 24.99,
        "categories": ["Books & Stationery"],
    },
    {
        "name": "Pilot G2 Gel Pens 12-Pack",
        "description": "Smooth writing gel ink pens with comfortable grip. Refillable and available in multiple colors.",
        "price": 14.99,
        "categories": ["Books & Stationery"],
    },
    {
        "name": "Wacom Intuos Graphics Tablet",
        "description": "Digital drawing tablet with pressure-sensitive pen. Includes creative software bundle.",
        "price": 79.99,
        "categories": ["Books & Stationery", "Electronics"],
    },
    {
        "name": "Oxford Spiral Notebooks 5-Pack",
        "description": "College ruled spiral notebooks with perforated pages. Durable covers and pocket dividers.",
        "price": 19.99,
        "categories": ["Books & Stationery"],
    },
    {
        "name": "Staedtler Colored Pencil Set 36 Colors",
        "description": "Professional quality colored pencils with vibrant pigments. Break-resistant leads in reusable metal case.",
        "price": 34.99,
        "categories": ["Books & Stationery"],
    },
    # Sports & Outdoors
    {
        "name": "Hydro Flask Water Bottle 32oz",
        "description": "Stainless steel insulated bottle keeps drinks cold for 24 hours. BPA-free with wide mouth opening.",
        "price": 44.99,
        "categories": ["Sports & Outdoors"],
    },
    {
        "name": "Coleman Sundome Camping Tent 4-Person",
        "description": "Easy setup dome tent with weather-resistant design. Spacious interior with storage pockets.",
        "price": 89.99,
        "categories": ["Sports & Outdoors"],
    },
    {
        "name": "Fitbit Charge 6 Fitness Tracker",
        "description": "Advanced health tracking with heart rate, GPS, and sleep monitoring. 7-day battery life and water resistant.",
        "price": 159.99,
        "categories": ["Sports & Outdoors", "Electronics"],
    },
    {
        "name": "Wilson Evolution Basketball",
        "description": "Official size indoor basketball with microfiber composite leather. Superior grip and control.",
        "price": 64.99,
        "categories": ["Sports & Outdoors"],
    },
    {
        "name": "Black Diamond Trail Trekking Poles",
        "description": "Lightweight aluminum poles with adjustable height. FlickLock mechanism and carbide tips.",
        "price": 139.99,
        "categories": ["Sports & Outdoors"],
    },
    # Beauty & Personal Care
    {
        "name": "CeraVe Moisturizing Cream 16oz",
        "description": "Daily face and body moisturizer with hyaluronic acid and ceramides. Fragrance-free and non-comedogenic.",
        "price": 19.99,
        "categories": ["Beauty & Personal Care"],
    },
    {
        "name": "Philips Norelco Multigroom 7000",
        "description": "All-in-one trimmer with 23 pieces for face, hair, and body. Self-sharpening blades, waterproof design.",
        "price": 69.99,
        "categories": ["Beauty & Personal Care"],
    },
    {
        "name": "Revlon One-Step Hair Dryer and Volumizer",
        "description": "Hot air brush for salon-quality blowouts at home. Ionic technology reduces frizz and static.",
        "price": 59.99,
        "categories": ["Beauty & Personal Care"],
    },
    {
        "name": "Neutrogena Makeup Remover Wipes 25-Pack",
        "description": "Ultra-soft cleansing cloths that remove makeup and mascara. Alcohol-free and ophthalmologist tested.",
        "price": 8.99,
        "categories": ["Beauty & Personal Care"],
    },
    {
        "name": "Oral-B Pro 1000 Electric Toothbrush",
        "description": "Rechargeable toothbrush with pressure sensor and timer. Removes up to 300% more plaque.",
        "price": 49.99,
        "categories": ["Beauty & Personal Care"],
    },
    # Toys & Games
    {
        "name": "LEGO Creator Expert Roller Coaster",
        "description": "Advanced building set with 4,124 pieces. Features motorized chain lift and 3 minifigures.",
        "price": 379.99,
        "categories": ["Toys & Games"],
    },
    {
        "name": "Nintendo Switch OLED Console",
        "description": "Gaming console with vibrant 7-inch OLED screen. Enhanced audio and 64GB internal storage.",
        "price": 349.99,
        "categories": ["Toys & Games", "Electronics"],
    },
    {
        "name": "Monopoly Board Game Classic Edition",
        "description": "Traditional property trading game for 2-6 players. Includes tokens, money, and property cards.",
        "price": 24.99,
        "categories": ["Toys & Games"],
    },
    {
        "name": "Rubik's Cube 3x3 Original Puzzle",
        "description": "Classic combination puzzle with 43 quintillion possible moves. Smooth turning action.",
        "price": 14.99,
        "categories": ["Toys & Games"],
    },
    {
        "name": "Nerf Elite 2.0 Blaster with Darts",
        "description": "High-performance foam dart blaster with 20-dart capacity. Includes 24 official Nerf darts.",
        "price": 29.99,
        "categories": ["Toys & Games"],
    },
    # Automotive
    {
        "name": "Bosch ICON Windshield Wiper Blades",
        "description": "Premium beam blade design with exclusive fx dual rubber. All-weather performance and easy installation.",
        "price": 44.99,
        "categories": ["Automotive"],
    },
    {
        "name": "Armor All Car Vacuum Cleaner",
        "description": "Portable 12V wet/dry vacuum with 16-foot power cord. Multiple attachments for interior detailing.",
        "price": 39.99,
        "categories": ["Automotive"],
    },
    {
        "name": "Michelin Tire Pressure Gauge Digital",
        "description": "High-accuracy digital gauge with LCD display. Measures 5-150 PSI with automatic shutoff.",
        "price": 19.99,
        "categories": ["Automotive"],
    },
    {
        "name": "Chemical Guys Complete Car Care Kit",
        "description": "16-piece detailing kit with wash, wax, and interior cleaning products. Professional results at home.",
        "price": 129.99,
        "categories": ["Automotive"],
    },
    {
        "name": "Garmin DriveSmart 65 GPS Navigator",
        "description": "6.95-inch GPS with voice-activated navigation and live traffic updates. Bluetooth connectivity included.",
        "price": 249.99,
        "categories": ["Automotive", "Electronics"],
    },
]


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

    # Create categories from predefined list
    categories = []
    actual_categories = CATEGORIES[:categories_count]
    for category_name in actual_categories:
        category, _ = Category.objects.get_or_create(name=category_name)
        categories.append(category)

    # Create a mapping of category names to Category objects
    category_map = {cat.name: cat for cat in categories}

    # Create products from predefined list
    products = []
    actual_products = PRODUCTS[:products_count]
    for idx, product_data in enumerate(actual_products, start=1):
        name = product_data["name"]
        defaults = {
            "description": product_data["description"],
            "price": decimal_price(int(product_data["price"] * 100)) / 100,
        }
        product, _ = Product.objects.get_or_create(name=name, defaults=defaults)

        product.description = defaults["description"]
        product.price = defaults["price"]
        if not product.image:
            image_name = f"products/{name[:30].replace(' ', '_').lower()}_{idx}.png"
            product.image.save(image_name, ContentFile(dummy_image), save=False)
        product.save()

        # Assign categories based on product definition
        product_categories = [
            category_map[cat_name]
            for cat_name in product_data["categories"]
            if cat_name in category_map
        ]
        if product_categories:
            product.categories.set(product_categories)
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
    print(f"Categories seeded: {len(categories)}")
    print(f"Products seeded: {len(products)}")
    print(f"Cart items created: {cart_items_created}")
    print(f"Orders created: {orders_created}")
    print(f"Order items created: {order_items_created}")
    print(f"Seed users password: {DEFAULT_PASSWORD}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Populate test data for ecomm backend.")
    parser.add_argument("--users", type=int, default=10, help="Number of seed users.")
    parser.add_argument(
        "--categories",
        type=int,
        default=8,
        help=f"Number of seed categories (max: {len(CATEGORIES)}).",
    )
    parser.add_argument(
        "--products",
        type=int,
        default=30,
        help=f"Number of seed products (max: {len(PRODUCTS)}).",
    )
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

    if args.categories > len(CATEGORIES):
        raise ValueError(
            f"Requested {args.categories} categories but only {len(CATEGORIES)} are defined. "
            f"Use --categories {len(CATEGORIES)} or less."
        )

    if args.products > len(PRODUCTS):
        raise ValueError(
            f"Requested {args.products} products but only {len(PRODUCTS)} are defined. "
            f"Use --products {len(PRODUCTS)} or less."
        )

    populate_db(
        users_count=args.users,
        categories_count=args.categories,
        products_count=args.products,
        orders_per_user=args.orders_per_user,
        max_cart_items=args.max_cart_items,
        random_seed=args.seed,
    )
