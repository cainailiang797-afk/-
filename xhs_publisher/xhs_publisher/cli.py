"""命令行入口：login / publish（单篇）/ batch（批量）。"""

from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path
from typing import Optional

from .auth import has_saved_state, login_interactive
from .publisher import Note, PublishResult, publish_batch, publish_note
from .auth import sync_playwright
from .auth import new_context


def _parse_list_csv(value: Optional[str]) -> list[str]:
    """CSV 单元格里的列表用 | 分隔。"""
    if not value:
        return []
    return [item.strip() for item in value.split("|") if item.strip()]


def load_notes_from_file(path: str) -> list[Note]:
    """从 CSV 或 JSON 读取多篇笔记。

    CSV 列：title, content, images(| 分隔), topics(| 分隔, 可选)
    JSON 结构：[{"title","content","images":[...],"topics":[...]}]
    """
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"数据文件不存在：{path}")

    if p.suffix.lower() == ".json":
        data = json.loads(p.read_text(encoding="utf-8"))
        return [
            Note(
                title=item["title"],
                content=item.get("content", ""),
                images=list(item.get("images", [])),
                topics=list(item.get("topics", [])),
            )
            for item in data
        ]

    if p.suffix.lower() == ".csv":
        notes: list[Note] = []
        with p.open(encoding="utf-8", newline="") as f:
            reader = csv.DictReader(f)
            for row in reader:
                notes.append(
                    Note(
                        title=row["title"].strip(),
                        content=row.get("content", "").strip(),
                        images=_parse_list_csv(row.get("images")),
                        topics=_parse_list_csv(row.get("topics")),
                    )
                )
        return notes

    raise ValueError(f"仅支持 .csv / .json，收到 {p.suffix}")


def _print_result(res: PublishResult) -> None:
    status = "✓ 成功" if res.success else "✗ 失败"
    print(f"  {status} | 标题：{res.note.title}")
    if res.url:
        print(f"    URL：{res.url}")
    if res.error:
        print(f"    备注：{res.error}")


def cmd_login(args: argparse.Namespace) -> int:
    if has_saved_state(args.state_file) and not args.force:
        print("已存在登录态文件。如需重新登录请加 --force。")
        return 0
    login_interactive(state_file=args.state_file, headless=args.headless)
    return 0


def cmd_publish(args: argparse.Namespace) -> int:
    note = Note(
        title=args.title,
        content=args.content or "",
        images=args.images,
        topics=args.topics or [],
    )
    try:
        note.validate()
    except (ValueError, FileNotFoundError) as e:
        print(f"参数校验失败：{e}", file=sys.stderr)
        return 2

    with sync_playwright() as p:
        browser, context = new_context(p, headless=args.headless, state_file=args.state_file)
        try:
            res = publish_note(context, note)
        finally:
            browser.close()
    _print_result(res)
    return 0 if res.success else 1


def cmd_batch(args: argparse.Namespace) -> int:
    try:
        notes = load_notes_from_file(args.file)
    except (FileNotFoundError, ValueError, KeyError) as e:
        print(f"读取数据文件失败：{e}", file=sys.stderr)
        return 2

    if not notes:
        print("数据文件中没有可发布的笔记。", file=sys.stderr)
        return 2

    print(f"共 {len(notes)} 篇笔记待发布。")
    # 先做整体校验，避免发到一半才因某篇格式错误中断
    for idx, n in enumerate(notes, 1):
        try:
            n.validate()
        except (ValueError, FileNotFoundError) as e:
            print(f"第 {idx} 篇校验失败：{e}", file=sys.stderr)
            return 2

    results = publish_batch(
        notes,
        state_file=args.state_file,
        headless=args.headless,
        interval_s=(args.min_interval, args.max_interval),
    )
    print("\n===== 汇总 =====")
    for res in results:
        _print_result(res)
    ok = sum(1 for r in results if r.success)
    print(f"\n成功 {ok}/{len(results)}")
    return 0 if ok == len(results) else 1


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="xhs-publisher",
        description="小红书图文笔记自动发布工具（基于 Playwright）",
    )

    # 共享参数：通过 parent parser 让每个子命令都能接收
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument(
        "--state-file",
        default=None,
        help="登录态文件路径，默认当前目录下的 .xhs_state.json",
    )
    common.add_argument(
        "--headless",
        action="store_true",
        help="无头模式运行（不推荐用于首次登录）",
    )

    sub = parser.add_subparsers(dest="command", required=True)

    p_login = sub.add_parser("login", help="交互式登录并保存登录态", parents=[common])
    p_login.add_argument("--force", action="store_true", help="即使已存在登录态也重新登录")
    p_login.set_defaults(func=cmd_login)

    p_pub = sub.add_parser("publish", help="发布单篇图文笔记", parents=[common])
    p_pub.add_argument("--title", required=True, help="标题（≤20 字）")
    p_pub.add_argument("--content", default="", help="正文（≤1000 字）")
    p_pub.add_argument(
        "--images",
        nargs="+",
        required=True,
        help="图片路径，1-9 张，空格分隔",
    )
    p_pub.add_argument(
        "--topics",
        nargs="*",
        default=[],
        help="话题列表，空格分隔（可选）",
    )
    p_pub.set_defaults(func=cmd_publish)

    p_batch = sub.add_parser("batch", help="批量发布（从 CSV / JSON 读取）", parents=[common])
    p_batch.add_argument("--file", required=True, help="数据文件路径（.csv 或 .json）")
    p_batch.add_argument("--min-interval", type=int, default=60, help="篇间最小停顿秒数")
    p_batch.add_argument("--max-interval", type=int, default=180, help="篇间最大停顿秒数")
    p_batch.set_defaults(func=cmd_batch)

    return parser


def main(argv: Optional[list[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
