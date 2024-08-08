# from pymongo import MongoClient
#
# # 创建MongoClient对象，连接到本地MongoDB实例
# client = MongoClient("mongodb://localhost:27017/")
#
# db = client['articles']  # 选择数据库

from pymongo import MongoClient

# 创建MongoClient对象，连接到本地MongoDB实例
client = MongoClient("mongodb://localhost:27017/")
db = client['articles']  # 选择数据库
collection = db['article_data']  # 选择集合

def insert_article_data(article_data):
    try:
        collection.insert_one(article_data)
        print("数据插入成功")
    except Exception as e:
        print(f"数据插入失败: {e}")
