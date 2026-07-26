"""登录态管理：Cookie / storage_state 持久化。"""

from __future__ import annotations

import time
from pathlib import Path
from typing import Optional

from playwright.sync_api import Browser, BrowserContext, Page, sync_playwright

DEFAULT_STATE_FILE = ".xhs_state.json"
CREATOR_URL = "https://creator.xiaohongshu.com/publish/publish"
LOGIN_TIMEOUT_MS = 5 * 60 * 1000  # 登录等待最长 5 分钟

# 真实浏览器 UA，降低风控命中概率
DEFAULT_UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36"
)


def resolve_state_path(state_file: Optional[str]) -> Path:
    """返回 storage_state 文件路径，默认当前目录。"""
    return Path(state_file) if state_file else Path.cwd() / DEFAULT_STATE_FILE


def has_saved_state(state_file: Optional[str]) -> bool:
    """判断是否已存在可复用的登录态文件。"""
    return resolve_state_path(state_file).exists()


def new_context(
    playwright,
    *,
    headless: bool = False,
    state_file: Optional[str] = None,
    user_agent: str = DEFAULT_UA,
) -> tuple[Browser, BrowserContext]:
    """创建浏览器与上下文，自动注入已保存的 storage_state。"""
    browser = playwright.chromium.launch(
        headless=headless,
        args=[
            "--disable-blink-features=AutomationControlled",
            "--no-sandbox",
        ],
    )
    storage_path = resolve_state_path(state_file)
    kwargs = {
        "user_agent": user_agent,
        "viewport": {"width": 1280, "height": 800},
        "locale": "zh-CN",
    }
    if storage_path.exists():
        kwargs["storage_state"] = str(storage_path)
    context = browser.new_context(**kwargs)
    return browser, context


def save_state(context: BrowserContext, state_file: Optional[str]) -> Path:
    """保存当前 context 的 storage_state（cookie + localStorage）到文件。"""
    storage_path = resolve_state_path(state_file)
    context.storage_state(path=str(storage_path))
    return storage_path


def is_logged_in(page: Page) -> bool:
    """判断当前是否处于已登录状态。

    登录态下访问发布页会停留在 publish/publish；
    未登录会被重定向到 login 页或出现二维码弹窗。
    """
    try:
        page.wait_for_load_state("networkidle", timeout=8000)
    except Exception:
        pass
    url = page.url
    if "/login" in url or "signin" in url:
        return False
    # 发布页通常存在上传图片的 input
    try:
        page.wait_for_selector('input[type="file"]', timeout=6000)
        return True
    except Exception:
        return False


def login_interactive(
    state_file: Optional[str] = None,
    headless: bool = False,
    timeout_ms: int = LOGIN_TIMEOUT_MS,
) -> Path:
    """交互式登录：打开浏览器让用户扫码，登录成功后保存 storage_state。

    返回保存的文件路径。
    """
    with sync_playwright() as p:
        browser, context = new_context(p, headless=headless, state_file=None)
        page = context.new_page()
        page.goto(CREATOR_URL)
        print("请在打开的浏览器中完成登录（扫码 / 手机号均可）。")
        print(f"等待登录完成，最长 {timeout_ms // 1000} 秒……")

        # 轮询直到进入发布页
        start = time.time()
        while time.time() - start < timeout_ms / 1000:
            if is_logged_in(page):
                break
            time.sleep(2)
        else:
            browser.close()
            raise TimeoutError("登录超时，未检测到登录成功。")

        storage_path = save_state(context, state_file)
        print(f"登录成功，已保存登录态到 {storage_path}")
        browser.close()
        return storage_path
