import re
from typing import List, Set
from core.models import Product


def clean_products(products: List[Product]) -> List[Product]:
    cleaned = []
    for p in products:
        if not p.title or p.price <= 0:
            continue

        title = re.sub(r'\s+', ' ', p.title.strip())
        title = re.sub(r'【.*?】', '', title).strip()

        price = round(p.price, 2)
        sales = p.sales if p.sales >= 0 else 0
        rating = min(max(p.shop_rating, 0.0), 5.0)

        cleaned_p = Product(
            title=title,
            price=price,
            platform=p.platform,
            url=p.url,
            sales=sales,
            shop_rating=rating,
            shop_name=p.shop_name.strip(),
            image_url=p.image_url,
            product_id=p.product_id,
            collected_at=p.collected_at
        )
        cleaned.append(cleaned_p)

    return cleaned


def deduplicate_products(products: List[Product]) -> List[Product]:
    seen_titles: Set[tuple] = set()
    seen_ids: Set[str] = set()
    deduped = []

    for p in products:
        if p.product_id and p.product_id in seen_ids:
            continue

        title_key = (p.platform, _normalize_title(p.title))
        if title_key in seen_titles:
            continue

        if p.product_id:
            seen_ids.add(p.product_id)
        seen_titles.add(title_key)
        deduped.append(p)

    return deduped


def _normalize_title(title: str) -> str:
    normalized = re.sub(r'[^\u4e00-\u9fa5a-zA-Z0-9]', '', title)
    normalized = normalized.lower()
    if len(normalized) > 30:
        normalized = normalized[:30]
    return normalized
