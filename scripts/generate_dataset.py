from elasticsearch import Elasticsearch
from elasticsearch.helpers import bulk
from datetime import datetime, timedelta
import random

# Connect to Elasticsearch
es = Elasticsearch("http://localhost:9200")

INDEX_NAME = "products"

# Reproducible random data
random.seed(42)

# Product information
categories = {
    "Laptop": {
        "brands": ["Dell", "HP", "Lenovo", "Acer", "Asus"],
        "items": [
            "Laptop for Students",
            "Programming Laptop",
            "Gaming Laptop",
            "Business Laptop",
            "Lightweight Laptop"
        ]
    },
    "Mobile": {
        "brands": ["Samsung", "Apple", "OnePlus", "Google", "Xiaomi"],
        "items": [
            "Camera Smartphone",
            "Budget Smartphone",
            "Gaming Smartphone",
            "5G Smartphone",
            "Premium Smartphone"
        ]
    },
    "Tablet": {
        "brands": ["Samsung", "Apple", "Lenovo", "Xiaomi"],
        "items": [
            "Student Tablet",
            "Drawing Tablet",
            "Gaming Tablet",
            "Android Tablet"
        ]
    },
    "Audio": {
        "brands": ["Sony", "JBL", "Boat", "Bose"],
        "items": [
            "Wireless Headphones",
            "Noise Cancelling Headphones",
            "Bluetooth Earbuds",
            "Wireless Earphones"
        ]
    },
    "Monitor": {
        "brands": ["LG", "Samsung", "Dell", "Acer"],
        "items": [
            "Full HD Monitor",
            "Gaming Monitor",
            "4K Monitor",
            "Office Monitor"
        ]
    },
    "Keyboard": {
        "brands": ["Logitech", "HP", "Dell", "Redragon"],
        "items": [
            "Wireless Keyboard",
            "Mechanical Keyboard",
            "Gaming Keyboard",
            "Office Keyboard"
        ]
    },
    "Mouse": {
        "brands": ["Logitech", "HP", "Dell", "Razer"],
        "items": [
            "Wireless Mouse",
            "Gaming Mouse",
            "Bluetooth Mouse",
            "Office Mouse"
        ]
    },
    "Storage": {
        "brands": ["Samsung", "SanDisk", "Western Digital", "Kingston"],
        "items": [
            "External SSD",
            "Portable SSD",
            "USB Storage Drive",
            "External Hard Drive"
        ]
    }
}

locations = [
    "India",
    "Bangalore",
    "Hyderabad",
    "Chennai",
    "Mumbai",
    "Delhi"
]

# Create index
if es.indices.exists(index=INDEX_NAME):
    es.indices.delete(index=INDEX_NAME)

es.indices.create(
    index=INDEX_NAME,
    mappings={
        "properties": {
            "title": {"type": "text"},
            "description": {"type": "text"},
            "category": {"type": "keyword"},
            "brand": {"type": "keyword"},
            "price": {"type": "float"},
            "rating": {"type": "float"},
            "tags": {"type": "keyword"},
            "location": {"type": "keyword"},
            "updated_at": {"type": "date"}
        }
    }
)

# Generate products
def generate_products(count=1000):
    products = []

    category_names = list(categories.keys())

    for i in range(1, count + 1):

        category = random.choice(category_names)

        brand = random.choice(
            categories[category]["brands"]
        )

        item = random.choice(
            categories[category]["items"]
        )

        title = f"{brand} {item} {i}"

        description = (
            f"{brand} {item} suitable for "
            f"students, professionals and everyday use. "
            f"Provides reliable performance and good quality."
        )

        price = round(random.uniform(2000, 100000), 2)

        rating = round(random.uniform(3.0, 5.0), 1)

        tags = [
            category.lower(),
            brand.lower(),
            item.lower().replace(" ", "_")
        ]

        product = {
            "_index": INDEX_NAME,
            "_id": f"P{i:04d}",
            "_source": {
                "title": title,
                "description": description,
                "category": category,
                "brand": brand,
                "price": price,
                "rating": rating,
                "tags": tags,
                "location": random.choice(locations),
                "updated_at": (
                    datetime.now()
                    - timedelta(days=random.randint(0, 30))
                )
            }
        }

        products.append(product)

    return products


# Generate and index products
products = generate_products(1000)

success, failed = bulk(es, products)

es.indices.refresh(index=INDEX_NAME)

print("=" * 60)
print("CLOUD-30 DATASET GENERATION")
print("=" * 60)
print(f"Products generated: {len(products)}")
print(f"Products indexed:   {success}")
print(f"Failed documents:    {failed}")
print(f"Index name:          {INDEX_NAME}")
print("=" * 60)