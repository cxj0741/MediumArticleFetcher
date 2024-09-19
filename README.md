# MediumArticleFetcher功能
爬取medium上的数据
# 环境准备
1. git
2.  python3

# 启动项目流程

```bash
# 克隆项目
git clone git@github.com:XZXY-AI/MediumArticleFetcher.git

# 进入项目文件夹
cd MediumArticleFetcher

# 更新本地的软件包
sudo apt update

# 安装虚拟环境所需的包
sudo apt install python3-venv

# 构建虚拟环境
python3 -m venv venv

# 激活虚拟环境
source venv/bin/activate

# 安装项目依赖
pip install -r requirements.txt

# 安装 Playwright 所需的系统库
playwright install-deps

# 下载 Playwright 浏览器
playwright install

# 安装虚拟显示服务器
sudo apt install xvfb

# 启动服务
xvfb-run -a python api.py
```
# 使用不同的谷歌账户进行登录
1. 首先需要保证部署机器在谷歌浏览器的medium是一种登录状态，没有登录需要注册并且登录
2. 在本地机器的谷歌浏览器地址栏输入chrome://version/并按回车，找到 "Profile Path" 一行，这一行显示了你当前使用的 Chrome 配置文件的路径
3. 在项目根路径下找到get_state.py，将user_data_dir=r"你的文件地址"
4. （可选：先删除本地的state.json文件），执行get_state.py
5. 注意，执行get_state.py的时候一定要关闭本地的谷歌浏览器，不然会文件冲突

# api使用
```
# 获取文章数据(get方法)，使用实例
基础地址：http://localhost:5000/api/parse_article
查询参数：url=<文章链接>
完整实例：http://localhost:5000/api/parse_article?url=https://medium.com/@monicah428/the-early-days-of-valve-from-a-woman-inside-bf80c6b47961?source=explore---------6-108--------------------f7f17187_eea2_4818_8b75_4d205f273321-------15

```