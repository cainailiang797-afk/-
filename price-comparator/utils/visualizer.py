import json
from typing import List, Dict
from core.models import Product, ComparisonResult


class Visualizer:
    @staticmethod
    def generate_price_chart_data(products: List[Product]) -> dict:
        sorted_products = sorted(products, key=lambda p: p.price)
        labels = []
        prices = []
        platforms = []
        colors = []

        platform_colors = {
            "京东": "#e1251b",
            "淘宝": "#ff4400",
            "拼多多": "#e02e24"
        }

        for i, p in enumerate(sorted_products[:20]):
            short_title = p.title[:15] + "..." if len(p.title) > 15 else p.title
            labels.append(f"{i+1}. {short_title}")
            prices.append(p.price)
            platforms.append(p.platform)
            colors.append(platform_colors.get(p.platform, "#666666"))

        return {
            "type": "bar",
            "data": {
                "labels": labels,
                "datasets": [{
                    "label": "价格 (元)",
                    "data": prices,
                    "backgroundColor": colors,
                    "borderWidth": 0,
                    "borderRadius": 4
                }]
            },
            "options": {
                "indexAxis": "y",
                "responsive": True,
                "plugins": {
                    "legend": {"display": False},
                    "tooltip": {
                        "callbacks": {
                            "label": lambda ctx: f"价格: ¥{ctx.raw}"
                        }
                    }
                },
                "scales": {
                    "x": {"title": {"display": True, "text": "价格 (元)"}},
                    "y": {"title": {"display": False}}
                }
            }
        }

    @staticmethod
    def generate_platform_comparison_data(platform_stats: dict) -> dict:
        labels = list(platform_stats.keys())
        avg_prices = [platform_stats[p]["avg_price"] for p in labels]
        counts = [platform_stats[p]["count"] for p in labels]
        min_prices = [platform_stats[p]["min_price"] for p in labels]
        max_prices = [platform_stats[p]["max_price"] for p in labels]

        colors = ["#e1251b", "#ff4400", "#e02e24"]

        return {
            "avg_price_chart": {
                "type": "bar",
                "data": {
                    "labels": labels,
                    "datasets": [{
                        "label": "平均价格 (元)",
                        "data": avg_prices,
                        "backgroundColor": colors[:len(labels)],
                        "borderRadius": 8
                    }]
                },
                "options": {
                    "responsive": True,
                    "plugins": {
                        "legend": {"display": False}
                    },
                    "scales": {
                        "y": {"beginAtZero": True, "title": {"display": True, "text": "价格 (元)"}}
                    }
                }
            },
            "price_range_chart": {
                "type": "bar",
                "data": {
                    "labels": labels,
                    "datasets": [
                        {
                            "label": "最低价",
                            "data": min_prices,
                            "backgroundColor": "#10b981",
                            "borderRadius": 4
                        },
                        {
                            "label": "最高价",
                            "data": max_prices,
                            "backgroundColor": "#ef4444",
                            "borderRadius": 4
                        }
                    ]
                },
                "options": {
                    "responsive": True,
                    "scales": {
                        "y": {"beginAtZero": True, "title": {"display": True, "text": "价格 (元)"}}
                    }
                }
            },
            "count_chart": {
                "type": "doughnut",
                "data": {
                    "labels": labels,
                    "datasets": [{
                        "data": counts,
                        "backgroundColor": colors[:len(labels)],
                        "borderWidth": 0
                    }]
                },
                "options": {
                    "responsive": True,
                    "plugins": {
                        "legend": {"position": "bottom"}
                    }
                }
            }
        }

    @staticmethod
    def generate_sales_vs_price_scatter(products: List[Product]) -> dict:
        platform_colors = {
            "京东": "#e1251b",
            "淘宝": "#ff4400",
            "拼多多": "#e02e24"
        }

        datasets = []
        for platform in ["京东", "淘宝", "拼多多"]:
            platform_products = [p for p in products if p.platform == platform]
            if platform_products:
                datasets.append({
                    "label": platform,
                    "data": [{"x": p.price, "y": p.sales, "title": p.title} for p in platform_products],
                    "backgroundColor": platform_colors.get(platform, "#666"),
                    "pointRadius": 8,
                    "pointHoverRadius": 12
                })

        return {
            "type": "scatter",
            "data": {"datasets": datasets},
            "options": {
                "responsive": True,
                "plugins": {
                    "tooltip": {
                        "callbacks": {
                            "label": lambda ctx: [
                                f"商品: {ctx.raw.title[:20]}...",
                                f"价格: ¥{ctx.raw.x}",
                                f"销量: {ctx.raw.y}"
                            ]
                        }
                    }
                },
                "scales": {
                    "x": {"title": {"display": True, "text": "价格 (元)"}},
                    "y": {"title": {"display": True, "text": "销量"}}
                }
            }
        }

    @staticmethod
    def generate_price_trend_mock(keyword: str, days: int = 30) -> dict:
        import random
        from datetime import datetime, timedelta

        base_prices = {"京东": 3500, "淘宝": 3200, "拼多多": 2900}
        labels = []
        datasets = []
        colors = {"京东": "#e1251b", "淘宝": "#ff4400", "拼多多": "#e02e24"}

        end_date = datetime.now()
        for i in range(days):
            date = end_date - timedelta(days=days - 1 - i)
            labels.append(date.strftime("%m-%d"))

        for platform, base_price in base_prices.items():
            prices = []
            current_price = base_price
            for i in range(days):
                change = random.uniform(-50, 30)
                current_price = max(base_price * 0.8, min(base_price * 1.2, current_price + change))
                prices.append(round(current_price, 2))

            datasets.append({
                "label": platform,
                "data": prices,
                "borderColor": colors[platform],
                "backgroundColor": colors[platform] + "20",
                "fill": False,
                "tension": 0.4,
                "pointRadius": 2,
                "pointHoverRadius": 6
            })

        return {
            "type": "line",
            "data": {"labels": labels, "datasets": datasets},
            "options": {
                "responsive": True,
                "plugins": {
                    "legend": {"position": "top"},
                    "title": {
                        "display": True,
                        "text": f"「{keyword}」近{days}天价格趋势（模拟数据）"
                    }
                },
                "scales": {
                    "y": {"title": {"display": True, "text": "价格 (元)"}},
                    "x": {"title": {"display": True, "text": "日期"}}
                }
            }
        }

    @staticmethod
    def generate_all_charts(result: ComparisonResult) -> dict:
        return {
            "price_bar": Visualizer.generate_price_chart_data(result.products),
            "platform_comparison": Visualizer.generate_platform_comparison_data(result.platform_stats),
            "sales_scatter": Visualizer.generate_sales_vs_price_scatter(result.products),
            "price_trend": Visualizer.generate_price_trend_mock(result.keyword)
        }
