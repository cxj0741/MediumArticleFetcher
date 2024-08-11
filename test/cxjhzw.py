import os
from playwright.sync_api import sync_playwright


def run(keyword=None, refresh=False):
    user_data_dir = os.path.abspath('../User Data')

    with sync_playwright() as playwright:
        browser = playwright.chromium.launch_persistent_context(
            user_data_dir=user_data_dir,
            headless=False,
            viewport={"width": 1280, "height": 720}
        )
        page = browser.new_page()
        page.goto("https://medium.com/")

        likes_locator = page.locator(
            ' #root > div > div.s.c > div.bz.gr.gs.gt > div.gw.gx.gy.gz.ha.hb.hc.hd.af.he.hf.hg.hh.hi.hj.n.bz > div')
        print(likes_locator.inner_text())
        browser.close()


if __name__ == "__main__":
    run()
