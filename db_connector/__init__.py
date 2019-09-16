from pymongo import MongoClient
from config import *

__mongo_client = MongoClient(host=db_config['DB_CONNECTION']['HOST'],
                           port=int(db_config['DB_CONNECTION']['PORT']),
                           username=db_config['DB_CONNECTION']['USERNAME'],
                           password=db_config['DB_CONNECTION']['PASSWORD'])

mongo_database = __mongo_client[db_config['DB_CONNECTION']['DATABASE']]

__all__ = ["mongo_database"]