import re
import json
import logging
import unittest
from db_connector import mongo_database
from config import item_config
import db_connector.google_place_api as gp_api

logger = logging.getLogger(__name__)

v_color      = item_config['VIETNAMESE_ATTRIBUTE']['COLOR']
v_memory     = item_config['VIETNAMESE_ATTRIBUTE']['MEMORY']
v_phone      = item_config['VIETNAMESE_ATTRIBUTE']['PHONE']


class Phone:
    def __init__(self, name, url, color: list, memory: list, nearest: dict):
        self.name = name
        self.url = url
        self.color = color
        self.memory = memory
        self.nearest = nearest


# Mapping function
def to_phone_object(phone_item):
    location_list = phone_item['locations']
    nearest_location, nearest_distance, nearest_duration = gp_api.get_nearest_place(location_list)
    nearest = {}
    nearest['location'] = nearest_location
    nearest['distance'] = nearest_distance
    nearest['duration'] = nearest_duration

    return Phone(phone_item['name'],
                 phone_item['url'],
                 phone_item['available_configs'][v_color] ,
                 phone_item['available_configs'][v_memory],
                 nearest)


def phone_obj_to_list(phone_obj):
    return {"name": phone_obj.name,
            "url": phone_obj.url,
            "available_configs": {
                v_color: phone_obj.color,
                v_memory: phone_obj.color
            },
            "nearest": phone_obj.nearest}

# Get phone information
def get_info_phone(name, color=None, memory=None):
    collection = mongo_database["items"]

    # for item in collection.find():
    #     logger.debug(item)

    # Set condition for query to database
    condition_query = {}

    # Check attribute exist on item
    condition_query['available_configs.' + v_color] = {"$exists": True}
    condition_query['available_configs.' + v_memory] = {"$exists": True}
    condition_query['locations'] = {"$exists": True}

    # Check type item is phone
    find_phone_condition = re.compile(v_phone, re.I)
    find_name_condition = re.compile(name, re.I)
    find_phone_name_condition = [
        {'name' : {'$regex' : find_phone_condition}},
        {'name' : {'$regex' : find_name_condition}}
    ]

    # Query follow name, color and memory size
    condition_query['$and'] = find_phone_name_condition
    if color is not None:
        find_color_condition = re.compile(color, re.I)
        condition_query['available_configs.' + v_color] = {"$regex" : find_color_condition}
    if memory is not None:
        memory_number = [int(s) for s in memory if s.isdigit()]
        memory_number = ''.join(str(e) for e in memory_number)
        if(len(memory_number)):
            find_memory_condition = re.compile(memory_number[0], re.I)
            condition_query['available_configs.' + v_memory] = {"$regex" : find_memory_condition}

    # Query and sort
    cursor = collection.find(condition_query).sort("name")
    phone_result = []
    for item in cursor:
        phone_result.append(item)

    # Return a list of Phone object
    if len(phone_result) == 0:
        return None
    else:

        map_phone_object = list(map(to_phone_object, phone_result))
        return (map_phone_object)

def get_item_by_price_range(category, range_left, range_right):
    collection_item_prices = mongo_database["item_prices"]
    collection_items = mongo_database["items"]

    query_Item_price_table = {"price_history.0.final_price": {"$gte": range_left, "$lte": range_right}}

    cursor_item_prices = collection_item_prices.find(query_Item_price_table)
    phone_item_prices = []
    for item in cursor_item_prices:
        phone_item_prices.append(item['title'])

    # query_items_by_name = {"name" : phone_result[0]}
    query_items_by_name = {"name" : {"$in" : phone_item_prices}}

    cursors_items = collection_items.find(query_items_by_name)

    # logger.debug(cursors_item)
    phone_result = []
    for item in cursors_items:
        phone_result.append(item['user_reviews'])

    return phone_result

    # return phone_result

    # # Return a list of Phone object
    # if len(phone_result) == 0:
    #     return None
    # else:

    #     map_phone_object = list(map(to_phone_object, phone_result))
    #     return map_phone_object.category


def get_suggest_phone(name, color=None, memory=None):
    result = get_info_phone(name=name, color=color, memory=memory)
    for item in result:
        print(item.nearest)

    # logger.debug(result)

    while result is None:
        name = name.rsplit(' ', 1)[0]
        result = get_info_phone(name=name, color=None, memory=None)

    return result

def get_phone_option(option, name):
    collection = mongo_database["items"]

    # Set condition for query to database
    condition_query = {}

    # Check attribute exist on item
    condition_query['available_configs.' + v_color] = {"$exists": True}
    condition_query['available_configs.' + v_memory] = {"$exists": True}
    condition_query['locations'] = {"$exists": True}

    # Check type item is phone
    find_phone_condition = re.compile(v_phone, re.I)
    find_name_condition = re.compile(name, re.I)
    find_phone_name_condition = [
        {'name': {'$regex' : find_phone_condition}},
        {'name': {'$regex' : find_name_condition}}
    ]

    # Query follow name
    condition_query['$and'] = find_phone_name_condition

    # Query and sort
    cursor = collection.find(condition_query).sort("name")
    phone_result = []
    for item in cursor:
        phone_result.append(item)
    if len(phone_result) == 0:
        return None
    else:
        # color_list = list(set(phone.color for phone in phone_result))
        map_phone_object = list(map(to_phone_object, phone_result))
        if (option == 'color'):
            color_list = list(set(phone.color[0].lower() for phone in map_phone_object))
            return color_list
        if (option == 'memory'):
            memory_list = list(set(phone.memory[0].lower() for phone in map_phone_object))
            return memory_list

def get_suggest_option_by_phone_name(option,product_name):
    list_phone_option = get_phone_option(option, product_name)

    # logger.debug(list_phone_option)

    if(list_phone_option == None):
        return None
    else:
        if (option == 'color'):
            if ("nhiều màu" in list_phone_option) and (len(list_phone_option) > 1):
                colors.remove('nhiều màu')

        leng = len(list_phone_option)
        i = 0

        suggest_phone_option = []

        if leng < 3 :
            suggest_phone_option = [list_phone_option[i] for i in range(leng)]
            text = ' hay '.join(suggest_phone_option)
            return text

        else:
            suggest_phone_option = random.sample(list_phone_option, k = 3)
            text = ' hay '.join(suggest_phone_option)
            return text

def get_location_by_phone_name(product_name):
    list_phone = get_suggest_phone(product_name)

    return list_phone[0].nearest, list_phone[0].url

def get_product_detail(user_input_name, item_filter=None, exact=True, multi=False):
    if not user_input_name:
        return None
    user_input_name = user_input_name.strip().replace('+', r'\+')
    if not user_input_name:
        return None

    partitions = user_input_name.partition(' ')
    last_words = partitions[2].strip()

    full_re = user_input_name if not exact else r'^' + user_input_name + r'$'
    brand_re = partitions[0] if not exact else r'^' + partitions[0] + r'$'
    product_re = '' if not last_words else (last_words if not exact
                                            else r'^' + last_words + r'$')
    if product_re:
        condition = {
            "$or" : [
                {
                    "product" : re.compile(full_re, re.I)
                },
                {
                    "brand": re.compile(brand_re, re.I),
                    "product": re.compile(product_re, re.I)
                }
            ]
        }
    else:
        condition = {
            "$or" : [
                { "product" : re.compile(full_re, re.I) },
                { "brand": re.compile(brand_re, re.I) }
            ]
        }

    return get_product_detail_internal(condition, item_filter, multi)

def get_product_detail_icase(brand, name, item_filter=None, multi=False):
    return get_product_detail_internal({
        "brand": brand,
        "product": re.compile('^' + name.replace('+', r'\+') + '$', re.I)
    }, item_filter, multi)

def get_product_detail_internal(product_cond, item_filter=None, multi=False):
    item_cond =  { "$and" : [{"$eq":[ {"$toLower": "$$spec_product"},
                                      "$productname" ] },
                             {"$eq": ["$$spec_brand", "$brand"] } ] }
    if item_filter:
        item_cond = {
            "$and": [
                item_cond,
                item_filter
            ]
        }

    query = [
        {
            "$match": product_cond
        },
        {
            "$lookup": {
                "from": "items",
                "let": {"spec_product": "$product", "spec_brand": "$brand"},
                "pipeline":
                [
                    {
                        "$match":{"$expr": item_cond }
                    },
                    {
                        "$project": {
                            "_id": 0,
                            "url": 1,
                            "latest_price": 1,
                            "image": { "$arrayElemAt": ["$original_image_urls", 0] },
                            "user_ratings": 1,
                            "user_reviews": 1,
                        }
                    },
                    {
                        "$sort": {"latest_price.final_price" : 1}
                    },
                    {
                        "$group": {
                            "_id": None,
                            "url": { "$first": "$url" },
                            "lowest_price": { "$first": "$latest_price.final_price" },
                            "highest_price": { "$last": "$latest_price.final_price" },
                            "image": { "$first": "$image" },
                            "user_ratings": { "$first": "$user_ratings" },
                            "user_reviews": { "$first": "$user_reviews" },
                        }
                    }
                ],
                "as": "items"
            }
        },
        {
            "$unwind": "$items"
        },
        {
            "$lookup": {
                "from": "item_prices",
                "localField": "items.url",
                "foreignField": "url",
                "as": "item_prices"
            }
        },
        {
            "$unwind": "$item_prices"
        },
        {
            "$lookup": {
                "from": "reviews",
                "let": {"spec_product": "$product"},
                "pipeline":
                [
                    {
                        "$match":{"$expr":{
                            "$eq":[
                                {"$toLower": "$$spec_product"},
                                "$product"
                            ]
                        }}
                    },
                ],
                "as": "review_articles"
            }
        },
        {
            "$lookup": {
                "from": "video_reviews",
                "let": {"spec_product": "$product"},
                "pipeline":
                [
                    {
                        "$match":{"$expr":{
                            "$eq":[
                                {"$toLower": "$$spec_product"},
                                "$product"
                            ]
                        }}
                    },
                    {
                        "$project": {
                            "_id": 0,
                            "title": "$snippet.title",
                            "url": { "$concat" : [
                                "https://www.youtube.com/watch?v=",
                                "$snippet.resourceId.videoId"
                            ]},
                        }
                    },
                ],
                "as": "review_videos"
            }
        },
        {
            "$project": {
                "_id": 0,
                "name": { "$concat" : [ "$brand", " ", "$product" ] },
                "product": 1,
                "brand": 1,
                "image": "$items.image",
                "specs": { "$concat": [ "$Platform.Chipset", ", ", "$Memory.Internal" ] },
                "screen_size": { "$concat": [{"$toString": "$Display.Diagonal"}, "\""] },
                "chipset": "$Platform.Chipset",
                "memory": "$Memory.Internal",
                "main_camera": { "$ifNull": [
                    "$Main Camera.Single", { "$ifNull": [
                        "$Main Camera.Dual", { "$ifNull": [
                            "$Main Camera.Triple", {"$ifNull": [
                                "$Main Camera.Quad", "" ]} ]} ]} ]},
                "selfie_camera": { "$ifNull": [
                    "$Selfie camera.Single", { "$ifNull": [
                        "$Selfie camera.Dual", { "$ifNull": [
                            "$Selfie camera.Triple", {"$ifNull": [
                                "$Selfie camera.Quad", "" ]} ]} ]} ]},
                "battery": { "$concat": [{"$toString": "$Battery.Capacity"}, " mAh"] },
                "rating": { "$cond" : [ { "$eq" : [ "$items.user_ratings.average", float('nan') ] },
                                        0,  "$items.user_ratings.average" ] },
                "url": "$items.url",
                "user_reviews": "$items.user_reviews",
                "lowest_price": "$items.lowest_price",
                "highest_price": "$items.highest_price",
                "price_history": "$item_prices.price_history",
                "review_articles.title": 1,
                "review_articles.url": 1,
                "review_videos.title": 1,
                "review_videos.url": 1
            }
        }
    ]

    collection = mongo_database["product_specs"]
    cursor = collection.aggregate(query)

    if multi:
        return [prod for prod in cursor]
    else:
        return next(cursor, None)



import pprint
if __name__ == '__main__':
    import logging.config
    DEFAULT_LOGGING = {
        'version': 1,
        'disable_existing_loggers': True,
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

    pp = pprint.PrettyPrinter(indent=2)

    # print(get_suggest_option_by_phone_name('memory','iPhone X'))
    # print(get_location_by_phone_name('iPhone X'))
    #print(get_item_by_price_range('title', 10000000,12000000))
    print("FIND PRODUCT: iphone")
    pp.pprint(get_product_detail("iphone", None, False, False))
    print("FIND PRODUCT: iphone x")
    pp.pprint(get_product_detail("iphone x", None, True, False))
    print("FIND PRODUCT: SAMSUNG S9")
    pp.pprint(get_product_detail("SAMSUNG S9", None, False, False))
    print("FIND PRODUCT: iphone x, has user rating")
    pp.pprint(get_product_detail("iphone x", {"$gt" : ["$user_ratings.average",
                                                       0.1]}, False, True))
