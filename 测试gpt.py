import asyncio
import os
import random
import httpx
from logger_config import logger


failed_urls = set()

file_path = 'failed_urls.txt'
permanent_failures_path = 'permanent_failures.txt'

# 记录失败的url
def record_failed_url(urls):
    try:
        with open(file_path, 'a') as file:
            for url in urls:
                file.write(f"{url},1\n")
    except Exception as e:
        logger.error(f"记录失败 URL 时发生错误: {e}")

# handle中写入url
def backup_failed_urls(failed_urls):
    # 将内存中的失败 URL 及其失败次数写入文件
    try:
        with open(file_path, 'w') as file:
            for url, count in failed_urls.items():
                file.write(f"{url},{count}\n")
    except Exception as e:
        logger.error(f"备份失败 URL 时发生错误: {e}")

# 处理失败的url
async def handle_failed_urls():
    if not os.path.exists(file_path):
        print("失败 URL 文件不存在")
        return

    temp_failed_urls = {}
    try:
        # 读取文件并更新失败 URL 和失败次数
        with open(file_path, 'r') as file:
            for line in file:
                url, count = line.strip().split(',')
                count = int(count)
                if url in temp_failed_urls:
                    temp_failed_urls[url] = max(temp_failed_urls[url], count)
                else:
                    temp_failed_urls[url] = count

        # 处理失败的 URL
        permanent_failures = []
        tasks = []
        for url, count in list(temp_failed_urls.items()):
            tasks.append(process_failed_url(url, count, temp_failed_urls, permanent_failures))

        await asyncio.gather(*tasks)

        # 备份更新后的失败 URL
        backup_failed_urls(temp_failed_urls)

        # 将永久失败的 URL 追加到永久失败文件中
        if permanent_failures:
            with open(permanent_failures_path, 'a') as file:
                for failure in permanent_failures:
                    file.write(f"{failure}\n")

    except Exception as e:
        print(f"处理失败的 URL 文件时发生错误: {e}")

# 异步调用
async def process_failed_url(url, count, temp_failed_urls, permanent_failures):
    try:
        # 在这里处理 URL
        print(f"重新处理 URL: {url} (失败次数: {count})")
        await scrape_article_content_and_images(url)  # 异步调用抓取函数
        temp_failed_urls.pop(url, None)  # 将处理成功的 URL 清除
    except Exception as e:
        # 处理失败，重新记录失败 URL，并增加失败次数
        if count < 5:
            temp_failed_urls[url] = count + 1
        else:
            # 将失败次数达到最大值的 URL 写入永久失败列表
            permanent_failures.append(f"{url},{count}")



async def retry_request(request_func, max_retries=5, retry_delay=(1, 3), *args, **kwargs):
    """重试请求的逻辑。

    Args:
        request_func (coroutine): 发起请求的异步函数。
        max_retries (int): 最大重试次数。
        retry_delay (tuple): 重试之间的延迟范围 (秒)。
        *args, **kwargs: 传递给请求函数的其他参数。

    Returns:
        response: 请求的响应对象。

    Raises:
        Exception: 如果在最大重试次数后仍然失败，抛出异常。
    """
    attempt = 0
    while attempt < max_retries:
        try:
            # 记录调试信息
            url = kwargs.get('url', '未知URL')
            json_payload = kwargs.get('json', '无负载')
            headers = kwargs.get('headers', '无头部信息')
            logger.debug(f"发起请求: {url} with payload: {json_payload} and headers: {headers}")

            response = await request_func(*args, **kwargs)
            response.raise_for_status()  # 处理HTTP错误
            logger.info("请求成功")
            return response
        except httpx.RequestError as e:
            attempt += 1
            logger.warning(f"请求失败: {e}. 尝试 {attempt}/{max_retries}...")
            if attempt >= max_retries:
                logger.error("达到最大重试次数，放弃请求。")
                raise
            delay = random.uniform(*retry_delay)
            await asyncio.sleep(delay)  # 延迟重试


# async def get_gpt_summary_and_title(client, article_content):
#     # api_key = 'sk-ozYXQPQjeu0xCHFg0a1f329dA2194689931b8a6a6809558c'
#     api_key = 'sk-snwSSPc5VkLWd6mU3cBd8e27211d46338a4c5fC7C52d651c'
#     api_url = 'https://aiserver.marsyoo.com/v1/chat/completions'
#
#
#
#     # api_url = 'https://api.ezchat.top/v1/chat/completions'
#
#     headers = {
#         'Authorization': f'Bearer {api_key}',
#         'Content-Type': 'application/json',
#     }
#     payload = {
#         'model': 'gpt-3.5-turbo',
#         'messages': [
#             {
#                 'role': 'system',
#                 'content': '你是一个帮助生成文章标题和摘要的助手。'
#             },
#             {
#                 'role': 'user',
#                 'content': f"请为以下文章生成一个标题和摘要(摘要就是1-3个概括文章的关键字)：\n\n{article_content}"
#             }
#         ],
#         'max_tokens': 100
#     }
#
#     try:
#         response = await retry_request(
#             client.post,
#             max_retries=5,
#             retry_delay=(1, 3),
#             url=api_url,
#             json=payload,
#             headers=headers
#         )
#         # response= await client.post(url=api_url, headers=headers, json=payload)
#         response.raise_for_status()
#         data = response.json()
#         content = data['choices'][0]['message']['content']
#
#         # 清理返回内容，去掉多余的标签
#         lines = content.split('\n')
#         title = lines[0].strip() if lines else ''
#         summary = ' '.join([line.strip() for line in lines[1:] if line.strip()]) if len(lines) > 1 else ''
#
#         # 去掉可能存在的“标题：”或“摘要：”等多余标识
#         title = title.replace('标题：', '').replace('标题:', '').strip()
#         summary = summary.replace('摘要：', '').replace('摘要:', '').strip()
#
#         return title, summary
#     except httpx.RequestError as e:
#         print(f"获取 GPT 响应时发生错误: {e}")
#         return None, None
async def get_gpt_summary_and_title(client, article_content):
    api_key = 'sk-snwSSPc5VkLWd6mU3cBd8e27211d46338a4c5fC7C52d651c'
    api_url = 'https://aiserver.marsyoo.com/v1/chat/completions'

    headers = {
        'Authorization': f'Bearer {api_key}',
        'Content-Type': 'application/json',
    }
    payload = {
        'model': 'gpt-3.5-turbo',
        'messages': [
            {
                'role': 'system',
                'content': '你是一个帮助生成文章标题和摘要的助手。'
            },
            {
                'role': 'user',
                'content': f"请为以下文章生成一个标题和摘要(摘要就是1-3个概括文章的关键字)：\n\n{article_content}"
            }
        ],
        'max_tokens': 250
    }

    try:
        # print("gpt???????????????????????????????????????")
        # response = await retry_request(client.post, api_url, json=payload, headers=headers)
        response = await retry_request(
            client.post,
            # max_retries=5,
            # retry_delay=(1, 3),
            url=api_url,
            json=payload,
            headers=headers
        )
        response.raise_for_status()
        data = response.json()
        content = data['choices'][0]['message']['content']

        print("gpt请求成功")
        # 清理返回内容，去掉多余的标签
        lines = content.split('\n')
        title = lines[0].strip() if lines else ''
        summary = ' '.join([line.strip() for line in lines[1:] if line.strip()]) if len(lines) > 1 else ''

        # 去掉可能存在的“标题：”或“摘要：”等多余标识
        title = title.replace('标题：', '').replace('标题:', '').strip()
        summary = summary.replace('摘要：', '').replace('摘要:', '').strip()

        print("标题，摘要生成成功")
        return title, summary
    except httpx.RequestError as e:
        print(f"获取 GPT 响应时发生错误: {e}")
        return None, None

async def main():
    article_content = """
       {"content":"Almost 30 years ago, Monica Harrington guided the marketing and business development efforts for\nValve\n, which has become the biggest player in the PC game industry. This is her story.\nAlmost 30 years ago, a small company was founded near Seattle WA.\nGabe Newell\nand my now ex\nMike Harrington\nwere the official cofounders.\nI was on a two-month leave from my job at Microsoft, where I was a group marketing manager in the Consumer Division, overseeing a product portfolio that included Microsoft Games.\nThe Microsoft Market Maker Award, chipped but still standing\nI'd worked for Microsoft for nine years by then. My career was in high gear. A year earlier I'd been honored with the Market Maker award as the marketer who \"added the most to the (1600+-person) Consumer Division's bottom line.\" I loved my job but I was also tired, so when Microsoft announced a leave program in the Spring of 1996, I was all in, hoping that a couple of months of paid leave would be invigorating, ideally with some travel and a break from the remodeling project that had left our new home a mess.\nMy husband Mike had other plans.\nHe'd worked in the game industry before joining Microsoft the same year I did, and he had a dream of starting a game company. Mike decided to use his break to figure out if he wanted to stay at Microsoft or embark on a huge new adventure doing something else. During the break he started to solidify plans with Gabe Newell to really make it happen. Our travel plans quickly disappeared.\nGabe and Mike had met when Mike was working on printer drivers for the OS/2 operating system and the three of us had hung around together beginning a few years earlier, including a weekend in Eastern WA with Gabe's then girlfriend. Mike was also friends with\nMike Abrash\n, an industry luminary who was then working at\nid Software\n, the independent studio behind the hugely popular Doom franchise.\nBecause of his relationship with Abrash, Mike was able to quickly secure agreement to build Valve's first product using id's game engine. That was a huge deal and essentially catapulted Valve and Gabe and Mike into serious company and game development.\nWhen I returned to Microsoft, Mike and Gabe and the small team they quickly assembled were well on their way to planning their first product.\nThe original idea Mike had was that Valve would create a product that would be launched by Microsoft. It turned out that Microsoft had little appetite for doing a deal with its own former employees, which meant that Valve would need to sign a publishing agreement with one of Microsoft's competitors.\nBecause of my role overseeing Games Marketing for Microsoft, the interplay with Valve was complicated. The investment Mike and I were making in Valve was substantial so I knew I couldn't not be involved, but I also needed boundaries. When I returned to Microsoft, I went directly to the head of games and to the VP of our division to say that my husband and Gabe Newell were starting a games business, and that I would be helping them, and that I'd be open to any changes Microsoft might want to make in terms of my role as a result. Both\nEd Fries\nand my managers were friendly and reassuring. At the time, there were literally hundreds of games published each year that vanished into the ether. Valve was a tiny player, and I'm sure from Ed's and everyone else's perspective, likely to remain so.\nI was traveling for Microsoft on a cold wintry day in Seattle when Mike called to tell me that he and the team had just finished meeting with the head of\nSierra Online\n, which was a major force in PC Games and one of our biggest competitors. Their office was in Bellevue WA, just twenty-five minutes or so from our home. Because of the icy conditions, Ken Williams, their CEO, was the only one from Sierra who made it into the office. By the end of the meeting Ken was essentially saying to the team, \"I want to work with you…let's make it happen.\"\nBecause of my role at Microsoft, I decided not to get involved in the contract negotiations. It was up to Mike and Gabe to figure that out with Sierra. At the time, standard industry practice for an unproven game company was for an upfront advance against royalties, with additional royalties due only if the game were successful.\nThe Sierra advance was for approximately a million dollars, which along with the hundreds of thousands Mike and I and Gabe had already invested, meant that Valve had enough to fund the company through the launch of the first product.\nThe first product was going to be a first-person shooter, in the same category as id's category-defining game\nDoom.\nGabe and Mike and I were meeting regularly and one of the things I told them was that the Games business was a hit-based business, where only the top 10 games made any real money. At a time when thousands of games were being introduced each year, it meant that Valve's first game was going to be a hit or it wasn't, and given the dynamics of the games industry, if the first game wasn't a hit, there likely wouldn't be a second Valve game. Gabe and Mike had been talking about trying to launch a B product, something that wasn't a hit, but that would be successful enough to support the company as it established itself, and I knew and made clear that simply wouldn't work.\nFor the next ten months or so, the activity at Valve was all about hiring and onboarding people, building out appropriate office space, and fleshing out the game concept that had hooked Sierra's Ken Williams.\nWhile I continued to consult with Valve, my day job at Microsoft was invigorating. One of the projects we had underway was the first global launch of a new game, which meant a simultaneous launch in all of the markets where Microsoft had a consumer presence. My team and I had been working for months to make sure we had the launch and marketing strategies ready to go to support Microsoft's next big hit game in markets around the world. At the time, the game group's biggest hits to date were the strategy game\nAge of Empires\nand\nFlight Simulator,\na product that mostly appealed to pilots and flying enthusiasts.\nIn the background, I was still working with Valve, something I reminded Microsoft folks about frequently. No one seemed worried. My general rule was that I wouldn't tell Microsoft anything about Valve, and I would tell Valve nothing about what was happening at Microsoft. However, all of the learning I was doing about the games industry in my work and personal time was definitely put to work for both Microsoft and Valve. Mike and I were each working 10 to 12-hour days or more.\nAt one time, I was in a meeting with some well-known game developers who had signed a long-term, multi-game development deal with Microsoft and the subject of Valve's new deal, using the id engine came up. The leads of that company, not having any idea about my ties to Valve said something like, \"what a joke — a couple of Microsoft developers license the id engine and think they can build a game.\"\nInside, I thought, \"Oh man…this is going to be tough.\"\nOne of the roles I played with Mike and Gabe in those days was to help them understand what it would take to be successful from a marketing and business standpoint. At the time, the key marketing strategies for games involved PR and outreach to influentials, advertising in game-specific publications, and working with the retail channel on strategies to get prominent display space so a consumer walking in would feel compelled to pick up and purchase your game. Once a game shipped, you had to feed and nurture the early adopters, supporting them so they could tell their friends about your game. The broad strategy I'd learned and fine-tuned over a period of years was essentially \"Arm and Activate (early adopters).\"\nFrom a PR perspective, Microsoft was a phenomenon within the industry. By the time I worked on the games business, I'd spent years working directly with consumer and technical press for products ranging from Microsoft Word and Office to Expedia and Encarta. I'd also managed large product marketing and communication teams, and had been on press tours meeting reviewers around the country, from New York to New Hampshire to Austin, Texas, and Eugene, Oregon. The games business shared a lot in common with some of the other businesses I worked on, but there was also a key difference. In a business like Word or Office, you basically run your marketing with a winner-take-all perspective, and that's because in those businesses, there's likely to be one market leader, and as that leader gains more market share, its advantages continue to grow and become self-reinforcing as companies and the broader industry standardize around one product. At the time, my experience in fighting market battles with Lotus and WordPerfect was that a given software category will only support one market leader.\nThe PC games business in the late 90s was much more like the music business, where there were lots of independent studios, and where the developers treated each other much as musicians do. There's mutual respect, there's competition in a given category, but also the understanding that gamers are going to buy multiple games. If they love your game, they also have room to love your competitor's game and in fact someone who likes action games is likely to be a connoisseur of the category, with multiple favorites. The most influential people in the games market were not press, but game developers themselves.\nFor the publishers and major players, it was a different story. Microsoft was competing against Sierra and Electronic Arts to attract game developers, much like music labels at the time competed to sign top musical talent. The typical 15 percent royalty margins for new games developers mimicked other content deals in music and book publishing.\nOf course, the huge difference between the games business and the book or music industry was that the costs of producing a game were much higher and starting to climb exponentially.\nAt Valve, costs were growing rapidly as the team was being built out. Soon it became clear that the initial investment Gabe and Mike and I had made plus the advance Sierra had made were not going to cover the actual cost of producing Valve's first game.\nOne evening Mike and I hosted a potential new Valve hire, Yahn Bernier, and his fiancé at our newly remodeled home. I remember thinking that \"if we hire you, Mike and I and Gabe are going to be paying your salary from our own pockets.\"\nWe pitched Yahn and his fiancé Beth hard. I remember that it was only a few days earlier that Beth had learned Yahn even did software development, as his day job was as a patent attorney in Atlanta. Valve's strength in those days was finding talent around the world who had done amazing things — the type of things that might not show up on a typical resume but could be discovered on the Internet, which in many ways was still in its infancy. At one point Gabe tracked down and recruited two creators of game-related software that was becoming popular on the Internet only to discover that they delivered pizza for a living and they thought Gabe's phone call was part of some elaborate prank.\nFortunately, while the Valve development team was working to build Half-Life, my Microsoft options were continuing to vest, which meant that Mike's and my net worth continued to climb. It was stressful, but in the overall context, the stress was manageable.\nSomewhere in the first year of Half-Life's development, I officially wrote up the marketing plan for launching Half-Life. Key to our strategy was positioning Half-Life as a game that was worthy of Game of the Year honors. We wanted to earn the respect of the industry influentials, which included the gaming press and other game developers. As part of the strategy, Valve's developers went to industry conferences to talk about some of the work they were doing in key technical areas including AI, skeletal animation, and physics. In support of the effort, I wrote up backgrounders on each of these topics for the press based on interviews with developers Ken Birdwell, Jay Stelly, Yahn Bernier and others.\nIn the Spring of 1997, I was in a meeting at Microsoft about the upcoming E3 show, which was the biggest and most important industry tradeshow for electronic entertainment companies. One of my team members made the recommendation for Microsoft not to attend the show, and during her pitch to me and others, part of her recommendation was clearly based on the idea that our competitors weren't likely to have a major presence there. I knew Sierra was going to be there and Valve would have a big presence.\nMeanwhile, the game I'd been focused on for Microsoft, which would have been at the show, had faced a huge setback. A month or two earlier, I had initiated a meeting with Ed Fries where I told him point blank, \"I'm not hearing great things about our game and am losing confidence. Are you sure?\"\nMy conversation was based on hallway talks with various gamers within the division, who had had exposure to the game and weren't excited. Basically, I couldn't find anyone who really believed in the game. I also knew from the work I was doing for Valve what it felt like when developers who are also gamers are hugely excited about a new project\nBy that time, Microsoft's Consumer Division had already laid a huge egg with\nMicrosoft Bob\n, and I knew that if we launched another consumer product that didn't live up to the expectations we'd raised, the broader consumer effort would be hugely damaged. After some soul searching, Ed decided to cancel the launch, and the huge plans we'd made were quietly set aside.\nBy that time, I knew that Sierra was going to be teasing Half-Life and that it would be the star of their booth at E3. I remembered thinking, \"Damn, I know too much. Something has to change.\"\nI had another conversation with Microsoft execs about my role and the conflict with Valve, and again I was essentially told, \"it's fine, we're OK, we like where you're at, don't worry.\"\nA couple of months later, Valve's Half-Life premiered publicly in the Sierra booth at E3 in Las Vegas. The demos Valve showed were so well received that Valve earned Best Action Game honors at the show.\nWhen the Valve team returned from Las Vegas, and I got the full update, I asked for a meeting with the division's senior exec, and said, \"this may not be a conflict for you, but it is for me. I need a new assignment.\"\nShortly thereafter, I started a new role within the company, completely unrelated to the games business.\nAs the months went on and Valve's costs continued to escalate, it became clear that Mike and I were maxing out on our financial commitment. Rather than renegotiate the contract with Sierra, Gabe, who had started at Microsoft much earlier than Mike and me, began funding the ongoing development costs, set up as a loan against future company profits.\nOver that summer and in the months to follow, the \"game\" that Valve had shown, which wasn't actually a game, but instead was some elaborate demos, went into early playtesting, which involved bringing gamers into Valve, having them play with the game elements and giving us their feedback. The feedback was OK. Just OK. Which for a company that needed a hit was devastating.\nGabe and Mike and I all knew that we couldn't stay the course. If Valve shipped the game we had, it would launch and quietly disappear, and all of the work we'd all done would account for nothing. All of the people we'd hired would lose their jobs, we'd lose the money we'd invested. It was a disaster.\nThere was no choice. Ultimately the decision was made to essentially toss out what we had, and use everything the team had learned to that point to start fresh. Unfortunately, Sierra was not on board with the plan. They wouldn't invest any more to make Valve's first game a hit. We were on our own. Gabe's deep pockets became more important.\nIt would take more than a year for Valve to rebuild Half-Life in a way that put us back into the position which everyone assumed was already the case– with a game that could be launched in just a few months. The new target become launching for the Christmas season of 1998.\nIn the Spring of 1998, Gabe was essentially saying, \"When can you be here full-time? We need you now.\"\nI'd already written the marketing and launch plan for Half-Life, I'd written all of the press materials and copy for the web site, I'd written the backgrounders we shared with key press, but I was not focused on some of the larger business fundamentals. As a huge example, I still had not read the publishing agreement Gabe and Mike signed with Sierra.\nI went to my bosses at Microsoft and essentially said, \"I'm ready to leave.\"\nIn my closing interview with Pete Higgins, then the VP of Microsoft's Consumer Division, he started by saying, \"Is there anything that would get you to stay?\" and I knew the answer was No.\nI needed to move on. Valve needed me. We had too much invested. It was time.\nFor the next few months, I worked furiously laying the groundwork for Half-Life's launch. Among the projects I worked on was seeding a story with the Wall St. Journal. Basically, my idea was to build retailer buzz so that the retailers who were going to be putting in orders for the Christmas season would order more Half-Life and feature it prominently. For several weeks, I sent the reporter emails with updates about all of the great Half-Life news, from developer comments to industry buzz that was appearing in the gaming press.\nBy that time, most of my Valve work was with Gabe or the other developers or with Sierra's own marketing team. Mike was furiously heads-down on the final work needed to finish Half-Life so we could send it off for duplication. One of the key issues we worried about was piracy. One of my nephews had recently bought a CD duplicator with a monetary gift I'd sent him, and I was horrified to realize that he was copying games and giving them to his friends. To him, it wasn't stealing; it was sharing. A generational shift in culture and technology meant that the game we'd poured our blood and treasure in would likely be pirated from its first days not just by the professional thieves, but also by everyday end users. At the time, no publisher was doing effective checking to ensure ownership of a PC game was legitimate. Valve would need to implement an authentication scheme.\nAt around this time, we caught a lucky break. For about a year, we'd been pushing Sierra on plans for seeding Half-Life with OEMs, the computer manufacturers who produced the hardware on which Half-Life could be played. For a time, we were even talking seriously with Intel about a version of the game that would highlight the features in a new chip they had under development. All of this came from the collective Microsoft experience about working with OEMs and seeding product in mass quantities to spur user adoption. Ultimately, the Intel play didn't happen but one of the programs that Sierra led involved providing a small portion of the game that they shipped as a trial disk called \"Day One.\"\nWhen we first realized what had happened, that Sierra had shipped some of the Half-Life code as Day One, Mike and I were furious. We quickly realized that we were at the mercy of whatever happened next. Fortunately, Day One became a phenomenon. Game developers LOVED it and began buzzing. Half-Life was going viral. The product was still a month or two from completion and no one had played the final game, but the early buzz for the first portion of the game was hugely promising.\nI continued to feed the Wall St. Journal reporter news about Half-Life, about its early reception, about what we were hearing from Day One users. It was all hugely positive.\nMike was still coding and he was exhausted. I was exhausted, and the team was antsy as we really didn't know how Half-Life would do in the marketplace. Finally, in late 1998, a few weeks before Christmas, we were ready to ship. Valve had a party where Mike broke open a pinata filled with candies and small toys.\nWhile the game was in manufacturing, final disks went to the gaming press. We waited. At some point, when Mike was in the shower, I felt overwhelmed by anxiety and asked with a worried tone to my voice, \"Is it really a good game?\" and his honest response, \"I don't know.\"\nGabe and Mike and I had all been through the shipping process at Microsoft, but being part of a large team where the company backed everything was completely different from being the funders of a company where we knew it was a one-shot deal. The game would either be a hit or it wouldn't, and for a short while, when the disks were being duplicated and the packaging printed and shipped, we simply wouldn't know. The first disks went straight to the key gaming press.\nAbout a year earlier, I had worked with Gabe to set the audacious goal of Half-Life winning at least three of the top industry Game of the Year awards. We very consciously thought through what it would take, including breakthrough technology, a compelling new angle, and broad industry support. It was going to be especially tough for a game that some insiders initially dismissed as \"Microsoft developers building on id's technology.\"\nWithin a few weeks, Half-Life won the first of more than 50 Game of the Year awards. It had never happened before. Shortly before Christmas, the Wall St. Journal article came out with the headline, \"\nStorytelling Computer Game Becomes a Big Hit for Valve.\"\nIn the article, Sierra as our publisher was barely mentioned. That was an explicit strategy of ours — since we were funding the development, we wanted Half-Life to be known as a Valve game, not a Sierra Studios game.\nA few weeks before Christmas, we were all exhausted. Some members of the team took vacation, but most continued showing up, almost in a daze, as we moved from tight pre-production intensity to the purgatory of Wait and See. We hadn't seen any sales figures. At one point, just after the game had shipped and we started seeing feedback online about how awful the authentication system was, Mike was yelling. It turned out that when someone complained about the authentication, Mike called the person back directly, challenging them and asking for sales verification. None of the people Mike contacted who complained early on had paid for the product. Mike was mad and tired but also vindicated.\nThe Game of the Year honors kept coming in, and we were optimistic that the great reception we were getting from industry influentials would ultimately translate into financial success for the company. I started working feverishly on post-launch marketing strategies, which mostly involved amplifying Half-Life's success and making sure retailers were armed with sales data and point of sale materials so customers could find it. I had purchased the web site GameoftheYear.com and we launched it with all of the material about the Game of the Year honors Half-Life was winning, including from\nPC Gamer\nand\nComputer Gaming World\n, which then were the heavyweights in our industry.\nIn the meantime, Gabe and Mike's relationship had deteriorated. A huge part of this was the stress and the financial imbalance. Gabe had become the major funder, and Mike had essentially burned himself out doing the final critical coding work before Half-Life shipped. Where before we'd tried to shield the team from our collective anxiety, Mike's yelling at customers had unnerved some people. I found myself in a situation where the two founders were essentially not talking to each other and people were tiptoeing around wondering what was going on.\nThen, in January at a time when I was getting ready to focus on Next Steps, Sierra asked for a meeting. Essentially their message to us was \"thank you, the game's done great, we're moving on.\" They were pulling all marketing from Valve to focus on one of their next titles. Basically, their marketing at the time amounted to Launch and Leave, whereas we were trying to market a franchise-worthy game that we could build on for years to come.\nGabe and I were stunned; I was also furious. I knew that the marketing of Half-Life was only getting started. We'd done all of this hard work to earn Game of the Year honors with the idea that that would help us break out from the pack and it was time to capitalize on that effort with sustained marketing. At Microsoft, winning awards was always the start of a much larger process where we leveraged positive reviews to win customers over time.\nWith steel in my voice, I told the Sierra team that they were not pulling marketing dollars from Half-Life. They were going to re-release it in a Game of the Year Box, and they were going to support it with huge marketing spend or we were going to walk away from our agreement and tell the industry that had fallen in love with Valve how screwed up Sierra really was. At the end of the meeting, I was shaking. We were vulnerable, the partners were barely speaking, and life at home and in the office was tense.\nSierra relented and started working on the packaging for a new Game of the Year box. The icon on the front looked similar to an Academy Award. The basic idea was that for anyone walking cold into a game retailer, they would quickly see that Half-Life was the Game of the Year they couldn't ignore.\nBy early March, things at Valve were still very strained. In addition to ongoing communications and marketing work for Half-Life, I was working on developer strategies closely with Gabe and some of the other developers and Mike was spending less and less time at the office. At some point in the early Spring, Mike said to me, \"I want to leave Valve.\"\nI was in a panic. We hadn't made back the money we'd invested. The buzz was continuing to build, but we had a long way to go. I told Mike that we needed time to figure out a pathway out, as at that time, the value of our ownership stake was highly questionable. At the same time, I was also panicked because I'd read, for the first time, the contractual agreement between Sierra and Valve, and while I thought I'd understood the key terms Gabe and Mike had agreed to, there were several points I hadn't been aware of. Chief among them was that Sierra owned all of the intellectual property for Half-Life and held the exclusive option to publish Valve's next two games, all at a royalty rate for Valve of 15 percent. We would do all of the development work with an upfront royalty advance of $1 million for each of those games, and Sierra would get 85% of the revenue and all of the intellectual property. At the time, I knew development costs were approaching $5 million or more per game\nGiven the licensing deal we had with id for the game engine license, the lack of any ownership of our own IP, and the exclusive commitment for future game publishing rights, all I could see was Valve swimming in red ink for years to come.\nWe needed a different path forward.\nFortunately, one of the consequences of Valve's work on an authentication system was that our customers were registering with Valve directly,\nEarly on, we started to understand the benefit of what we'd inadvertently done. Instead of a situation where we had no idea who our customers were, we actually knew exactly who our customers were. It was unprecedented. Every Half-Life registration meant a customer contact directly in Valve's database.\nAdded to this, the previous year, Gabe had had the brilliant idea of recruiting a development team that had written one of the leading mods for id's huge hit Quake and now they were part of Valve's team. John Cook and Robin Walker were delightful Aussie additions to Valve. The game mod they'd written to run on top of id's Quake was quickly adapted to run on top of Half-Life. Essentially the game mod enabled a player to play a completely different game on top of the technology of Half-Life. In the case of Team Fortress, it was a multiplayer game where you could team up with your friends over the Internet in a team-based game where each of you played a unique and fun character.\nWhile the Half-Life buzz was continuing to build through word-of-mouth and the new marketing push, the additional buzz and enthusiasm that came as a result of Team Fortress was layered on top of everything else. Soon there were hundreds of thousands of people playing Team Fortress on top of Half-Life and Valve knew who each and every one of them were. We had a direct pipeline, bypassing Sierra, to our own customers.\nIn late Spring, Team Fortress, the Cook/Walker mod for the Half-Life engine was presented at E3, where it won Best Action Game and Best Online Game on behalf of Valve.\nThrough all of this, I continued to noodle about the best ways I could position Valve for long-term success. With the bad publishing deal in hand, I knew I had to work on multiple fronts.\nIf Mike and I were to leave, we needed to demonstrate value for Valve that wasn't tied directly to the Half-Life IP. We needed to renegotiate our deal with Sierra. And we needed to figure out a way to cap our royalties to id, so that Valve wouldn't be paying them a fee each time someone bought one of our future games.\nValve had already done a lot of work to customize the id engine code for our purposes, and we'd reached the point where for any next game, we'd either continue using and adapting that code base or we'd take the time to write new engine code ourselves from scratch.\nWith Gabe's OK, I reached out to the team at id, and we came to quick agreement on a capped deal.\nThe second step was to kick off steps to renegotiate our agreement with Sierra. I met with Valve's attorney, and the basic approach we took was to make clear that if Sierra was going to insist on keeping the original deal, then the Valve team would pivot to a completely different category and never publish a second game. Since Gabe and Mike had a ton of experience in other facets of software development, the threat was not idle. The bottom line was we weren't going to create games and take on all of the risk only to make other people rich.\nOne of my responsibilities in the mid-90s at Microsoft was overseeing the initial marketing for Expedia. I'd spent a lot of time with Josh, the person on my team who was tasked with laying out the market case. From that and other experience over the years, I knew a lot about how to scope and size the online opportunity for a completely new category. I got to work trying to figure out an online business opportunity that wasn't dependent on the Half-Life IP.\nInternally, we had rich experience to draw from. Gabe and Mike had a lot of experience with developers and with the developer marketplace, and at one time, I'd overseen Microsoft's PR outreach related to software tools for the developer community. In addition, I knew the games business inside and out, and I'd been part of teams within Microsoft that were completely focused on the emerging online opportunity made possible by the Internet.\nBy the summer of 1999, Mike was researching trawler yachts, I was immersed in figuring out Valve's potential business opportunities, and Gabe was doing deep thinking, leading the team and communicating with customers. In the meantime, because of the way Gabe and Mike had structured the ownership, where employees could earn equity over time, Mike's and my ownership stake was effectively shrinking.\nFinally, at some point, I realized that the only way to prove the worth of some of the ideas I was focused on was to write them up and get an offer. Without that, I could make the case that Valve was worth a lot of money or nothing. And I knew Gabe could make that same case.\nWith Gabe's buy-in, I decided to pitch Amazon on a new business opportunity. I'd known about Amazon for a long time as one of my dear friends from Microsoft had been hired on as its original marketing lead. She had since left, but I'd followed the company closely. At the time, it was headquartered in South Seattle in an imposing building just South of the i-90 freeway exchange.\nIn a nine-page document, I proposed that Valve and Amazon team up to create a new online entertainment platform. I scaled the business opportunity within four years at $500 million dollars. The gist of the idea was to create a made-for-the-medium platform that would bring users together in a sticky, compelling entertainment experience, with digital and offline content sales. I wanted Amazon's financial backing as a way to gain first mover advantage against Microsoft and Electronic Arts, then the major PC games players. I didn't see a role for Sierra. If pushed, we wouldn't create any new games ourselves, and instead would team with outside developers so that they could distribute content not subject to an 85% publishing fee. At the time, I considered it an act of rebellion against the traditional publishing dynamic where independent developers took on huge risk, and the big publishing houses reaped the rewards.\nWith Gabe's OK, I sent the document over to Amazon. Within a short period of time I had a response. \"Let's meet.\"\nWhen I arrived, the Amazon Vice President I met with was super friendly. He was familiar but I couldn't place him. Then he said, \"You don't remember me, but you interviewed me at Microsoft.\"\nI realized I must not have hired him, and for the first time, started getting uneasy about how things would go. He reminded me gently that when Amazon was pretty much in its infancy and a company I knew of mostly because of my friend, I had interviewed him for a position at Microsoft. He was interviewing at Microsoft because the company he worked for had just done a major layoff. Our division was pretty much in a temporary hiring freeze and he had a background in retail, so I suggested he look into a tiny company named Amazon. By the time we met again, he'd been there several years.\nWe had a great discussion, and a couple of weeks later, a champagne bottle appeared at Valve's door.\nIt was exhilarating and scary at the same time. We had an offer from Amazon for a minority stake, but the dynamics within the company were tricky. Amazon could help propel Valve to the next level, but the partnership would not be without costs. Valve's culture was still evolving. A partnership with a major outside player could help but it could also hurt what we'd all built.\nIt was after the Amazon offer that Mike revealed to Gabe that he wanted to leave. With an offer in-hand, it didn't take long for us to figure out the outline of a deal.\nUltimately, Mike and I gave up ownership to start the next chapter of our lives. The structure of the deal meant that we would be vested in Valve's success over the next five years. I knew the opportunity that lay ahead. I also saw huge risks. The Sierra deal might collapse publicly, employees might get spooked, we might not be able to actually get the IP back, and with any online endeavor, there would be huge new risks.\nWithin several months, Mike and I left Seattle for a new adventure on San Juan Island and Whistler B.C. I continued to make myself available to Valve. But for the most part, I shed my work identity and started on new projects, including a passion for protecting Washington's resident orca whales.\nIt was up to Gabe and the Valve team to move the business forward.\nSeveral years after Valve, I went to work for the Bill & Melinda Gates Foundation, and from there, took on another CMO role when Mike started a new partnership and business focused on photo editing. That company, Picnik, sold to Google in 2010.\nI continued to see the Valve team intermittently through the years, and even worked with the team on a\nstory\nthat appeared in the New York Times in 2012 about Valve's highly unusual flat culture. When the Half-Life IP was secured and owned by Valve, the team sent us a small trophy with the etching \"Welcome back Gordon.\" Gordon was the key protagonist in the Half-Life adventure.\nIn 2016, Mike and I separated and then divorced. In 2018, I joined Gabe and some friends from Valve on a cruise on Gabe's yacht around the islands of Japan.\nSome ten years after Half-Life's release, PC Gamer named it the Best PC Game Ever. In a separate story, PC Gamer also named Half-life the Best Marketed Game Ever, with special credit to whoever came up with the Game of the Year box and retail push. Valve's online platform Steam is now an industry phenomenon, with annual sales in the billions of dollars.\nAs I look back on the huge success Valve has become, I'm proud of what the team accomplished. I'm also proud of the work I did while recognizing that my biggest contributions to Valve's business went largely unnoticed and unrecognized within the industry. Part of that was due to the bro culture of the software business, part of it was that I receded to support my husband in a partnership where he was effectively the lesser partner, and part of it was that women, especially in tech, often seem to disappear when the story gets told.\nI was hugely disappointed when Valve released a video in 2023 about the creation of Half-Life where one of the people interviewed, Karen Laur, a wonderfully talented texture artist, talked about the isolating experience of being a woman at Valve and essentially said that the only other woman during her tenure there was an office manager. I understood why she felt as she did, but the senior Valve team knows better. Watching the\nvideo\n, I felt like my place in Valve's history had been completely erased.\nI know that Valve wouldn't have been successful without Mike. It wouldn't have been successful without Gabe. And it wouldn't have been successful without me. A friend of mine who knows the full story once said to me, \"you were a founding partner\" and in hindsight, I agree. From the beginning, I invested time, treasure and industry expertise to make the company a huge succes\nAnd it is.\nThe author celebrating the holidays along Route 66 with Scott.\nMonica Harrington lives in Bend, Oregon, with Scott Walker and their spaniel Johnnie Walker Black and White.\nEditorial note 8/21: The author updated some details regarding the authentication scheme (thanks Mike) and the name of the mod created by Robin Walker and John Cook, which ultimately shipped as Team Fortress Classic.\nEditorial note 9/6: A careful reader noticed that I said Team Fortress was built as a mod for Doom, when in fact TF was a mod for Quake. Of course. This has been fixed.\nEditorial note 9/7: Karen Laur sent me a note essentially saying that the video (as edited) didn't make clear she was talking about her experience in her first year (when I was still working full-time at Microsoft, and contributing to Valve via email and direct interaction with Gabe and Mike.) Thanks for the clarifying note Karen.\nEditorial note 9/16: Some readers seem confused about the term \"lesser partner\" which is the reality when, in a partnership, one partner has more ownership and voting rights than the other.","images":["https://miro.medium.com/v2/resize:fit:700/1*bEHDk45U7xgg4Lr08gufYA.jpeg","https://miro.medium.com/v2/resize:fill:88:88/1*EoXOOMWLEiPwBBaYA1HQXA.jpeg","https://miro.medium.com/v2/resize:fit:700/1*jWiR8ZvcwMIONhIlPvRemQ.jpeg","https://miro.medium.com/v2/resize:fit:700/1*EIL09dzr3slNwMP8ZX0LrA.jpeg"]}..
       """
    async with httpx.AsyncClient() as client:
        title, summary = await get_gpt_summary_and_title(client, article_content)
        print("Title:", title)
        print("Summary:", summary)


if __name__ == '__main__':
    asyncio.run(main())
