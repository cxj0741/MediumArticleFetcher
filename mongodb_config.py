from pymongo import MongoClient

# 创建MongoClient对象，连接到本地MongoDB实例
client = MongoClient("mongodb://localhost:27017/")

db = client['pdf_database']  # 选择数据库