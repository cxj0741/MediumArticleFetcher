from pymongo import MongoClient

# 替换为你的连接字符串
connection_string = "mongodb+srv://webcrawler:nSgnzTzGVq+uIF@webcrawler.mongocluster.cosmos.azure.com/?tls=true&authMechanism=SCRAM-SHA-256&retrywrites=false&maxIdleTimeMS=120000"

client = MongoClient(connection_string)

# 访问特定的数据库
db = client['your_database_name']

# 访问特定的集合
collection = db['your_collection_name']

# 示例操作：打印所有文档
for doc in collection.find():
    print(doc)
