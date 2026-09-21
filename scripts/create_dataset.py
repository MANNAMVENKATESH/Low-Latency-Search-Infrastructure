from elasticsearch import Elasticsearch
from datetime import datetime

# Connect to Elasticsearch
es = Elasticsearch("http://localhost:9200")

# Create index
INDEX_NAME = "products"

# Delete old index if it exists
if es.indices.exists(index=INDEX_NAME):
    es.indices.delete(index=INDEX_NAME)

# Create index with mapping
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

# Our initial dataset
products = [
    {
        "title": "Dell Inspiron 15 Laptop",
        "description": "Laptop suitable for students and programming",
        "category": "Laptop",
        "brand": "Dell",
        "price": 55000,
        "rating": 4.4,
        "tags": ["student", "programming", "laptop"],
        "location": "India",
        "updated_at": datetime.now()
    },
    {
        "title": "HP Pavilion 14 Laptop",
        "description": "Lightweight laptop for college students",
        "category": "Laptop",
        "brand": "HP",
        "price": 62000,
        "rating": 4.3,
        "tags": ["student", "college", "laptop"],
        "location": "India",
        "updated_at": datetime.now()
    },
    {
        "title": "Lenovo IdeaPad Gaming Laptop",
        "description": "Gaming and programming laptop with high performance",
        "category": "Laptop",
        "brand": "Lenovo",
        "price": 70000,
        "rating": 4.5,
        "tags": ["gaming", "programming", "laptop"],
        "location": "India",
        "updated_at": datetime.now()
    },
    {
        "title": "Samsung Galaxy S24",
        "description": "Smartphone with high quality camera",
        "category": "Mobile",
        "brand": "Samsung",
        "price": 75000,
        "rating": 4.6,
        "tags": ["mobile", "camera", "smartphone"],
        "location": "India",
        "updated_at": datetime.now()
    },
    {
        "title": "Apple iPhone 15",
        "description": "Premium smartphone with advanced camera",
        "category": "Mobile",
        "brand": "Apple",
        "price": 70000,
        "rating": 4.7,
        "tags": ["mobile", "camera", "smartphone"],
        "location": "India",
        "updated_at": datetime.now()
    },
    {
        "title": "Sony Wireless Headphones",
        "description": "Wireless headphones with noise cancellation",
        "category": "Audio",
        "brand": "Sony",
        "price": 12000,
        "rating": 4.5,
        "tags": ["audio", "wireless", "headphones"],
        "location": "India",
        "updated_at": datetime.now()
    },
    {
        "title": "LG 27 Inch Monitor",
        "description": "Full HD monitor suitable for programming and office work",
        "category": "Monitor",
        "brand": "LG",
        "price": 18000,
        "rating": 4.2,
        "tags": ["monitor", "programming", "office"],
        "location": "India",
        "updated_at": datetime.now()
    },
    {
        "title": "Logitech Wireless Keyboard",
        "description": "Wireless keyboard for office and programming",
        "category": "Keyboard",
        "brand": "Logitech",
        "price": 3500,
        "rating": 4.3,
        "tags": ["keyboard", "wireless", "office"],
        "location": "India",
        "updated_at": datetime.now()
    }
]

# Insert products into Elasticsearch
for product in products:
    es.index(index=INDEX_NAME, document=product)

# Refresh index
es.indices.refresh(index=INDEX_NAME)

print(f"Successfully indexed {len(products)} products.")
print(f"Index name: {INDEX_NAME}")