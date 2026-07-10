from .models import Product, ComparisonResult
from typing import List, Tuple
from utils.data_cleaner import clean_products, deduplicate_products


class ProductAnalyzer:
    def __init__(self):
        pass

    def analyze(self, keyword: str, products: List[Product]) -> ComparisonResult:
        cleaned = clean_products(products)
        deduped = deduplicate_products(cleaned)
        sorted_products = sorted(deduped, key=lambda p: p.price)

        cheapest = sorted_products[0] if sorted_products else None
        best_value = self._find_best_value(sorted_products)
        avg_price = self._calc_avg_price(sorted_products)
        price_range = self._calc_price_range(sorted_products)
        platform_stats = self._calc_platform_stats(sorted_products)

        return ComparisonResult(
            keyword=keyword,
            products=sorted_products,
            cheapest=cheapest,
            best_value=best_value,
            avg_price=avg_price,
            price_range=price_range,
            platform_stats=platform_stats
        )

    def _find_best_value(self, products: List[Product]) -> Product:
        if not products:
            return None

        scores = []
        for p in products:
            price_score = 1.0 - (p.price - min(pr.price for pr in products)) / \
                (max(pr.price for pr in products) - min(pr.price for pr in products) + 1)
            sales_score = min(p.sales / max(pr.sales for pr in products) if products else 1, 1.0)
            rating_score = (p.shop_rating - 4.0) / 1.0 if p.shop_rating > 4.0 else 0.0

            total_score = price_score * 0.4 + sales_score * 0.3 + rating_score * 0.3
            scores.append((p, total_score))

        scores.sort(key=lambda x: x[1], reverse=True)
        return scores[0][0] if scores else None

    def _calc_avg_price(self, products: List[Product]) -> float:
        if not products:
            return 0.0
        return round(sum(p.price for p in products) / len(products), 2)

    def _calc_price_range(self, products: List[Product]) -> dict:
        if not products:
            return {"min": 0, "max": 0, "spread": 0}
        prices = [p.price for p in products]
        return {
            "min": min(prices),
            "max": max(prices),
            "spread": round(max(prices) - min(prices), 2)
        }

    def _calc_platform_stats(self, products: List[Product]) -> dict:
        stats = {}
        for p in products:
            if p.platform not in stats:
                stats[p.platform] = {
                    "count": 0,
                    "total_price": 0.0,
                    "min_price": float('inf'),
                    "max_price": 0.0,
                    "avg_sales": 0,
                    "total_sales": 0
                }
            s = stats[p.platform]
            s["count"] += 1
            s["total_price"] += p.price
            s["total_sales"] += p.sales
            if p.price < s["min_price"]:
                s["min_price"] = p.price
            if p.price > s["max_price"]:
                s["max_price"] = p.price

        for platform in stats:
            s = stats[platform]
            s["avg_price"] = round(s["total_price"] / s["count"], 2) if s["count"] else 0
            s["avg_sales"] = int(s["total_sales"] / s["count"]) if s["count"] else 0
            del s["total_price"]
            del s["total_sales"]

        return stats
