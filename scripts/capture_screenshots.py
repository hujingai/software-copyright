#!/usr/bin/env python3
"""使用 Playwright 对本地 HTTP 服务下的 HTML 页面逐页截图。"""

import os
import sys
import time
from pathlib import Path
from playwright.sync_api import sync_playwright

BASE_URL = "http://localhost:8800"
OUTPUT_DIR = Path(__file__).resolve().parent.parent / "screenshots"

PAGES = [
    ("首页.html", "首页.png"),
    ("课程展示页.html", "课程展示.png"),
    ("在线课堂页.html", "在线课堂.png"),
    ("作业管理页.html", "作业管理.png"),
    ("账户页.html", "账户中心.png"),
]

VIEWPORT = {"width": 1440, "height": 900}


def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(viewport=VIEWPORT)
        page = context.new_page()

        for html_file, png_name in PAGES:
            url = f"{BASE_URL}/{html_file}"
            filepath = OUTPUT_DIR / png_name
            print(f"[SCREENSHOT] {url} -> {png_name}")

            try:
                page.goto(url, wait_until="networkidle", timeout=15000)
                # 等待渲染稳定
                page.wait_for_timeout(2000)
                page.screenshot(path=str(filepath), full_page=True)
                print(f"   OK: {filepath.resolve()} ({filepath.stat().st_size / 1024:.1f} KB)")
            except Exception as e:
                print(f"   FAIL: {e}")

        browser.close()

    print("\nAll screenshots done!")
    print(f"Output: {OUTPUT_DIR.resolve()}")


if __name__ == "__main__":
    main()
