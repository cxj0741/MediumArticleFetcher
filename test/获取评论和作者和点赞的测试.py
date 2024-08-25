from playwright.async_api import async_playwright

url3 = 'https://medium.com/neurodiversified/accessible-communication-benefits-everyone-b042eb916106'
url1='https://medium.com/write-a-catalyst/how-i-went-from-0-to-3000-a-month-in-three-months-by-writing-online-ecdbbbb3df7e'

async def run(playwright):
    browser = await playwright.chromium.launch(headless=False)
    context = await browser.new_context()
    page = await context.new_page()
    await page.goto(url1)

    author=page.locator('#root > div > div.l.c > div:nth-child(2) > div.ft.fu.fv.fw.fx.l > article > div > div > section > div > div.gu.gv.gw.gx.gy > div > div > div:nth-child(2) > div > div > div > div.ik.il.im.in.io.ab > div.bm.bg.l > div.ab > div > span > div > div > div > div > div > p > a')
    comments=page.locator('#root > div > div.l.c > div:nth-child(2) > div.ft.fu.fv.fw.fx.l > article > div > div > section > div > div.gu.gv.gw.gx.gy > div > div > div:nth-child(2) > div > div > div > div.ab.co.kd.ke.kf.kg.kh.ki.kj.kk.kl.km.kn.ko.kp.kq.kr.ks > div.h.k.w.ff.fg.q > div:nth-child(2) > div > button > p > span')
    likes=page.locator('#root > div > div.l.c > div:nth-child(2) > div.ft.fu.fv.fw.fx.l > article > div > div > section > div > div.gu.gv.gw.gx.gy > div > div > div:nth-child(2) > div > div > div > div.ab.co.kd.ke.kf.kg.kh.ki.kj.kk.kl.km.kn.ko.kp.kq.kr.ks > div.h.k.w.ff.fg.q > div.li.l > div > div.pw-multi-vote-count.l.lw.lx.ly.lz.ma.mb.mc > div > div > p > button')
    # 获取文本内容
    author_text = await author.inner_text()
    comments_text = await comments.inner_text()
    likes_text = await likes.inner_text()
    print(author_text)
    print(comments_text)
    print(likes_text)


    await context.close()
    await browser.close()

async def main():
    async with async_playwright() as playwright:
        await run(playwright)

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
