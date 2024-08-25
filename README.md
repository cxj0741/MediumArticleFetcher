# MediumArticleFetcher功能
爬取medium上的数据
# 环境准备
## git
## python3
# 启动项目流程
## git clone git@github.com:XZXY-AI/MediumArticleFetcher.git
## 进入文件夹：cd MediumArticleFetcher
## 安装虚拟环境所需要的包：sudo apt install python3-venv
## 构建虚拟环境：python3 -m venv venv
## 激活虚拟环境：source venv/bin/activate
## pip install -r requirements.txt,安装依赖
## 下载playwright的浏览器：playwright install
## 安装playwright所需要的库：playwright install-deps
## sudo apt update， sudo apt install xvfb通过这俩个命令安装虚拟显示服务器
## xvfb-run -a python api.py  启动服务