# MediumArticleFetcher功能
爬取medium上的数据
# 环境准备
1. git
2.  python3
# 启动项目流程
1. git clone git@github.com:XZXY-AI/MediumArticleFetcher.git
2. 进入文件夹：cd MediumArticleFetcher
3. 安装虚拟环境所需要的包：sudo apt install python3-venv
4. 构建虚拟环境：python3 -m venv venv
5. 激活虚拟环境：source venv/bin/activate
6. 安装依赖：pip install -r requirements.txt
7. 下载playwright的浏览器：playwright install
8. 安装playwright所需要的库：playwright install-deps
9. 通过这俩个命令安装虚拟显示服务器：sudo apt update， sudo apt install xvfb
10. 启动服务：xvfb-run -a python api.py  