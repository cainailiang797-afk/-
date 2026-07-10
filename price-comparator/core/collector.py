from typing import List, Dict
from concurrent.futures import ThreadPoolExecutor, as_completed
from .models import Product
from collectors import JDCollector, TaobaoCollector, PDDCollector


class CollectorManager:
    def __init__(self, use_mock: bool = True, platforms: List[str] = None,
                 max_workers: int = 3):
        self.use_mock = use_mock
        self.max_workers = max_workers
        self.platforms = platforms or ["京东", "淘宝", "拼多多"]
        self._collectors = self._init_collectors()

    def _init_collectors(self) -> Dict[str, object]:
        collector_map = {
            "京东": JDCollector,
            "淘宝": TaobaoCollector,
            "拼多多": PDDCollector
        }
        collectors = {}
        for p in self.platforms:
            if p in collector_map:
                collectors[p] = collector_map[p](use_mock=self.use_mock)
        return collectors

    def search_all(self, keyword: str, max_results_per_platform: int = 20) -> List[Product]:
        all_products = []

        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            future_to_platform = {}
            for platform, collector in self._collectors.items():
                future = executor.submit(collector.search, keyword, max_results_per_platform)
                future_to_platform[future] = platform

            for future in as_completed(future_to_platform):
                platform = future_to_platform[future]
                try:
                    products = future.result()
                    all_products.extend(products)
                except Exception as e:
                    print(f"[{platform}] 采集失败: {e}")

        return all_products

    def search_single(self, platform: str, keyword: str, max_results: int = 20) -> List[Product]:
        if platform not in self._collectors:
            raise ValueError(f"不支持的平台: {platform}")
        return self._collectors[platform].search(keyword, max_results)
