from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from products.models import Brand, Category, Product, ProductImage


class Command(BaseCommand):
    help = "Create a small FurniNest demo catalog with local product photos."

    categories = (
        ("Living Room", "living-room"),
        ("Dining Room", "dining-room"),
        ("Bedroom", "bedroom"),
        ("Home Office", "home-office"),
        ("Prayer Room", "prayer-room"),
        ("Hallway", "hallway"),
        ("Outdoor", "outdoor"),
        ("Home Decor", "home-decor"),
    )
    products = (
        {
            "name": "Maison Upholstered Accent Chair",
            "slug": "maison-upholstered-accent-chair",
            "sku": "DEMO-MAISON-CHAIR",
            "category_slug": "living-room",
            "price": "28990.00",
            "discount_price": "24970.00",
            "stock_quantity": 8,
            "image": "products/demo/maison-accent-chair.jpg",
            "alt_text": "Olive upholstered accent chair with a wooden frame",
            "material": "Velvet and solid wood",
            "color": "Olive",
            "dimensions": "74 × 68 × 82 cm",
            "featured": True,
        },
        {
            "name": "Willow Counter Stool",
            "slug": "willow-counter-stool",
            "sku": "DEMO-WILLOW-STOOL",
            "category_slug": "dining-room",
            "price": "12490.00",
            "discount_price": "10990.00",
            "stock_quantity": 12,
            "image": "products/demo/willow-counter-stool.jpg",
            "alt_text": "Whitewashed wooden counter stool",
            "material": "Solid wood",
            "color": "White oak",
            "dimensions": "42 × 42 × 66 cm",
            "featured": True,
        },
        {
            "name": "Linea Velvet Sofa",
            "slug": "linea-velvet-sofa",
            "sku": "DEMO-LINEA-SOFA",
            "category_slug": "living-room",
            "price": "89500.00",
            "discount_price": None,
            "stock_quantity": 4,
            "image": "products/demo/linea-sofa.jpg",
            "alt_text": "Teal velvet sofa with tapered wooden legs",
            "material": "Velvet and solid wood",
            "color": "Deep teal",
            "dimensions": "198 × 86 × 78 cm",
            "featured": True,
        },
        {
            "name": "Sola Dining Table",
            "slug": "sola-dining-table",
            "sku": "DEMO-SOLA-DINING",
            "category_slug": "dining-room",
            "price": "45900.00",
            "discount_price": "42200.00",
            "stock_quantity": 5,
            "image": "products/demo/sola-dining-table.jpg",
            "alt_text": "Round white dining table with natural wood legs",
            "material": "Engineered wood and beech",
            "color": "Warm white",
            "dimensions": "110 cm diameter × 75 cm",
            "featured": True,
        },
        {
            "name": "Kinari Leather Sofa",
            "slug": "kinari-leather-sofa",
            "sku": "DEMO-KINARI-SOFA",
            "category_slug": "living-room",
            "price": "112000.00",
            "discount_price": None,
            "stock_quantity": 3,
            "image": "products/demo/kinari-leather-sofa.jpg",
            "alt_text": "Warm tan leather sofa",
            "material": "Leather and hardwood",
            "color": "Cognac",
            "dimensions": "210 × 92 × 80 cm",
            "featured": False,
        },
        {
            "name": "Nami Coffee Table",
            "slug": "nami-coffee-table",
            "sku": "DEMO-NAMI-TABLE",
            "category_slug": "living-room",
            "price": "18900.00",
            "discount_price": "16900.00",
            "stock_quantity": 9,
            "image": "products/demo/nami-living-room.jpg",
            "alt_text": "Low natural-wood coffee table in a calm living room",
            "material": "Solid ash",
            "color": "Natural",
            "dimensions": "90 × 60 × 38 cm",
            "featured": True,
        },
    )

    def handle(self, *args, **options):
        media_root = Path(settings.MEDIA_ROOT)
        demo_dir = media_root / "products" / "demo"
        demo_dir.mkdir(parents=True, exist_ok=True)
        fallback_source = demo_dir / "maison-accent-chair.jpg"

        department_images = {
            "living-room": "products/demo/linea-sofa.jpg",
            "dining-room": "products/demo/sola-dining-table.jpg",
            "bedroom": "products/demo/bedroom-bed.jpg",
            "home-office": "products/demo/office-desk.jpg",
            "hallway": "products/demo/hallway-console.jpg",
            "outdoor": "products/demo/outdoor-chair.jpg",
            "home-decor": "products/demo/decor-vase.jpg",
            "prayer-room": "products/demo/prayer-mat.jpg",
        }

        if fallback_source.is_file():
            import shutil
            for rel_path in department_images.values():
                target_path = media_root / rel_path
                if not target_path.is_file():
                    shutil.copy(fallback_source, target_path)

        missing_images = [
            item["image"]
            for item in self.products
            if not (media_root / item["image"]).is_file()
        ]
        if missing_images:
            raise CommandError(
                "Demo product photos are missing: " + ", ".join(missing_images)
            )

        categories = {}
        for name, slug in self.categories:
            category, _ = Category.objects.get_or_create(
                slug=slug,
                defaults={"name": name, "is_active": True},
            )
            categories[slug] = category
        brand, _ = Brand.objects.get_or_create(
            slug="furninest-studio",
            defaults={
                "name": "FurniNest Studio",
                "description": "A sample brand for the local demo catalog.",
                "is_active": True,
            },
        )

        created_products = 0
        for data in self.products:
            product, created = Product.objects.get_or_create(
                sku=data["sku"],
                defaults={
                    "category": categories[data["category_slug"]],
                    "brand": brand,
                    "name": data["name"],
                    "slug": data["slug"],
                    "description": (
                        f"{data['name']} brings thoughtful proportions and warm, "
                        "natural materials to a considered home."
                    ),
                    "price": data["price"],
                    "discount_price": data["discount_price"],
                    "stock_quantity": data["stock_quantity"],
                    "material": data["material"],
                    "color": data["color"],
                    "dimensions": data["dimensions"],
                    "is_featured": data["featured"],
                    "is_active": True,
                },
            )
            ProductImage.objects.get_or_create(
                product=product,
                sort_order=0,
                defaults={
                    "image": data["image"],
                    "alt_text": data["alt_text"],
                },
            )
            created_products += int(created)

        category_products = {
            "living-room": ["Serein Sofa", "Arden Lounge Chair", "Nami Side Table", "Cove Media Console", "Milo Ottoman", "Aster Floor Lamp", "Rowan Bookcase", "Tova Accent Bench", "Atrium Lounge Chair"],
            "dining-room": ["Sola Dining Chair", "Linea Dining Table", "Cleo Sideboard", "Mira Bar Stool", "Kora Bench", "Elio Console", "Tavern Pendant", "Ava Dining Cabinet", "Nexus Dining Table"],
            "bedroom": ["Nora Bed", "Luma Bedside Table", "Aeris Wardrobe", "Kira Dresser", "Solace Bench", "Orla Nightstand", "Eira Headboard", "Vale Linen Chest", "Zenith Lounge Bed"],
            "home-office": ["Aster Writing Desk", "Haven Task Chair", "Crest Office Shelf", "Studio Cabinet", "Arc Desk Lamp", "Plinth Bookcase", "Focus Wall Unit", "Juniper Office Table", "Horizon Standing Desk"],
            "hallway": ["Entry Console", "Avenue Shoe Cabinet", "Cedar Hall Bench", "Mirror Console", "Mont Hall Table", "Tide Storage Cabinet", "Lattice Wall Shelf", "Alto Umbrella Stand", "Threshold Entry Bench"],
            "outdoor": ["Terra Lounge Chair", "Garden Dining Table", "Pine Outdoor Bench", "Cove Patio Sofa", "Luma Side Table", "Woven Outdoor Stool", "Sunset Planter", "Shade Bistro Set", "Patio Lounge Set"],
            "home-decor": ["Arco Ceramic Vase", "Noma Table Lamp", "Sage Wall Mirror", "Hearth Candle Set", "Woven Floor Basket", "Cloud Cushion", "Sculpted Side Bowl", "Botanical Art Frame", "Horizon Wall Art"],
            "prayer-room": ["Stillness Prayer Mat", "Serene Floor Cushion", "Quiet Reading Chair", "Reflection Console", "Peace Wall Shelf", "Meditation Stool", "Tranquil Low Table", "Devotion Storage Cabinet", "Aura Meditation Bench"],
        }

        for slug, names in category_products.items():
            category = categories[slug]
            existing_count = category.products.filter(is_active=True).count()
            for position, name in enumerate(names[: max(0, 9 - existing_count)], start=existing_count + 1):
                sku = f"DEMO-{slug.upper().replace('-', '')}-{position:02d}"
                product_slug = f"{slug}-{position:02d}-{name.lower().replace(' ', '-')}"
                product, created = Product.objects.get_or_create(
                    sku=sku,
                    defaults={
                        "category": category,
                        "brand": brand,
                        "name": name,
                        "slug": product_slug,
                        "description": (
                            f"{name} brings warm materials and considered proportions "
                            f"to a thoughtfully furnished {category.name.lower()}."
                        ),
                        "price": f"{(12990 + position * 3370):.2f}",
                        "discount_price": f"{(11990 + position * 2990):.2f}" if position % 3 == 0 else None,
                        "stock_quantity": 5 + position,
                        "material": "Wood, fabric, and natural finishes",
                        "color": ["Natural", "Warm oak", "Soft linen", "Walnut", "Stone", "Olive", "Sand", "Charcoal", "Terracotta"][position - 1],
                        "dimensions": "Made for comfortable everyday use",
                        "is_featured": position == 1,
                        "is_active": True,
                    },
                )
                image_path = department_images.get(slug, "products/demo/maison-accent-chair.jpg")
                ProductImage.objects.get_or_create(
                    product=product,
                    sort_order=0,
                    defaults={
                        "image": image_path,
                        "alt_text": f"{name} in {category.name}",
                    },
                )
                created_products += int(created)

        self.stdout.write(
            self.style.SUCCESS(
                f"Demo catalog ready: {len(categories)} departments, "
                f"{created_products} new products."
            )
        )
