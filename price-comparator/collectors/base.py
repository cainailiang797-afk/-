import random
import time
from abc import ABC, abstractmethod
from typing import List
from core.models import Product


class BaseCollector(ABC):
    platform_name = "base"
    base_url = ""

    def __init__(self, use_mock: bool = True, delay_range: tuple = (1, 3)):
        self.use_mock = use_mock
        self.delay_range = delay_range

    def search(self, keyword: str, max_results: int = 20) -> List[Product]:
        if self.use_mock:
            time.sleep(random.uniform(*self.delay_range) * 0.1)
            return self._mock_search(keyword, max_results)
        return self._real_search(keyword, max_results)

    @abstractmethod
    def _mock_search(self, keyword: str, max_results: int) -> List[Product]:
        pass

    @abstractmethod
    def _real_search(self, keyword: str, max_results: int) -> List[Product]:
        pass

    def _generate_mock_product(self, keyword: str, index: int,
                               price_range: tuple, sales_range: tuple,
                               rating_range: tuple, shop_prefixes: list) -> Product:
        price = round(random.uniform(*price_range), 2)
        sales = random.randint(*sales_range)
        rating = round(random.uniform(*rating_range), 1)
        shop_name = f"{random.choice(shop_prefixes)}{keyword}专营店"
        product_id = f"{self.platform_name}_{int(time.time())}_{index}"

        return Product(
            title=f"【{shop_name}】{keyword} {index + 1}号 - 正品保障 全国联保",
            price=price,
            platform=self.platform_name,
            url=f"{self.base_url}/product/{product_id}",
            sales=sales,
            shop_rating=rating,
            shop_name=shop_name,
            image_url=f"https://img.example.com/{product_id}.jpg",
            product_id=product_id
        )
