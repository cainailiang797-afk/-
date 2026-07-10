from typing import List
from .base import BaseCollector
from core.models import Product


class TaobaoCollector(BaseCollector):
    platform_name = "淘宝"
    base_url = "https://item.taobao.com"

    def _mock_search(self, keyword: str, max_results: int) -> List[Product]:
        products = []
        shop_prefixes = ["天猫旗舰", "淘宝精选", "品牌直营", "好物推荐", "人气店铺", "金牌卖家"]
        price_ranges = {
            "手机": (1999, 7999),
            "耳机": (49, 1599),
            "电脑": (2999, 12999),
            "空调": (1499, 5999),
            "冰箱": (1299, 7999),
            "洗衣机": (799, 4999),
            "电视": (999, 9999),
            "笔记本": (3999, 15999),
            "平板": (999, 6999),
            "手表": (199, 3999),
        }
        price_range = price_ranges.get(keyword, (30, 3000))

        for i in range(max_results):
            product = self._generate_mock_product(
                keyword=keyword,
                index=i,
                price_range=price_range,
                sales_range=(1000, 100000),
                rating_range=(4.2, 4.9),
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
