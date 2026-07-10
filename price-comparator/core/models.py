from dataclasses import dataclass, field
from typing import List, Optional
from datetime import datetime


@dataclass
class Product:
    title: str
    price: float
    platform: str
    url: str
    sales: int = 0
    shop_rating: float = 0.0
    shop_name: str = ""
    image_url: str = ""
    product_id: str = ""
    collected_at: datetime = field(default_factory=datetime.now)

    def to_dict(self):
        return {
            'title': self.title,
            'price': self.price,
            'platform': self.platform,
            'url': self.url,
            'sales': self.sales,
            'shop_rating': self.shop_rating,
            'shop_name': self.shop_name,
            'image_url': self.image_url,
            'product_id': self.product_id,
            'collected_at': self.collected_at.isoformat()
        }


@dataclass
class PriceHistory:
    product_id: str
    prices: List[dict] = field(default_factory=list)

    def add_price(self, price: float, date: Optional[datetime] = None):
        if date is None:
            date = datetime.now()
        self.prices.append({
            'price': price,
            'date': date.isoformat()
        })


@dataclass
class ComparisonResult:
    keyword: str
    products: List[Product]
    cheapest: Optional[Product] = None
    best_value: Optional[Product] = None
    avg_price: float = 0.0
    price_range: dict = field(default_factory=dict)
    platform_stats: dict = field(default_factory=dict)
    collected_at: datetime = field(default_factory=datetime.now)

    def to_dict(self):
        return {
            'keyword': self.keyword,
            'products': [p.to_dict() for p in self.products],
            'cheapest': self.cheapest.to_dict() if self.cheapest else None,
            'best_value': self.best_value.to_dict() if self.best_value else None,
            'avg_price': self.avg_price,
            'price_range': self.price_range,
            'platform_stats': self.platform_stats,
            'collected_at': self.collected_at.isoformat()
        }
