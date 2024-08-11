from playwright.sync_api import Playwright, sync_playwright


def run(playwright: Playwright) -> None:
    browser = playwright.chromium.launch(headless=False)
    context = browser.new_context()
    page = context.new_page()

    # 导航到页面
    page.goto("https://medium.com/")

    # 等待页面加载完成（可选，具体等待条件可以根据需要调整）
    page.wait_for_load_state('networkidle')

    # 获取整个页面的文本内容
    page_text = page.inner_text('body')  # 'body' 选择器可以获取整个页面的文本内容

    # 输出页面文本内容
    print(page_text)

    # 关闭上下文和浏览器
    context.close()
    browser.close()


with sync_playwright() as playwright:
    run(playwright)
