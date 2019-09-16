import configparser

db_config = configparser.ConfigParser()
db_config.read('config/db_config.ini')

item_config = configparser.ConfigParser()
item_config.read('config/item_config.ini')

__all__ = ['db_config', 'item_config']