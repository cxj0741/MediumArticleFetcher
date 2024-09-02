# 删除重复的url
from pymongo import MongoClient
from urllib.parse import urlparse, urlunparse

# 去除查询参数
def remove_query_params(url):
    """
    移除 URL 中的查询参数。
    """
    parsed_url = urlparse(url)
    cleaned_url = urlunparse(parsed_url._replace(query=""))
    return cleaned_url

# MongoDB 连接
connection_string = "mongodb+srv://webcrawler:nSgnzTzGVq%2BuIF@webcrawler.mongocluster.cosmos.azure.com/?tls=true&authMechanism=SCRAM-SHA-256&retrywrites=false&maxIdleTimeMS=120000"
client = MongoClient(connection_string)
db = client['articles']  # 选择数据库
collection = db['article_data']  # 选择集合

# 删除重复数据
def delete_duplicates():
    # 以 `clean_url` 为键，使用 `find` 和 `aggregate` 找出重复的文档
    pipeline = [
        {
            "$group": {
                "_id": {"clean_url": {"$substr": ["$url", 0, {"$indexOfCP": ["$url", "?"]}]}}, # 通过清理后的 URL 分组
                "firstId": {"$first": "$_id"},  # 保留第一条的 _id
                "allIds": {"$push": "$_id"},  # 获取所有的 _id
                "count": {"$sum": 1}  # 统计数量
            }
        },
        {
            "$match": {
                "count": {"$gt": 1}  # 仅保留有重复的组
            }
        }
    ]

    duplicates = collection.aggregate(pipeline)

    delete_count = 0

    for doc in duplicates:
        all_ids = doc["allIds"]
        first_id = doc["firstId"]
        all_ids.remove(first_id)  # 从列表中移除第一条

        # 删除所有其他重复的文档
        result = collection.delete_many({"_id": {"$in": all_ids}})
        delete_count += result.deleted_count
        print(f"Deleted {result.deleted_count} duplicates for URL: {doc['_id']['clean_url']}")

    print(f"Total duplicates deleted: {delete_count}")

delete_duplicates()
