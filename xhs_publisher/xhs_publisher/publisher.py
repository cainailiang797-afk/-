"""图文笔记发布流程。"""

from __future__ import annotations

import random
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, Optional

from playwright.sync_api import (
    BrowserContext,
    Page,
    TimeoutError as PWTimeout,
    sync_playwright,
)

from .auth import CREATOR_URL, is_logged_in, new_context


@dataclass
class Note:
    """一篇图文笔记的数据。"""

    title: str
    content: str
    images: list[str] = field(default_factory=list)
    topics: list[str] = field(default_factory=list)

    def validate(self) -> None:
        if not self.title or not self.title.strip():
            raise ValueError("标题不能为空")
        if len(self.title) > 20:
            raise ValueError(f"标题超长（{len(self.title)} > 20）：{self.title}")
        if not self.images:
            raise ValueError("图文笔记至少需要 1 张图片")
        for img in self.images:
            if not Path(img).exists():
                raise FileNotFoundError(f"图片不存在：{img}")
        if len(self.content) > 1000:
            raise ValueError(f"正文超长（{len(self.content)} > 1000）")


@dataclass
class PublishResult:
    success: bool
    note: Note
    url: Optional[str] = None
    error: Optional[str] = None


def _sleep(min_s: float = 0.6, max_s: float = 1.6) -> None:
    """随机短停顿，降低机器节奏被风控识别的概率。"""
    time.sleep(random.uniform(min_s, max_s))


def _wait_upload_done(page: Page, expected_count: int, timeout_ms: int = 60_000) -> None:
    """等待所有图片上传完成：等到出现 expected_count 个已上传缩略图且无上传中进度条。"""
    deadline = time.time() + timeout_ms / 1000
    while time.time() < deadline:
        # 上传中的进度元素（不同版本选择器不同，尽量宽松）
        uploading = page.locator(
            "[class*='upload'][class*='loading'], [class*='progress'], "
            "[class*='uploading']"
        ).count()
        thumbs = page.locator(
            "[class*='upload'] img, [class*='image-item'] img, "
            "[class*='drag'] img[src]"
        ).count()
        if thumbs >= expected_count and uploading == 0:
            return
        time.sleep(1)
    raise PWTimeout(f"图片上传未在 {timeout_ms // 1000}s 内完成")


def _fill_title(page: Page, title: str) -> None:
    """填写标题。"""
    selectors = [
        'input[placeholder*="标题"]',
        'input.dsl-title',
        'input[maxlength="20"]',
        'textarea[placeholder*="标题"]',
    ]
    for sel in selectors:
        loc = page.locator(sel).first
        if loc.count() > 0:
            loc.click()
            loc.fill("")
            loc.type(title, delay=random.randint(40, 120))
            _sleep()
            return
    raise RuntimeError("未找到标题输入框，页面结构可能已变更")


def _fill_content(page: Page, content: str) -> None:
    """填写正文。"""
    selectors = [
        '[contenteditable="true"][placeholder*="描述"]',
        '[contenteditable="true"][class*="content"]',
        'div[contenteditable="true"]',
        'textarea[placeholder*="描述"]',
        'textarea[class*="content"]',
    ]
    for sel in selectors:
        loc = page.locator(sel).first
        if loc.count() > 0:
            loc.click()
            loc.fill("")
            loc.type(content, delay=random.randint(30, 90))
            _sleep()
            return
    raise RuntimeError("未找到正文输入框，页面结构可能已变更")


def _add_topic(page: Page, topic: str) -> bool:
    """在正文末尾通过 # 触发话题选择，命中第一个候选。

    返回是否成功选中候选；失败则返回 False（话题会以纯文本形式留在正文中）。
    """
    try:
        body = page.locator(
            '[contenteditable="true"][placeholder*="描述"], '
            'div[contenteditable="true"]'
        ).first
        body.type("#", delay=random.randint(50, 100))
        _sleep(0.4, 0.9)
        body.type(topic, delay=random.randint(50, 120))
        # 等待话题候选浮层出现
        popup = page.locator(
            "[class*='topic'][class*='popup'], [class*='hashtag'] [class*='list'], "
            "[class*='mention'] [class*='item']"
        ).first
        popup.wait_for(state="visible", timeout=4000)
        _sleep(0.3, 0.7)
        # 选中第一个候选（通常是回车）
        page.keyboard.press("Enter")
        _sleep(0.4, 0.8)
        return True
    except Exception:
        # 候选未出现时，补一个空格分隔，避免吞掉文字
        try:
            page.keyboard.type(" ", delay=50)
        except Exception:
            pass
        return False


def _click_publish(page: Page) -> None:
    """点击发布按钮。"""
    candidates = [
        'button:has-text("发布")',
        'button.publishBtn',
        'div[class*="publish"]:has-text("发布")',
        '[class*="submit"]:has-text("发布")',
    ]
    for sel in candidates:
        loc = page.locator(sel).first
        if loc.count() > 0:
            loc.wait_for(state="visible", timeout=5000)
            _sleep(0.5, 1.2)
            loc.click()
            return
    raise RuntimeError("未找到发布按钮")


def _wait_publish_done(page: Page, timeout_ms: int = 30_000) -> Optional[str]:
    """等待发布完成，返回成功页 URL（如有）。"""
    try:
        page.wait_for_url("**/publish/success**", timeout=timeout_ms)
        return page.url
    except PWTimeout:
        pass
    # 兜底：检测页面是否出现“发布成功”提示
    try:
        page.wait_for_selector("text=发布成功", timeout=8000)
        return page.url
    except PWTimeout:
        return None


def publish_note(
    context: BrowserContext,
    note: Note,
) -> PublishResult:
    """在已登录的 context 中发布一篇图文笔记。"""
    note.validate()
    page = context.new_page()
    try:
        page.goto(CREATOR_URL, wait_until="domcontentloaded")
        if not is_logged_in(page):
            return PublishResult(False, note, error="未登录或登录态已失效，请重新执行 login")

        # 上传图片
        file_input = page.locator('input[type="file"]').first
        file_input.wait_for(state="attached", timeout=15000)
        file_input.set_input_files([str(Path(i).resolve()) for i in note.images])
        _wait_upload_done(page, expected_count=len(note.images))
        _sleep(1.0, 2.0)

        # 标题 + 正文
        _fill_title(page, note.title)
        _fill_content(page, note.content)

        # 话题
        for topic in note.topics:
            _add_topic(page, topic)

        _sleep(0.8, 1.6)
        _click_publish(page)

        url = _wait_publish_done(page)
        if url:
            return PublishResult(True, note, url=url)
        # 未跳转到成功页，但也没报错：返回当前 URL 让用户复核
        return PublishResult(
            True,
            note,
            url=page.url,
            error="未确认到成功页，请到 App / 创作者中心复核",
        )
    except Exception as e:  # noqa: BLE001
        return PublishResult(False, note, error=str(e))
    finally:
        try:
            page.close()
        except Exception:
            pass


def publish_batch(
    notes: list[Note],
    *,
    state_file: Optional[str] = None,
    headless: bool = False,
    interval_s: tuple[int, int] = (60, 180),
    on_result: Optional[Callable[[PublishResult], None]] = None,
) -> list[PublishResult]:
    """批量发布。两篇之间随机停顿 interval_s，降低风控。"""
    results: list[PublishResult] = []
    with sync_playwright() as p:
        browser, context = new_context(p, headless=headless, state_file=state_file)
        try:
            for idx, note in enumerate(notes, 1):
                print(f"[{idx}/{len(notes)}] 发布：{note.title}")
                res = publish_note(context, note)
                results.append(res)
                if on_result:
                    on_result(res)
                if res.success:
                    print(f"  ✓ 成功 {res.url or ''}")
                else:
                    print(f"  ✗ 失败：{res.error}")
                if idx < len(notes):
                    gap = random.randint(*interval_s)
                    print(f"  等待 {gap}s 后继续……")
                    time.sleep(gap)
        finally:
            browser.close()
    return results
