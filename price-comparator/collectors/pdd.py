from typing import List
from .base import BaseCollector
from core.models import Product


class PDDCollector(BaseCollector):
    platform_name = "拼多多"
    base_url = "https://mobile.yangkeduo.com"

    def _mock_search(self, keyword: str, max_results: int) -> List[Product]:
        products = []
        shop_prefixes = ["百亿补贴", "品牌黑标", "官方旗舰", "品质保障", "百亿品牌", "工厂直供"]
        price_ranges = {
            "手机": (1599, 6999),
            "耳机": (29, 1299),
            "电脑": (2499, 10999),
            "空调": (1299, 4999),
            "冰箱": (999, 6999),
            "洗衣机": (599, 3999),
            "电视": (799, 8999),
            "笔记本": (3499, 13999),
            "平板": (799, 5999),
            "手表": (99, 2999),
        }
        price_range = price_ranges.get(keyword, (20, 2000))

        for i in range(max_results):
            product = self._generate_mock_product(
                keyword=keyword,
                index=i,
                price_range=price_range,
                sales_range=(2000, 200000),
                rating_range=(4.0, 4.8),
                shop_prefixes=shop_prefixes
            )
            products.append(product)

        return products

    def _real_search(self, keyword: str, max_results: int) -> List[Product]:
        products = []
        return products

    def _parse_sales(self, sales_str: str) -> int:
        sales_str = sales_str.replace('+', '').replace('人付款', '').replace('人收货', '')
        if '万' in sales_str:
            return int(float(sales_str.replace('万', '')) * 10000)
        try:
            return int(sales_str)
        except ValueError:
            return 0
