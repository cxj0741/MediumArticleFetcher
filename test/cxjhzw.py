import os
from playwright.sync_api import sync_playwright


def run(keyword=None, refresh=False):
    # 直接使用绝对路径
    # user_data_dir = '/home/ubuntu/MediumArticleFetcher/User Data'
    user_data_dir = os.path.abspath('../User Data')
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch_persistent_context(
            user_data_dir=user_data_dir,
            headless=False,
            viewport={"width": 1280, "height": 720}
        )
        print("User data directory:", user_data_dir)

        page = browser.new_page()
        page.goto("https://medium.com/")

        # 未登录页面的元素
        # likes_locator = page.locator(
        #     ' #root > div > div.l.n.s > div.ar.as.n.s.at.au.av > div.di.m.as.n.o.p.au > div > div.do.dp.dq.dr.ds.dt.bo > span > h2')
        # print(likes_locator.inner_text())

        likes_locator1 = page.locator(
            ' #root > div > div.s.c > div.bz.gr.gs.gt > div.gw.gx.gy.gz.ha.hb.hc.hd.af.he.hf.hg.hh.hi.hj.n.bz > div > div > div > a > p ')
        print(likes_locator1.inner_text())
        browser.close()


if __name__ == "__main__":
    run()
