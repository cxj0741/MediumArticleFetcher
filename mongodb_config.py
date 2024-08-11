from pymongo import MongoClient
from pymongo.errors import BulkWriteError
from logger_config import logger

# 使用URL编码的连接字符串
connection_string = "mongodb+srv://webcrawler:nSgnzTzGVq%2BuIF@webcrawler.mongocluster.cosmos.azure.com/?tls=true&authMechanism=SCRAM-SHA-256&retrywrites=false&maxIdleTimeMS=120000"

# client = MongoClient("mongodb://localhost:27017/")
client = MongoClient(connection_string)
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
# # 测试数据
# single_document = {"name": "Alice", "age": 30, "city": "New York"}
# batch_data = [
#     {"name": "Bob", "age": 25, "city": "Los Angeles"},
#     {"name": "Charlie", "age": 35, "city": "Chicago"}
# ]
#
# # 插入单个文档
# print("插入单个文档测试:")
# insert_article_data(single_document)
#
# # 批量插入数据
# print("批量插入数据测试:")
# insert_articles_batch(batch_data)
#
# # 查询并打印所有文档
# try:
#     print("查询所有文档:")
#     for doc in collection.find():
#         print(doc)
# except Exception as e:
#     print(f"查询失败: {e}")