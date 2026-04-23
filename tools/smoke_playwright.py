from pathlib import Path

from playwright.sync_api import expect, sync_playwright


ROOT = Path(__file__).resolve().parents[1]
SCREENSHOT_DIR = ROOT / "artifacts"
SCREENSHOT_DIR.mkdir(exist_ok=True)


with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page(viewport={"width": 1440, "height": 980})
    page.goto("http://127.0.0.1:5173")
    page.wait_for_load_state("networkidle")
    expect(page.get_by_role("heading", name="图文回复评估平台")).to_be_visible()
    expect(page.get_by_role("heading", name="评估输入")).to_be_visible()
    expect(page.get_by_role("heading", name="执行流程")).to_be_visible()
    expect(page.get_by_role("heading", name="评估结果")).to_be_visible()
    page.get_by_role("button", name="使用商务车推荐样例").click()
    expect(page.locator('input[value="30万以内商务车推荐"]')).to_be_visible()
    page.screenshot(path=str(SCREENSHOT_DIR / "home-smoke.png"), full_page=True)
    browser.close()
