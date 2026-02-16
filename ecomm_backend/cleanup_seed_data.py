#!/usr/bin/env python3
"""
Remove all seed data from the database.

This script removes:
- Seed users (starting with 'seed_user_')
- Seed products (starting with 'Seed Product')
- Seed categories (starting with 'Seed Category')
- All associated carts, orders, and related data

Usage:
    python cleanup_seed_data.py
    python cleanup_seed_data.py --confirm
"""

import argparse
import os
import sys

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "ecomm_backend.settings")

import django  # noqa: E402

django.setup()

from django.contrib.auth import get_user_model  # noqa: E402
from django.db import transaction  # noqa: E402

from cart.models import Cart, CartItem  # noqa: E402
from orders.models import Order, OrderItem  # noqa: E402
from products.models import Category, Product  # noqa: E402
from users.models import UserProfile  # noqa: E402

User = get_user_model()


SEED_USERNAME_PREFIX = "seed_user_"
SEED_PRODUCT_PREFIX = "Seed Product "
SEED_CATEGORY_PREFIX = "Seed Category "


def count_seed_data():
    """Count all seed data that will be deleted."""
    seed_users = User.objects.filter(username__startswith=SEED_USERNAME_PREFIX)
    seed_products = Product.objects.filter(name__startswith=SEED_PRODUCT_PREFIX)
    seed_categories = Category.objects.filter(name__startswith=SEED_CATEGORY_PREFIX)
    
    seed_carts = Cart.objects.filter(user__in=seed_users)
    cart_items = CartItem.objects.filter(cart__in=seed_carts)
    orders = Order.objects.filter(user__in=seed_users)
    order_items = OrderItem.objects.filter(order__in=orders)
    user_profiles = UserProfile.objects.filter(user__in=seed_users)
    
    return {
        "users": seed_users.count(),
        "products": seed_products.count(),
        "categories": seed_categories.count(),
        "carts": seed_carts.count(),
        "cart_items": cart_items.count(),
        "orders": orders.count(),
        "order_items": order_items.count(),
        "user_profiles": user_profiles.count(),
    }


@transaction.atomic
def cleanup_seed_data():
    """Remove all seed data from the database."""
    
    print("🔍 Scanning for seed data...")
    counts = count_seed_data()
    
    if sum(counts.values()) == 0:
        print("✅ No seed data found in the database.")
        return
    
    print("\n📊 Seed data found:")
    print(f"   Users: {counts['users']}")
    print(f"   User Profiles: {counts['user_profiles']}")
    print(f"   Products: {counts['products']}")
    print(f"   Categories: {counts['categories']}")
    print(f"   Carts: {counts['carts']}")
    print(f"   Cart Items: {counts['cart_items']}")
    print(f"   Orders: {counts['orders']}")
    print(f"   Order Items: {counts['order_items']}")
    
    # Get querysets
    seed_users = User.objects.filter(username__startswith=SEED_USERNAME_PREFIX)
    seed_products = Product.objects.filter(name__startswith=SEED_PRODUCT_PREFIX)
    seed_categories = Category.objects.filter(name__startswith=SEED_CATEGORY_PREFIX)
    
    print("\n🗑️  Deleting seed data...")
    
    # Delete in correct order to respect foreign key constraints
    
    # 1. Delete cart items (references cart and product)
    seed_carts = Cart.objects.filter(user__in=seed_users)
    deleted_cart_items = CartItem.objects.filter(cart__in=seed_carts).delete()[0]
    print(f"   ✓ Deleted {deleted_cart_items} cart items")
    
    # 2. Delete carts (references user)
    deleted_carts = seed_carts.delete()[0]
    print(f"   ✓ Deleted {deleted_carts} carts")
    
    # 3. Delete order items (references order and product)
    orders = Order.objects.filter(user__in=seed_users)
    deleted_order_items = OrderItem.objects.filter(order__in=orders).delete()[0]
    print(f"   ✓ Deleted {deleted_order_items} order items")
    
    # 4. Delete orders (references user)
    deleted_orders = orders.delete()[0]
    print(f"   ✓ Deleted {deleted_orders} orders")
    
    # 5. Delete user profiles (references user)
    deleted_profiles = UserProfile.objects.filter(user__in=seed_users).delete()[0]
    print(f"   ✓ Deleted {deleted_profiles} user profiles")
    
    # 6. Delete seed users
    deleted_users = seed_users.delete()[0]
    print(f"   ✓ Deleted {deleted_users} seed users")
    
    # 7. Delete seed products (may have category relationships)
    deleted_products = seed_products.delete()[0]
    print(f"   ✓ Deleted {deleted_products} seed products")
    
    # 8. Delete seed categories
    deleted_categories = seed_categories.delete()[0]
    print(f"   ✓ Deleted {deleted_categories} seed categories")
    
    print("\n✅ Seed data cleanup complete!")
    print("   All seed users, products, categories, and related data have been removed.")


def parse_args():
    parser = argparse.ArgumentParser(
        description="Remove all seed data from the database.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python cleanup_seed_data.py              # Interactive mode (asks for confirmation)
  python cleanup_seed_data.py --confirm    # Skip confirmation prompt
  python cleanup_seed_data.py --dry-run    # Show what would be deleted without deleting
        """
    )
    parser.add_argument(
        "--confirm",
        action="store_true",
        help="Skip confirmation prompt and delete immediately",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be deleted without actually deleting",
    )
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    
    if args.dry_run:
        print("🔍 DRY RUN MODE - No data will be deleted\n")
        counts = count_seed_data()
        
        if sum(counts.values()) == 0:
            print("✅ No seed data found in the database.")
        else:
            print("📊 Seed data that would be deleted:")
            print(f"   Users: {counts['users']}")
            print(f"   User Profiles: {counts['user_profiles']}")
            print(f"   Products: {counts['products']}")
            print(f"   Categories: {counts['categories']}")
            print(f"   Carts: {counts['carts']}")
            print(f"   Cart Items: {counts['cart_items']}")
            print(f"   Orders: {counts['orders']}")
            print(f"   Order Items: {counts['order_items']}")
            print("\nRun without --dry-run to actually delete this data.")
        sys.exit(0)
    
    # Check if there's any seed data to delete
    counts = count_seed_data()
    if sum(counts.values()) == 0:
        print("✅ No seed data found in the database.")
        sys.exit(0)
    
    # Interactive confirmation
    if not args.confirm:
        print("⚠️  WARNING: This will permanently delete all seed data from the database!")
        print(f"   - {counts['users']} seed users")
        print(f"   - {counts['products']} seed products")
        print(f"   - {counts['categories']} seed categories")
        print(f"   - {counts['orders']} orders")
        print(f"   - {counts['order_items']} order items")
        print(f"   - {counts['cart_items']} cart items")
        print(f"   - And related data")
        print("\nThis action cannot be undone.")
        
        response = input("\nDo you want to continue? (yes/no): ").strip().lower()
        if response not in ["yes", "y"]:
            print("❌ Cleanup cancelled.")
            sys.exit(0)
    
    cleanup_seed_data()
