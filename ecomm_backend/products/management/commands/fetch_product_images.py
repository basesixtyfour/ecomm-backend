import os
import hashlib

import httpx
from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand

from products.models import Product

PEXELS_SEARCH_URL = "https://api.pexels.com/v1/search"
PICSUM_URL = "https://picsum.photos/800/800"


class Command(BaseCommand):
    help = "Fetch product images from Pexels (or Lorem Picsum fallback) and attach them to products."

    def add_arguments(self, parser):
        parser.add_argument(
            "--overwrite",
            action="store_true",
            help="Re-download images even for products that already have one.",
        )
        parser.add_argument(
            "--limit",
            type=int,
            default=0,
            help="Only process N products (0 = all).",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Do not save anything; just print what would happen.",
        )
        parser.add_argument(
            "--pexels-key",
            type=str,
            default=None,
            help="Pexels API key (overrides PEXELS_API_KEY env var).",
        )

    def handle(self, *args, **options):
        pexels_key = options["pexels_key"] or os.environ.get("PEXELS_API_KEY", "")
        overwrite = options["overwrite"]
        limit = int(options["limit"] or 0)
        dry_run = bool(options["dry_run"])

        products = Product.objects.prefetch_related("categories").all()
        if limit > 0:
            products = products[:limit]
        if not products.exists():
            self.stderr.write(self.style.WARNING("No products in the database."))
            return

        use_pexels = bool(pexels_key)
        source = "Pexels" if use_pexels else "Lorem Picsum (no PEXELS_API_KEY set)"
        self.stdout.write(f"Image source: {source}")
        self.stdout.write(f"Products to process: {products.count()}")

        with httpx.Client(timeout=30, follow_redirects=True) as client:
            for product in products:
                if product.image and product.image.name and not overwrite:
                    self.stdout.write(f"  SKIP  {product.name} (already has image)")
                    continue

                if use_pexels:
                    image_bytes, ext = self._fetch_pexels(client, pexels_key, product)
                else:
                    image_bytes, ext = self._fetch_picsum(client, product)

                if image_bytes is None:
                    self.stderr.write(self.style.ERROR(f"  FAIL  {product.name}"))
                    continue

                slug = self._slugify(product.name)
                filename = f"{slug}.{ext}"
                if dry_run:
                    self.stdout.write(self.style.SUCCESS(f"  DRY   {product.name} -> products/{filename}"))
                else:
                    product.image.save(filename, ContentFile(image_bytes), save=True)
                    self.stdout.write(self.style.SUCCESS(f"  OK    {product.name} -> {product.image.name}"))

        self.stdout.write(self.style.SUCCESS("Done."))

    # ------------------------------------------------------------------
    # Pexels
    # ------------------------------------------------------------------
    def _fetch_pexels(self, client: httpx.Client, api_key: str, product: Product):
        query = self._build_search_query(product)
        self.stdout.write(f"  Pexels search: \"{query}\"")

        try:
            resp = client.get(
                PEXELS_SEARCH_URL,
                params={"query": query, "per_page": 1, "orientation": "square"},
                headers={"Authorization": api_key},
            )
            resp.raise_for_status()
            data = resp.json()

            photos = data.get("photos", [])
            if not photos:
                self.stderr.write(self.style.WARNING(f"  No Pexels results for \"{query}\", falling back to Picsum"))
                return self._fetch_picsum(client, product)

            src = photos[0].get("src") or {}
            image_url = src.get("large2x") or src.get("large") or src.get("medium") or src.get("original")
            if not image_url:
                self.stderr.write(self.style.WARNING(f"  Pexels result missing image URL, falling back to Picsum"))
                return self._fetch_picsum(client, product)
            return self._download(client, image_url)
        except httpx.HTTPError as exc:
            self.stderr.write(self.style.ERROR(f"  Pexels error: {exc}"))
            return None, None

    # ------------------------------------------------------------------
    # Lorem Picsum fallback
    # ------------------------------------------------------------------
    def _fetch_picsum(self, client: httpx.Client, product: Product):
        seed = hashlib.md5(str(product.id).encode()).hexdigest()[:8]
        url = f"https://picsum.photos/seed/{seed}/800/800"
        self.stdout.write(f"  Picsum fallback (seed={seed})")
        return self._download(client, url)

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    def _download(self, client: httpx.Client, url: str):
        try:
            resp = client.get(url)
            resp.raise_for_status()

            content_type = resp.headers.get("content-type", "")
            if "png" in content_type:
                ext = "png"
            elif "webp" in content_type:
                ext = "webp"
            else:
                ext = "jpg"

            return resp.content, ext
        except httpx.HTTPError as exc:
            self.stderr.write(self.style.ERROR(f"  Download error: {exc}"))
            return None, None

    @staticmethod
    def _build_search_query(product: Product) -> str:
        categories = list(product.categories.values_list("name", flat=True))
        parts = [product.name]
        parts.extend(categories[:2])
        return " ".join([p for p in parts if p])

    @staticmethod
    def _slugify(name: str) -> str:
        return (
            name.lower()
            .replace(" ", "-")
            .replace("'", "")
            .replace('"', "")
            .replace("/", "-")
            .replace("\\", "-")
        )[:80]
