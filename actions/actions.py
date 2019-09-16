# -*- coding: utf-8 -*-
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from typing import Dict, Text, Any, List, Union
from rasa_sdk import Tracker, Action
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.events import SlotSet
from rasa_sdk.forms import FormAction
from rasa_sdk.events import Restarted
import random
import db_connector.utils as dbconnector
import models.item as dbitem

import json
from bson import json_util
import csv
import os
import pandas as pd
import requests
import random
import datetime
from db_connector import mongo_database

import logging
import shutil
from functools import cmp_to_key

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

PATH = './attr/fambot/'

def convert_age(number):
    if number < 18:
        return 0
    if 18 <= number < 22:
        return 0.2
    if 22 <= number < 25:
        return 0.4
    if 25 <= number < 30:
        return 0.6
    if 30 <= number < 45:
        return 0.8
    if 45 <= number:
        return 1

# clean and remove temp dir
shutil.rmtree('/tmp/tigi-action', ignore_errors=True)
os.makedirs('/tmp/tigi-action')

print("##################### RASA ACTION ##########################")

def set_user_property(user, prop, value):
    path = '/tmp/tigi-action/' + user + '/' + prop
    if value or value > 0:
        if not os.path.exists('/tmp/tigi-action/' + user):
            os.makedirs('/tmp/tigi-action/' + user)
        with open(path, 'w') as f:
            f.write(str(value))
    elif os.path.exists(path):
        os.remove(path)

def get_user_property(user, prop):
    path = '/tmp/tigi-action/' + user + '/' + prop
    try:
        with open(path, 'r') as f:
            return int(f.readline())
    except:
        return 0
    return 0

def call_api_question_answer(ques):
    requests_url = os.getenv('QUESTION_ANSWERING_API',default= 'http://localhost:5000') + '/v1/api/questionanswering'

    input_data = {
        'question' : ques
    }

    request_data = json.dumps(input_data)
    logger.info("Request to server: " + str(input_data))

    default = "Tôi không tư vấn nổi nữa rồi :( "

    try:
        response = requests.post(url=requests_url, data=request_data)

        logger.info("Response from server: " + str(response.content))


        re_data = json.loads(response.content)

        answer = re_data['answer'] if 'answer' in re_data else default
    except requests.exceptions.RequestException as e:
        answer = default

    response = [
        {
            "type": "text",
            "data": {
                "content": answer,
                "speak": True,
            }
        }
    ]
    return json.dumps(response)

class ProfileForm(FormAction):
    def name(self):
        return "profile_form"

    @staticmethod
    def required_slots(tracker: Tracker) -> List[Text]:

        return ["user_name", "user_age", "user_gender"]

    def request_next_slot(
            self,
            dispatcher,  # type: CollectingDispatcher
            tracker,  # type: Tracker
            domain,  # type: Dict[Text, Any]
    ):
        is_QA = get_user_property((tracker.current_state())["sender_id"], 'is_QA')
        if is_QA > 0:
            answer = call_api_question_answer(tracker.latest_message['text'])
            dispatcher.utter_message(answer)
            #set_user_property((tracker.current_state())["sender_id"], 'is_QA', is_QA - 1)
            return None
        for slot in self.required_slots(tracker):
            if self._should_request_slot(tracker, slot):
                print("Request next slot '%s'", slot)


                if slot == 'user_name':
                    txt = domain['templates']['utter_ask_user_name'][1]['text']
                    response = [
                        {
                        "type":"text",
                        "data": {
                            "content": txt,
                            "speak": False,
                        }
                    }
                    ]
                    print(json.dumps(response))
                    dispatcher.utter_message(json.dumps(response))

                if slot == 'user_age':
                    txt = domain['templates']['utter_ask_user_age'][1]['text']
                    print(txt)
                    response = [
                        {
                        "type":"text",
                        "data": {
                            "content": txt,
                            "speak": False,
                        }
                    }
                    ]
                    print(json.dumps(response))
                    dispatcher.utter_message(json.dumps(response))

                if slot == 'user_gender':
                    txt = domain['templates']['utter_ask_user_gender'][1]['text']
                    response = [
                        {
                        "type":"text",
                        "data": {
                            "content": txt,
                            "speak": False,
                        }
                    }
                    ]
                    print(json.dumps(response))
                    dispatcher.utter_message(json.dumps(response))

                return [SlotSet("requested_slot", slot)]
        return None


    def submit(self,
               dispatcher: CollectingDispatcher,
               tracker: Tracker,
               domain: Dict[Text, Any]) -> List[Dict]:

        txt = domain['templates']['utter_finish_profile_form'][1]['text']
        user_name = tracker.get_slot('user_name')
        user_age = tracker.get_slot('user_age')
        user_gender = tracker.get_slot('user_gender')
        txt = txt.replace("{user_name}",user_name)

        user_id = (tracker.current_state())["sender_id"]
        gender =  0 if (user_gender.lower()).strip() == 'nam' else 1
        age = convert_age(int(user_age))
        print(user_id, gender, age)

        # collection = mongo_database['users']


        # dict_user = {"_id":user_id, "name": user_name, "gender": gender, "age": age}
        # collection.insert_one(dict_user)
        response = [
            {
            "type":"text",
            "data": {
                "content": txt,
                "speak": False,
            }
        }
        ]
        print(json.dumps(response))
        dispatcher.utter_message(json.dumps(response))

        return []

def write_attr_to_csv( text, entity, operator, value):
    user_attr = [text, entity, operator, value]
    with open(PATH + 'personal.csv','a+') as fd:
        writer = csv.writer(fd)
        writer.writerow(user_attr)


def read_attr_to_csv():
    df = pandas.read_csv(PATH+'personal.csv').dropna(axis  = 1)
    # print(df)
    result =[]
    # print(df['Entity'][0])
    i = 0
    for i in range(len(df)):
        result.append(
            {
                'text': df['Content'][i],
                'attribute':df['Entity'][i],
                'operator':df['Operator'][i],
                'value':df['Value'][i]
            }
        )
    return result

def add_header_csv():

    with open(PATH + 'personal.csv',newline='') as f:
        r = csv.reader(f)
        data = [line for line in r]
    with open(PATH + 'personal.csv','w',newline='') as f:
        w = csv.writer(f)
        w.writerow(['Content','Entity','Operator','Value'])
        w.writerows(data)

def standardized_operator(x):
    op_better = {'tốt','hơn','khủng','bự','mạnh mẽ','to', 'lớn','trâu'}
    op_least = {'kém','thua','bé','nhỏ'}
    op_eq = {'bằng','là','tầm'}
    if x in set(op_better):
        res = '>'
    elif x in set(op_least):
        res = '<'
    elif x in set(op_eq):
        res = '=='
    else:
        res = True
    return res

class ActionAskForDemand(Action):
    """
        Utters ask user talk more detail about their demand
    """
    def name(self):
        return "action_ask_for_demand"

    def run(self, dispatcher, tracker, domain):
        is_QA = get_user_property((tracker.current_state())["sender_id"], 'is_QA')
        if is_QA > 0:
            answer = call_api_question_answer(tracker.latest_message['text'])
            dispatcher.utter_message(answer)
            #set_user_property((tracker.current_state())["sender_id"], 'is_QA', is_QA - 1)
            return None 
        # Handle response follow format of API response
        txt = domain['templates']['utter_demand_question'][0]['text']
        response = [
            {
                "type":"text",
                "data": {
                    "content": txt,
                    "speak": True,
                }
            }
        ]
        dispatcher.utter_message(json.dumps(response))

        return []

class ActionAskAttribute(Action):
    def name(self):
        return "action_suggest_product_by_attribute"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict[Text,Any]]:
        is_QA = get_user_property((tracker.current_state())["sender_id"], 'is_QA')
        if is_QA > 0:
            answer = call_api_question_answer(tracker.latest_message['text'])
            dispatcher.utter_message(answer)
            #set_user_property((tracker.current_state())["sender_id"], 'is_QA', is_QA - 1)
            return None

        l_attribute = [
            'product_color',
            'product_memory',
            'product_battery',
            'product_screensize',
            'product_waterproof',
            'product_selfie_score',
            'product_lowest_price',
            'product_ram',
            'product_brand',
            'product_demand'
        ]
            # if os.path.exists(PATH + 'personal.csv'):
            #     os.remove(PATH + 'personal.csv')
        l_product_name = tracker.get_slot('product_name')
        suggestion = None
        if l_product_name is not None:
            # print('Cos ten dien thoai r' + product_name)
            data_row = dbconnector.get_product_detail(l_product_name[0], exact = False)
            print('---')
            print(data_row)
            print('---')
            if data_row is None:
                content = "Rất tiếc, tôi không thể tìm thấy sản phẩm " + l_product_name[0]
                res = [
                    {
                        "type":"text",
                        "data": {
                            "content": content,
                            "speak": True,
                        }
                    }
                ]
                dispatcher.utter_message(json.dumps(res))
                print(json.dumps(res))
                return[]
            else:
                # print(data_row)
                img = data_row['image']
                desc = data_row['specs']
                name = data_row['product']
                data_l_pr=[
                    {
                        "image": img,
                        "description":desc,
                        "name":name
                    }
                ]
        else:
            # Handle result from natural language understanding hungph
            # After contest, we can improve by implement concat value of extracted entity from NLU
            # Now let's me use rule-based
            # Read all defined filter intent from csv file
            try:
                atrribute_message += tracker.latest_message.get('text')
            except NameError:
                atrribute_message = tracker.latest_message.get('text')

            nlu_filter = []
            filter_attribute = None
            filter_value = None
            for item in l_attribute:
                filter_attribute = tracker.get_slot(item)
                # Handle for True/False and product brand attribute which has no value
                if item in ['product_waterproof', 'product_brand']:
                    filter_value = ''
                else:
                    filter_value = tracker.get_slot('attr_level')
                if filter_attribute is not None:
                    filter_element = {}
                    if item == 'product_brand':
                        filter_element['attribute'] = 'name'
                        filter_element['value'] = filter_attribute
                        nlu_filter.append(filter_element)
                    elif item == 'product_demand':
                        for demand in filter_attribute:
                            filter_element['attribute'] = demand
                            filter_element['value'] = ''
                            nlu_filter.append(filter_element)
                            filter_element = {}
                    else:
                        filter_element['attribute'] = filter_attribute
                        filter_element['value'] = '' if filter_value == None else filter_value
                        nlu_filter.append(filter_element)

                filter_attribute = None
                filter_value = None

            print('[INFO] Received filter from NLU block: ' + str(nlu_filter))
            # add_header_csv()

            filter_path = './filter.csv'
            filter_df = pd.read_csv(filter_path)
            # Set filter list to be all available filter
            filter_list = []
            filter_text = []
            for _, row in filter_df.iterrows():
                # Create list for the current row
                filter_text_row = row.text
                filter_row = {
                    'attribute': row.attribute,
                    'operator': row.operator,
                    'value': row.value
                }
                filter_list.append(filter_row)
                filter_text.append(filter_text_row)
            # Set filter_attributes to be input of recommender API
            filter_attributes = []
            for filter in nlu_filter:
                if filter['value'] == None:
                    print('[ERROR] Please check your NLU again. Maybe value of attribute is empty !')
                    return False
                l_cased_filter = (str(filter['attribute']) + ' ' + str(filter['value'])).strip().lower()
                if l_cased_filter in filter_text:
                    indices = [i for i, x in enumerate(filter_text) if x == l_cased_filter]
                    for match_i in indices:
                        filter_attributes.append({
                            'attribute': filter_list[match_i]['attribute'],
                            'operator': filter_list[match_i]['operator'],
                            'value': filter_list[match_i]['value']
                        })
                if filter['attribute'] == 'name':
                    filter_attributes.append({
                        'attribute': 'name',
                        'operator': 'find',
                        'value': filter['value']
                    })
            print('[INFO] Filter attribute list before handle call external recommender API: ' + str(filter_attributes))
            input_data = {
                "input_string": atrribute_message,
                "count": "6",
                "filter_attributes": filter_attributes
            }
            # Boss thanhnd correct for me pls
            request_url = os.getenv('RECOMMENDER_API', 'http://tigi-recommender:5000') + '/v1/api/recommend'

            logging.basicConfig(level=logging.INFO)
            logger = logging.getLogger(__name__)

            # filter_attributes = result
            request_data = json.dumps(input_data)
            logger.info("Request to server: " + str(request_data))

            response = requests.post(url = request_url, data = request_data)
            logger.info("Response from server: " + str(response.content))
            # print (response.content)
            item_re = json.loads(response.content)

            fix_rank = {
                'galaxy a80': 0,
                'iphone x': 1,
                'galaxy s10': 2
            }

            def cmp_items(a, b):
                proda = a['product'].lower()
                prodb = b['product'].lower()
                if proda in fix_rank and prodb in fix_rank:
                    return -1 if fix_rank[proda] < fix_rank[prodb] else 1
                elif proda in fix_rank:
                    return -1
                elif prodb in fix_rank:
                    return 1
                else:
                    return -1 if proda < prodb else 1

            item_re = sorted(item_re, key=cmp_to_key(cmp_items))

            logger.info("Sorted: " + str(item_re))

            # End handle result from nlu and call recommend api hungph
            l_brand = [item['brand']  for item in item_re]
            l_product = [item['product']  for item in item_re]

            # brand = 'Apple'
            # product_name  = 'iPhone X'
            # print(l_brand)
            # print(l_product[1])

            i = 0
            data_l_pr = []
            for i in range(len(l_brand)):
                # condition = {
                #         "product" : l_product[i],
                #         "brand": l_brand[i]
                # }
                # print(condition)

                data_row = dbconnector.get_product_detail_icase(l_brand[i],l_product[i])
                if data_row:
                    # print(data_row)
                    img = data_row['image']
                    desc = data_row['specs']
                    name = data_row['product']

                    # data_l_pr = []
                    data_l_pr.append(
                        {
                            "image": img,
                            "description":desc,
                            "name":name
                        }
                    )
            best_product_name = data_l_pr[0]['name']
            suggestion = {
                "type": "text",
                "data": {
                    "content": "Trong những sản phẩm này, Tizzie cho rằng " + best_product_name + " sẽ phù hợp nhất với nhu cầu chơi game và công việc hàng ngày ở một mức giá tốt.",
                    "speak": True
                }
            }

        mess = [
            {
                "type": "item",
                "data": data_l_pr
            },
        ]

        if suggestion:
            mess.append(suggestion)

        dispatcher.utter_message(json.dumps(mess, default=json_util.default))
        print(mess)

class Action_show_detail_product(Action):
    def name(self):
        return "action_show_detail_product"

    @staticmethod
    def required_slots(tracker: Tracker) -> List[Text]:
        return ['product_name']

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict[Text,Any]]:
        is_QA = get_user_property((tracker.current_state())["sender_id"], 'is_QA')
        if is_QA > 0:
            answer = call_api_question_answer(tracker.latest_message['text'])
            dispatcher.utter_message(answer)
            #set_user_property((tracker.current_state())["sender_id"], 'is_QA', is_QA - 1)
            return None

        l_name = tracker.get_slot('product_name')
        if l_name is None:
            txt = domain['templates']['utter_default'][1]['text']

            response = [
                {
                "type":"text",
                "data": {
                    "content": txt,
                    "speak": True,
                }
            }
            ]
            print(json.dumps(response))
            dispatcher.utter_message(json.dumps(response))
        else:
            p_name = l_name[0]
            response = dbconnector.get_product_detail(p_name,exact= False)
            url_image = response['image']
            product = response['product']
            brand = response['brand']

            if len(response['review_articles']) > 0:
                request_url = os.getenv('PERSONALREVIEWSUMMARY_API', 'http://tigi-personalreviewsummary:5000') + '/v1/api/personalsummarization'
                review_url = response['review_articles'][0]['url']

                # TODO: get user profile vector via service
                input_data = {'user_demands': {'screen': 0.1,'battery': 0.9,'camera': 0.4,'config': 0.6,'design': 0.2,'durability': 0.1,'feature': 0.4,'sound': 0.9},'product_url': review_url,"req_type": "short"}

                request_data = json.dumps(input_data)
                logger.info(request_data)
                logger.info(request_url)
                reviewservice_response = requests.post(url = request_url, data = request_data)
                logger.info(reviewservice_response)
                # print (response.content)
                reviewservice_result = json.loads(reviewservice_response.content)
                logger.info(reviewservice_result['summary'])


                desc = reviewservice_result['summary']
            else:
                desc = p_name

            lowest_price = response['lowest_price']
            rating = response['rating']
            specs = {
                "Chip": response['chipset'],
                "Kích thước màn hình" : response['screen_size'],
                "Bộ nhớ": response['memory'],
                "Camera sau": response['main_camera'],
                "Camera truoc": response['selfie_camera']
            }

            detail_product = [
                {
                "type":"detail",
                "data":[
                    {
                    "image": url_image,
                    "product": product,
                    "brand": brand,
                    "desc": desc,
                    "lowest_price": lowest_price,
                    "specs": specs
                    }
                ]
                }
            ]
            dispatcher.utter_message(json.dumps(detail_product))
            print(json.dumps(detail_product))


class Action_show_history_product(Action):
    def name(self):
        return "action_show_history_product"

    @staticmethod
    def required_slots(tracker: Tracker) -> List[Text]:
        return ['product_name']

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict[Text,Any]]:
        is_QA = get_user_property((tracker.current_state())["sender_id"], 'is_QA')
        if is_QA > 0:
            answer = call_api_question_answer(tracker.latest_message['text'])
            dispatcher.utter_message(answer)
            #set_user_property((tracker.current_state())["sender_id"], 'is_QA', is_QA - 1)
            return None

        l_name = tracker.get_slot('product_name')
        if l_name is None:
            txt = domain['templates']['utter_default'][1]['text']

            response = [
                {
                "type":"text",
                "data": {
                    "content": txt,
                    "speak": False,
                }
            }
            ]
            print(json.dumps(response))
            dispatcher.utter_message(json.dumps(response))
        else:
            p_name = l_name[0]
            response = dbconnector.get_product_detail(p_name,exact=False)
            price_history = response['price_history']
            print(price_history)
            print('-----')
            lent = len(price_history)
            response_history = []

            today = datetime.date.today()
            inserted_date = datetime.date.today() - datetime.timedelta(15)
            first_date = price_history[0]['update_time'].date()
            index = 0


            while inserted_date < first_date:
                h = price_history[0].copy()
                h['update_time'] = datetime.datetime.fromordinal(inserted_date.toordinal())
                response_history.append(h)
                #print("\tAdd first ", price_history[index]['update_time'], inserted_date)
                inserted_date += datetime.timedelta(1)

            while inserted_date <= today:
                while index < len(price_history) and price_history[index]['update_time'].date() < inserted_date:
                    response_history.append(price_history[index])
                    #print("\tAdd leftover ", price_history[index]['update_time'])
                    index += 1

                if index < len(price_history) and price_history[index]['update_time'].date() == inserted_date:
                    response_history.append(price_history[index])
                    #print("\tAdd true date ", price_history[index]['update_time'])
                    index += 1
                elif index > 0:
                    h = price_history[index-1].copy()
                    h['update_time'] = datetime.datetime.fromordinal(inserted_date.toordinal())
                    response_history.append(h)
                    #print("\tAdd old data ", price_history[index-1]['update_time'])
                else:
                    break

                inserted_date += datetime.timedelta(1)

            #print(response_history)

            history_product = [
                {
                "type":"price_history",
                "data": response_history
                }
            ]
            dispatcher.utter_message(json.dumps(history_product,default=json_util.default))
            print(json.dumps(history_product, default=json_util.default))

class Action_show_review_product(Action):

    def name(self):
        return "action_show_review_product"

    @staticmethod
    def required_slots(tracker: Tracker) -> List[Text]:
        return ['product_name']

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict[Text,Any]]:
        is_QA = get_user_property((tracker.current_state())["sender_id"], 'is_QA')
        if is_QA > 0:
            answer = call_api_question_answer(tracker.latest_message['text'])
            dispatcher.utter_message(answer)
            #set_user_property((tracker.current_state())["sender_id"], 'is_QA', is_QA - 1)
            return None

        l_name = tracker.get_slot('product_name')
        if l_name is None:
            txt = domain['templates']['utter_default'][1]['text']

            response = [
                {
                "type":"text",
                "data": {
                    "content": txt,
                    "speak": True,
                }
            }
            ]
            print(json.dumps(response))
            dispatcher.utter_message(json.dumps(response))
        else:
            p_name = l_name[0]
            response = dbconnector.get_product_detail(p_name,exact=False)
            if response is None:
                content = "Rất tiếc, tôi không thể tìm thấy sản phẩm " + p_name
                res = [
                    {
                        "type":"text",
                        "data": {
                            "content": content,
                            "speak": True,
                        }
                    }
                ]
                dispatcher.utter_message(json.dumps(res))
                print(json.dumps(res))
            else:
                review = response['review_articles']
                lent = len(review)

                if lent > 0:
                    request_url = os.getenv('PERSONALREVIEWSUMMARY_API',
                                            'http://localhost:5000') + '/v1/api/personalsummarization'
                    review_url = response['review_articles'][0]['url']

                    # TODO: get user profile vector via service
                    input_data = {
                        'user_demands': {'screen': 0.1, 'battery': 0.9, 'camera': 0.4, 'config': 0.6, 'design': 0.2,
                                         'durability': 0.1, 'feature': 0.4, 'sound': 0.9},
                        'product_url': review_url,
                        "req_type": "long"}

                    request_data = json.dumps(input_data)
                    logger.info(request_data)
                    logger.info(request_url)
                    reviewservice_response = requests.post(url=request_url, data=request_data)
                    logger.info(reviewservice_response)
                    # print (response.content)
                    reviewservice_result = json.loads(reviewservice_response.content)
                    logger.info(reviewservice_result['summary'])

                    id = random.randint(0,lent-1)
                    review_product = [
                        {
                        "type":"text",
                        "data": {
                            "content": "Bạn có thể tham khảo link sau: " + review[id]['url'] + "\n" + "Tóm tắt:" + reviewservice_result['summary'],
                            "speak": False
                        }
                    }
                    ]
                else:
                    review_product = [{
                        "type":"text",
                        "data": {
                            "content": "Rất tiếc, chúng tôi không thể tìm thấy trải nghiệm của sản phẩm",
                            "speak": True
                        }
                    }]


                dispatcher.utter_message(json.dumps(review_product,default=json_util.default))
                print(json.dumps(review_product, default=json_util.default))

class Action_show_video_user_experience_product(Action):

    def name(self):
        return "action_show_video_user_experience_product"

    @staticmethod
    def required_slots(tracker: Tracker) -> List[Text]:
        return ['product_name']

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict[Text,Any]]:
        is_QA = get_user_property((tracker.current_state())["sender_id"], 'is_QA')
        if is_QA > 0:
            answer = call_api_question_answer(tracker.latest_message['text'])
            dispatcher.utter_message(answer)
            #set_user_property((tracker.current_state())["sender_id"], 'is_QA', is_QA - 1)
            return None

        l_name = tracker.get_slot('product_name')
        if l_name is None:
            txt = domain['templates']['utter_default'][1]['text']

            response = [
                {
                "type":"text",
                "data": {
                    "content": txt,
                    "speak": True,
                }
            }
            ]
            print(json.dumps(response))
            dispatcher.utter_message(json.dumps(response))
        else:
            p_name = l_name[0]
            response = dbconnector.get_product_detail(p_name,exact=False)
            if response is None:
                content = "Rất tiếc, tôi không thể tìm thấy sản phẩm " + p_name
                res = [
                    {
                        "type":"text",
                        "data": {
                            "content": content,
                            "speak": True,
                        }
                    }
                ]
                dispatcher.utter_message(json.dumps(res))
                print(json.dumps(res))
            else:
                print(response)
                review = response['review_videos']
                print('====')
                if review == []:
                    content = "Rất tiếc, chúng tôi không thể tìm thấy video trải nghiệm của sản phẩm " + p_name
                    res = [
                        {
                            "type":"text",
                            "data": {
                                "content": content,
                                "speak": True,
                            }
                        }
                    ]
                    dispatcher.utter_message(json.dumps(res))
                    print(json.dumps(res))

                else:

                    lent = len(review)
                    id = random.randint(0,lent-1)
                            # price_history = response['price_history']

                            # print()
                    review_product = [
                        {
                        "type":"text",
                        "data": [
                            {
                            "url": review[id]['url'],
                            "title": review[id]['title']
                            }
                        ]
                        }
                    ]
                    dispatcher.utter_message(json.dumps(review_product,default=json_util.default))
                    print(json.dumps(review_product, default=json_util.default))


class Action_greet(Action):
    def name(self):
        return "action_greet"

    @staticmethod
    def required_slots(tracker: Tracker) -> List[Text]:
        return []

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict[Text,Any]]:
        is_QA = get_user_property((tracker.current_state())["sender_id"], 'is_QA')
        if is_QA > 0:
            answer = call_api_question_answer(tracker.latest_message['text'])
            dispatcher.utter_message(answer)
            #set_user_property((tracker.current_state())["sender_id"], 'is_QA', is_QA - 1)
            return None

        txt = domain['templates']['utter_greet'][1]['text']
        guide_message = 'Bạn có thể nói cho mình biết bạn đang "Tìm" sản phẩm như thế nào, "Sử dụng" vào mục đích gì, "Giới hạn" các tiêu chí tìm kiếm và "So sánh" các sản phẩm nào với nhau. Để kết thúc phiên tìm kiếm bạn vui lòng nói với Tizzie "Tôi chọn sản phẩm" nào nhé.'

        response = [
            {
            "type":"text",
            "data": 
                {
                    "content": txt,
                    "speak": True,
                }
            },
            {
            "type":"text",
            "data": 
                {
                    "content": guide_message,
                    "speak": False,
                }
            }
        ]
        print(json.dumps(response))
        dispatcher.utter_message(json.dumps(response))

class Action_Default_Fallback(Action):
    def name(self):
        return "action_default_fallback"

    @staticmethod
    def required_slots(tracker: Tracker) -> List[Text]:
        return []

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict[Text,Any]]:
        is_QA = get_user_property((tracker.current_state())["sender_id"], 'is_QA')
        if is_QA > 0:
            answer = call_api_question_answer(tracker.latest_message['text'])
            dispatcher.utter_message(answer)
            #set_user_property((tracker.current_state())["sender_id"], 'is_QA', is_QA - 1)
            return None

        txt = domain['templates']['utter_default'][1]['text'] + \
              """.\nBạn có thể nói cho mình biết bạn đang "Tìm" \
              sản phẩm như thế nào,  "Sử dụng" vào mục đích gì, \
              "Giới hạn" các tiêu chí tìm kiếm và "So sánh" các \
              sản phẩm nào với nhau.  Để kết thúc phiên tìm kiếm \
              bạn vui lòng nói với Tizzie "Tôi chọn sản phẩm" nào nhé."""

        response = [
            {
            "type":"text",
            "data": {
                "content": txt,
                "speak": True,
            }
        }
        ]
        print(json.dumps(response))
        dispatcher.utter_message(json.dumps(response))

class ActionRestart(Action):
    def name(self):
        return 'action_restart'

    def run(self, dispatcher, tracker, domain):

        is_QA = get_user_property((tracker.current_state())["sender_id"], 'is_QA')
        if is_QA > 0:
            answer = call_api_question_answer(tracker.latest_message['text'])
            dispatcher.utter_message(answer)
            #set_user_property((tracker.current_state())["sender_id"], 'is_QA', is_QA - 1)
            return None

        txt = domain['templates']['utter_restart'][0]['text']
        response = [
            {
            "type":"text",
            "data": {
                "content": txt,
                "speak": True,
            }
        }
        ]
        print(json.dumps(response))
        dispatcher.utter_message(json.dumps(response))
        return[Restarted()]

class ActionCompareProduct(Action):
    def name(self):
        return 'action_compare_product_by_name'

    @staticmethod
    def required_slots(tracker: Tracker) -> List[Text]:
        return []

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict[Text,Any]]:

        is_QA = get_user_property((tracker.current_state())["sender_id"], 'is_QA')
        if is_QA > 0:
            answer = call_api_question_answer(tracker.latest_message['text'])
            dispatcher.utter_message(answer)
            #set_user_property((tracker.current_state())["sender_id"], 'is_QA', is_QA - 1)
            return None

        list_product_name  = tracker.get_slot('product_name')
        product1 = list_product_name[0].strip()
        lent = len(list_product_name)
        if lent == 1:
            product2 = 'Samsung Galaxy A80'
        else:
            product2 = list_product_name[1].strip()

        print('===')
        print(product1)
        print(product2)
        print('===')
        response1 = dbconnector.get_product_detail(product1,exact=False)
        response2 = dbconnector.get_product_detail(product2,exact=False)
        print('===')
        print(response1)
        print(response2)
        print('===')
        if response1 is None :
            content = "Rất tiếc, tôi không thể tìm thấy sản phẩm " + product1
            res = [
                {
                    "type":"text",
                    "data": {
                        "content": content,
                        "speak": True,
                    }
                }
            ]
            dispatcher.utter_message(json.dumps(res))
            print(json.dumps(res))
        elif response2 is None:
            content = "Rất tiếc, tôi không thể tìm thấy sản phẩm " + product2
            res = [
                {
                    "type":"text",
                    "data": {
                        "content": content,
                        "speak": True,
                    }
                }
            ]
            dispatcher.utter_message(json.dumps(res))
            print(json.dumps(res))
        else:

            if len(response2['review_articles']) > 0:
                request_url = os.getenv('PERSONALREVIEWSUMMARY_API', 'http://tigi-personalreviewsummary:5000') + '/v1/api/personalsummarization'
                review_url = response2['review_articles'][0]['url']

                # TODO: get user profile vector via service
                input_data = {'user_demands': {'screen': 0.1,'battery': 0.9,'camera': 0.4,'config': 0.6,'design': 0.2,'durability': 0.1,'feature': 0.4,'sound': 0.9},'product_url': review_url,"req_type": "short"}

                request_data = json.dumps(input_data)
                logger.info(request_data)
                logger.info(request_url)
                reviewservice_response = requests.post(url = request_url, data = request_data)
                logger.info(reviewservice_response)
                # print (response.content)
                reviewservice_result = json.loads(reviewservice_response.content)
                logger.info(reviewservice_result['summary'])


                desc2 = reviewservice_result['summary']
            else:
                desc2 = p_name

            if len(response1['review_articles']) > 0:
                request_url = os.getenv('PERSONALREVIEWSUMMARY_API', 'http://tigi-personalreviewsummary:5000') + '/v1/api/personalsummarization'
                review_url = response1['review_articles'][0]['url']

                # TODO: get user profile vector via service
                input_data = {'user_demands': {'screen': 0.1,'battery': 0.9,'camera': 0.4,'config': 0.6,'design': 0.2,'durability': 0.1,'feature': 0.4,'sound': 0.9},'product_url': review_url,"req_type": "short"}

                request_data = json.dumps(input_data)
                logger.info(request_data)
                logger.info(request_url)
                reviewservice_response = requests.post(url = request_url, data = request_data)
                logger.info(reviewservice_response)
                # print (response.content)
                reviewservice_result = json.loads(reviewservice_response.content)
                logger.info(reviewservice_result['summary'])


                desc1 = reviewservice_result['summary']
            else:
                desc1 = p_name

            specs1 ={
                    "Chip": response1['chipset'],
                    "Kích thước màn hình" : response1['screen_size'],
                    "Bộ nhớ": response1['memory'],
                    "Camera sau": response1['main_camera'],
                    "Camera trước": response1['selfie_camera']
                }


            specs2 = {
                "Chip": response2['chipset'],
                "Kích thước màn hình" : response2['screen_size'],
                "Bộ nhớ": response2['memory'],
                "Camera sau": response2['main_camera'],
                "Camera trước": response2['selfie_camera']
            }

            compare_product = [
                {
                "type":"compare",
                "data":[
                    {
                    "image" : response1['image'],
                    "name": response1['product'],
                    "brand": response1['brand'],
                    "desc": desc1,
                    "lowest_price": response1['lowest_price'],
                    "rating" : response1['rating'],
                    "specs": specs1
                    },
                    {
                    "image": response2['image'],
                    "name": response2['product'],
                    "brand": response2['brand'],
                    "desc": desc2,
                    "lowest_price": response2['lowest_price'],
                    "rating" : response2['rating'],
                    "specs": specs2
                    }
                ]
                }
            ]
            #dispatcher.utter_message(json.dumps(compare_product))

            print('=====================')
            battery1 = int(response1['battery'].replace(' mAh',''))
            battery2 = int(response2['battery'].replace(' mAh',''))
            screen_size1 = response1['screen_size'].replace('\"','')
            sz1 = float(screen_size1)
            screen_size2 = response2['screen_size'].replace('\"','')
            sz2 = float(screen_size2)
            print(battery1)
            print(battery2)
            range_battery = abs(battery2 - battery1 )
            range_screen_size = abs(sz2 - sz1)
            a = round(range_battery*100/battery2)
            print(a)
            print(range_screen_size)
            if a > 20 :
                txt = 'Bạn nên dùng sản phẩm ' + product2 + ' vì nó lớn hơn tận ' + str(a) + '% so với ' + product1
            elif 0.6 < range_screen_size < 0.8:
                txt = 'Bạn nên dùng sản phẩm ' + product2 + ' vì nó có kích thước màn hình to hơn ' + product1
            else:
                txt = 'Bạn nên cân nhắc kỹ 2 sản phẩm này nha'
            suggest = {
                "type":"text",
                "data": {
                    "content": txt,
                    "speak": False,
                }
            }

            compare_product.insert(0, suggest)

            logger.info(json.dumps(compare_product))
            dispatcher.utter_message(json.dumps(compare_product))
            return None


class ActionFinishFindProduct(Action):
    def name(self):
        return 'action_finish_find_product'

    def run(self,dispatcher,tracker,domain):
        is_QA = get_user_property((tracker.current_state())["sender_id"], 'is_QA')
        if is_QA > 0:
            answer = call_api_question_answer(tracker.latest_message['text'])
            dispatcher.utter_message(answer)
            #set_user_property((tracker.current_state())["sender_id"], 'is_QA', is_QA - 1)
            return None


        last_product = tracker.get_latest_entity_values('product_name')
        product_name = tracker.get_slot('product_name')[0]
        print(last_product)
        print(product_name)
        user_id = (tracker.current_state())["sender_id"]

        set_user_property(user_id, 'is_QA', 3)

        txt = domain['templates']['utter_finish_find_product'][0]['text']
        txt = txt.replace('<product_name>',product_name)
        response = [
            {
            "type":"text",
            "data": {
                "content": txt,
                "speak": False,
            }
        }
        ]
        print(json.dumps(response))
        dispatcher.utter_message(json.dumps(response))

        dispatcher.utter_template('utter_finish_find_product',tracker,product_name=product_name)
        return[]

class ActionHappyProduct(Action):
    def name(self):
        return 'action_happy_product'

    def run(self,dispatcher,tracker,domain):
        # is_QA = get_user_property((tracker.current_state())["sender_id"], 'is_QA')
        # if is_QA > 0:
        #     answer = call_api_question_answer(tracker.latest_message['text'])
        #     dispatcher.utter_message(answer)
        set_user_property((tracker.current_state())["sender_id"], 'is_QA', 0 )
        #     return None
        logger.info('=========================================')

        #txt = domain['templates']['utter_location_product'][0]['text']

        response = [
            {
            "type":"location",
            "data": {
                "content": "",
                "speak": False,
            }
        }
        ]
        print(json.dumps(response))
        dispatcher.utter_message(json.dumps(response))
        return[]


