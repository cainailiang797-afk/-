#!/usr/bin/env python3
import argparse
import sys
import os
import json

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.collector import CollectorManager
from core.analyzer import ProductAnalyzer
from utils.visualizer import Visualizer


def print_banner():
    banner = r"""
    ╔═══════════════════════════════════════════════════╗
    ║     电商商品价格自动采集与对比工具 v1.0            ║
    ║     E-Commerce Price Comparator                   ║
    ╚═══════════════════════════════════════════════════╝
    """
    print(banner)


def print_result(result, show_charts=False):
    print(f"\n{'='*70}")
    print(f"  搜索关键词: {result.keyword}")
    print(f"  采集商品数: {len(result.products)}")
    print(f"  采集时间: {result.collected_at.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*70}")

    print(f"\n📊 价格概况:")
    print(f"  ├─ 最低价: ¥{result.price_range['min']:.2f}")
    print(f"  ├─ 最高价: ¥{result.price_range['max']:.2f}")
    print(f"  ├─ 价格差: ¥{result.price_range['spread']:.2f}")
    print(f"  └─ 平均价: ¥{result.avg_price:.2f}")

    if result.cheapest:
        print(f"\n💰 最低价商品:")
        print(f"  ├─ 商品: {result.cheapest.title[:50]}...")
        print(f"  ├─ 价格: ¥{result.cheapest.price:.2f}")
        print(f"  ├─ 平台: {result.cheapest.platform}")
        print(f"  ├─ 店铺: {result.cheapest.shop_name}")
        print(f"  └─ 链接: {result.cheapest.url}")

    if result.best_value:
        print(f"\n⭐ 性价比之选:")
        print(f"  ├─ 商品: {result.best_value.title[:50]}...")
        print(f"  ├─ 价格: ¥{result.best_value.price:.2f}")
        print(f"  ├─ 平台: {result.best_value.platform}")
        print(f"  ├─ 销量: {result.best_value.sales}")
        print(f"  ├─ 店铺评分: {result.best_value.shop_rating}")
        print(f"  └─ 链接: {result.best_value.url}")

    print(f"\n📈 各平台统计:")
    for platform, stats in result.platform_stats.items():
        print(f"  ├─ {platform}:")
        print(f"  │   ├─ 商品数: {stats['count']}")
        print(f"  │   ├─ 最低价: ¥{stats['min_price']:.2f}")
        print(f"  │   ├─ 最高价: ¥{stats['max_price']:.2f}")
        print(f"  │   ├─ 平均价: ¥{stats['avg_price']:.2f}")
        print(f"  │   └─ 平均销量: {stats['avg_sales']}")

    print(f"\n📋 商品列表 (按价格排序):")
    print(f"  {'排名':<5} {'平台':<8} {'价格':<12} {'销量':<10} {'评分':<8} 商品名称")
    print(f"  {'-'*5} {'-'*8} {'-'*12} {'-'*10} {'-'*8} {'-'*40}")

    for i, p in enumerate(result.products[:20]):
        tag = ""
        if result.cheapest and p.product_id == result.cheapest.product_id:
            tag = " [最低价]"
        if result.best_value and p.product_id == result.best_value.product_id:
            tag = " [推荐]"
        title = p.title[:40] + "..." if len(p.title) > 40 else p.title
        print(f"  {i+1:<5} {p.platform:<8} ¥{p.price:<10.2f} {p.sales:<10} {p.shop_rating:<7.1f}  {title}{tag}")

    if len(result.products) > 20:
        print(f"\n  ... 还有 {len(result.products) - 20} 条商品")

    print(f"\n{'='*70}\n")


def main():
    parser = argparse.ArgumentParser(
        description="电商商品价格自动采集与对比工具",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python cli.py search "手机"              # 搜索手机并对比
  python cli.py search "耳机" -n 30       # 搜索耳机，每平台30条
  python cli.py search "空调" --platforms 京东 淘宝  # 仅京东和淘宝
  python cli.py search "手表" --output result.json  # 导出JSON
  python cli.py search "笔记本" --real    # 使用真实采集（需配置）
        """
    )

    subparsers = parser.add_subparsers(dest="command", help="可用命令")

    search_parser = subparsers.add_parser("search", help="搜索并对比商品")
    search_parser.add_argument("keyword", help="搜索关键词")
    search_parser.add_argument("-n", "--num", type=int, default=20,
                               help="每个平台采集数量 (默认: 20)")
    search_parser.add_argument("--platforms", nargs="+",
                               default=["京东", "淘宝", "拼多多"],
                               help="指定平台 (默认: 京东 淘宝 拼多多)")
    search_parser.add_argument("--output", "-o", help="导出结果到JSON文件")
    search_parser.add_argument("--real", action="store_true",
                               help="使用真实采集（默认使用模拟数据）")
    search_parser.add_argument("--no-chart", action="store_true",
                               help="不生成图表数据")

    subparsers.add_parser("demo", help="运行演示示例")

    args = parser.parse_args()

    if args.command == "demo":
        run_demo()
    elif args.command == "search":
        run_search(args)
    else:
        parser.print_help()


def run_demo():
    print_banner()
    print("🎯 运行演示模式...")
    print("搜索关键词: 手机")
    print("使用模拟数据进行演示\n")

    manager = CollectorManager(use_mock=True, platforms=["京东", "淘宝", "拼多多"])
    analyzer = ProductAnalyzer()

    print("正在采集商品数据...")
    products = manager.search_all("手机", max_results_per_platform=15)
    print(f"✓ 共采集到 {len(products)} 条商品数据")

    print("正在分析对比...")
    result = analyzer.analyze("手机", products)

    print_result(result)

    demo_file = os.path.join(os.path.dirname(__file__), "examples", "demo_result.json")
    os.makedirs(os.path.dirname(demo_file), exist_ok=True)
    with open(demo_file, "w", encoding="utf-8") as f:
        json.dump(result.to_dict(), f, ensure_ascii=False, indent=2)
    print(f"💾 演示数据已保存到: {demo_file}")


def run_search(args):
    print_banner()
    use_mock = not args.real

    mode = "模拟模式" if use_mock else "真实模式"
    print(f"🔍 搜索模式: {mode}")
    print(f"🔍 搜索关键词: {args.keyword}")
    print(f"🔍 目标平台: {', '.join(args.platforms)}")
    print(f"🔍 每平台数量: {args.num}\n")

    manager = CollectorManager(use_mock=use_mock, platforms=args.platforms)
    analyzer = ProductAnalyzer()

    print("正在采集商品数据...")
    products = manager.search_all(args.keyword, max_results_per_platform=args.num)
    print(f"✓ 共采集到 {len(products)} 条商品数据")

    print("正在清洗和分析数据...")
    result = analyzer.analyze(args.keyword, products)

    print_result(result, show_charts=not args.no_chart)

    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            json.dump(result.to_dict(), f, ensure_ascii=False, indent=2)
        print(f"💾 结果已保存到: {args.output}")


if __name__ == "__main__":
    main()
