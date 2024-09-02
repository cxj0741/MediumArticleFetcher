import hashlib

from pymongo import MongoClient
from pymongo.errors import BulkWriteError
from logger_config import logger
from urllib.parse import urlparse, urlunparse
from bson.regex import Regex

# 去除查询参数
def remove_query_params(url):
    """
    移除 URL 中的查询参数。
    """
    parsed_url = urlparse(url)
    cleaned_url = urlunparse(parsed_url._replace(query=""))
    return cleaned_url

# 使用URL编码的连接字符串
connection_string = "mongodb+srv://webcrawler:nSgnzTzGVq%2BuIF@webcrawler.mongocluster.cosmos.azure.com/?tls=true&authMechanism=SCRAM-SHA-256&retrywrites=false&maxIdleTimeMS=120000"

# client = MongoClient("mongodb://localhost:27017/")
client = MongoClient(connection_string)
db = client['articles']  # 选择数据库
collection = db['article_data']  # 选择集合

# 插入单条数据
def insert_article_data(article_data):
    try:
        collection.insert_one(article_data)
        print("数据插入成功")
    except Exception as e:
        print(f"数据插入失败: {e}")

# 根据url生成唯一的_id
def generate_id_from_url(url):
    """
    根据去除查询参数的 URL 生成唯一的 _id。
    """
    cleaned_url = remove_query_params(url)
    return hashlib.md5(cleaned_url.encode('utf-8')).hexdigest()


# 批量插入，即使某一条插入错误也不会影响其他，会尽可能的将数据进行插入
def insert_articles_batch(article_data_list):
    """
    批量插入文章数据，跳过重复的 _id 并继续插入不同的文档
    """
    if article_data_list:
        for article in article_data_list:
            # 使用清理后的 URL 生成 _id
            # todo 后续可以将这个去除查询参数提前
            article['_id'] = generate_id_from_url(article['url'])

        try:
            result = collection.insert_many(article_data_list, ordered=False)
            logger.info(f"成功插入了 {len(result.inserted_ids)} 条记录")
        except BulkWriteError as bwe:
            # 获取重复错误的文档索引
            duplicate_ids = []
            for error in bwe.details['writeErrors']:
                if error['code'] == 11000:  # 11000 表示 Duplicate Key Error
                    duplicate_ids.append(error['op']['_id'])

            logger.warning(f"批量插入时遇到 {len(duplicate_ids)} 条重复 _id，跳过这些文档")

            # 过滤掉重复的文档
            remaining_data = [article for article in article_data_list if article['_id'] not in duplicate_ids]

            if remaining_data:
                try:
                    result = collection.insert_many(remaining_data, ordered=False)
                    logger.info(f"成功插入了 {len(result.inserted_ids)} 条非重复记录")
                except Exception as e:
                    logger.error(f"在处理剩余文档时插入失败: {e}")
            else:
                logger.info("没有剩余的文档需要插入")
        except Exception as e:
            logger.error(f"批量插入数据失败: {e}")


# 新增函数：获取文章数据
def get_articles(page=1, limit=10, search=''):
    """
    获取文章数据，支持分页和搜索
    """
    skip = (page - 1) * limit

    pipeline = [
        {
            "$match": {
                "$or": [
                    {"title": Regex(search, 'i')},
                    {"author": Regex(search, 'i')}
                ]
            }
        },
        {
            "$addFields": {
                "likesNumeric": {"$toInt": "$likes"}
            }
        },
        {
            "$sort": {"likesNumeric": -1}
        },
        {
            "$skip": skip
        },
        {
            "$limit": limit
        }
    ]

    articles = list(collection.aggregate(pipeline))
    total = collection.count_documents({})

    return {"articles": articles, "total": total}

