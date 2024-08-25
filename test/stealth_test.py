from playwright.sync_api import sync_playwright

def run(playwright) -> None:
    browser = playwright.chromium.launch(headless=False)
    context = browser.new_context(
        user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/103.0.0.0 Safari/537.36',
        viewport={'width': 1280, 'height': 720},
        locale='en-US',
        timezone_id='America/New_York'
    )
    page = context.new_page()

    # 伪装自动化浏览器
    context.add_init_script("""
        Object.defineProperty(navigator, 'webdriver', { get: () => undefined });
        window.navigator.chrome = { runtime: {} };
        Object.defineProperty(navigator, 'languages', { get: () => ['en-US', 'en'] });
        Object.defineProperty(navigator, 'plugins', { get: () => [1, 2, 3, 4, 5] });
        Object.defineProperty(navigator, 'platform', { get: () => 'Win32' });
    """)

    # 手动设置 cookies（如果有）
    # cookies = [{"name": "cookie_name", "value": "cookie_value", "domain": ".example.com", "path": "/"}]
    # context.add_cookies(cookies)

    # 访问目标网站
    page.goto("https://accounts.google.com/")
    page.wait_for_timeout(5000)

    # 尝试登录
    page.fill('input[type="email"]', 'your-email@example.com')
    page.click('button[type="button"]')

    # 等待页面加载和可能的操作
    page.wait_for_timeout(50000)  # 50 秒，调整根据需要

    # 清理
    context.close()
    browser.close()

with sync_playwright() as playwright:
    run(playwright)
