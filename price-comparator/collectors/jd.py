from typing import List
from .base import BaseCollector
from core.models import Product


class JDCollector(BaseCollector):
    platform_name = "京东"
    base_url = "https://item.jd.com"

    def _mock_search(self, keyword: str, max_results: int) -> List[Product]:
        products = []
        shop_prefixes = ["京东自营", "京东超市", "官方旗舰", "品质优选", "正品专卖"]
        price_ranges = {
            "手机": (2999, 8999),
            "耳机": (99, 1999),
            "电脑": (3999, 15999),
            "空调": (1999, 6999),
            "冰箱": (1599, 8999),
            "洗衣机": (999, 5999),
            "电视": (1299, 12999),
            "笔记本": (4999, 19999),
            "平板": (1299, 8999),
            "手表": (299, 4999),
        }
        price_range = price_ranges.get(keyword, (50, 5000))

        for i in range(max_results):
            product = self._generate_mock_product(
                keyword=keyword,
                index=i,
                price_range=price_range,
                sales_range=(500, 50000),
                rating_range=(4.5, 5.0),
                shop_prefixes=shop_prefixes
            )
            products.append(product)

        return products

    def _real_search(self, keyword: str, max_results: int) -> List[Product]:
        import requests
        from bs4 import BeautifulSoup

        products = []
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }

        try:
            url = f"https://search.jd.com/Search?keyword={keyword}&enc=utf-8"
            resp = requests.get(url, headers=headers, timeout=10)
            soup = BeautifulSoup(resp.text, 'html.parser')

            items = soup.select('.gl-item')[:max_results]
            for item in items:
                try:
                    title = item.select_one('.p-name em').get_text(strip=True)
                    price = float(item.select_one('.p-price i').get_text(strip=True))
                    link = 'https:' + item.select_one('.p-name a')['href']
                    shop = item.select_one('.p-shop a').get_text(strip=True) if item.select_one('.p-shop a') else ''
                    sales = item.select_one('.p-commit strong a').get_text(strip=True) if item.select_one('.p-commit strong a') else '0'
                    sales_num = self._parse_sales(sales)
                    img = 'https:' + item.select_one('.p-img img')['src'] if item.select_one('.p-img img') else ''

                    products.append(Product(
                        title=title,
                        price=price,
                        platform=self.platform_name,
                        url=link,
                        sales=sales_num,
                        shop_rating=4.8,
                        shop_name=shop,
                        image_url=img,
                        product_id=link.split('/')[-1].replace('.html', '')
                    ))
                except Exception:
                    continue
        except Exception:
            pass

        return products

    def _parse_sales(self, sales_str: str) -> int:
        sales_str = sales_str.replace('+', '').replace('人付款', '').replace('人收货', '')
        if '万' in sales_str:
            return int(float(sales_str.replace('万', '')) * 10000)
        try:
            return int(sales_str)
        except ValueError:
            return 0
