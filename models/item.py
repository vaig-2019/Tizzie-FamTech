import logging
import re
import math
from models import mongo_database
from config import item_config

logger = logging.getLogger(__name__)

v_color      = item_config['VIETNAMESE_ATTRIBUTE']['COLOR']
v_memory     = item_config['VIETNAMESE_ATTRIBUTE']['MEMORY']
v_phone      = item_config['VIETNAMESE_ATTRIBUTE']['PHONE']


def get_products_with_prices(cursor):
    for item in cursor:
        logger.debug("item: " + str(item))
        price_cursor = mongo_database['item_prices'].find({"url": item['cheapest_item_url']}).limit(1)
        for price in price_cursor:
            item['item_price'] = price
        yield item    

def search_products(category_filter=None, attribute_filter=None, price_filter=None, other_filters=None):
    """
    Return list of productss by AND filters. Each filter is a dictionary-like object
    Example of category filter: {"category": "mobile"}
    Example of attribute filter: {"color": "blue", "capacity": "16GB"}
    Example of price filter: {"min_price": 4000000, "max_price": 6000000}
    Example of other filters: {"min_rating": 4.0}
    """
    
    query_condition = []
    if category_filter:
        query_condition.append({'categories': category_filter['category']})

    if attribute_filter:
        if 'color' in attribute_filter:
            query_condition.append({'available_configs.' + v_color : attribute_filter['color']})
        if 'capacity' in attribute_filter:
            query_condition.append({'available_configs.' + v_memory : attribute_filter['capacity']})

    if price_filter:
        if 'min_price' in price_filter:
            query_condition.append({'cheapest_price' : {'$gte' : price_filter['min_price']}})
        if 'max_price' in price_filter:
            query_condition.append({'cheapest_price' : {'$lte' : price_filter['max_price']}})

    if other_filters:
        if 'min_rating' in other_filters:
            query_condition.append({'user_ratings.average' : {'$gte' : other_filter['min_rating']}})

    item_cursor = mongo_database['items'].find({'$and' : query_condition})
    return [item for item in get_products_with_prices(item_cursor)]

def search_products_by_name(product_name):
    """
    Return list of products by name, search result must be case-insensitive
    """

    item_collection = mongo_database['items']
    product_name_regex = re.compile(product_name, re.I)
    item_cursor = item_collection.find({"name" : {"$regex" : product_name_regex}})
    return [item for item in get_products_with_prices(item_cursor)]

def get_item_info(url):
    pass

def get_item_price_history(url):
    pass

def get_exact_product(product_name):
    """
    Return exacpt item with that product name
    """

    item_collection = mongo_database['items']
    product_name_regex = re.compile('\\b' + product_name + '\\b', re.I)
    item_cursor = item_collection.find({"name" : {"$regex" : product_name_regex}}).limit(1)

    for item in get_products_with_prices(item_cursor):
        return item

    return None


if __name__ == '__main__':
    import logging.config
    DEFAULT_LOGGING = {
        'version': 1,
        'disable_existing_loggers': False,
        'formatters': { 
            'standard': { 
                'format': '[%(asctime)s] p%(process)s {%(pathname)s:%(lineno)d} %(levelname)s - %(message)s'
            },
        },
        'loggers': {
            '': {
                'level': 'DEBUG',
                'handlers': ['default'],
                'propagate': True
            },
        },
        'handlers': { 
            'default': { 
                'level': 'DEBUG',
                'formatter': 'standard',
                'class': 'logging.StreamHandler'
            },
        }
    }
    logging.config.dictConfig(DEFAULT_LOGGING)

    # print(get_cheapest_product('iphone xs max'))
    # print(search_products_by_name('iphone'))
    print(search_products(price_filter={'min_price': 3000000, 'max_price': 7000000}, attribute_filter={'color': 'Xanh'} ))
    # for item in mongo_database['items'].find():
        # logger.debug(item)