from pymongo import MongoClient
from pymongo.errors import BulkWriteError
from logger_config import logger

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

def insert_articles_batch(article_data_list):
    if article_data_list:
        try:
            result = collection.insert_many(article_data_list, ordered=False)  # 不按顺序插入
            logger.info(f"成功插入了 {len(result.inserted_ids)} 条记录")
        except BulkWriteError as bwe:
            logger.error(f"批量插入数据失败: {bwe.details}")
        except Exception as e:
            logger.error(f"批量插入数据失败: {e}")
