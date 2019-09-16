
## Story profile form
* greet
    - action_greet
    - profile_form
    - form{"name":"profile_form"}
    - form{"name":null}

## Story inform product name
* inform
    - slot{"product_name":"Iphone X"}
    - action_suggest_product_by_attribute



## Story find product
## New story
* find_product{"category":"điện thoại","product_lowest_price":"phân khúc","attr_level":"cận cao cấp"}
    - slot{"attr_level":"cận cao cấp"}
    - slot{"product_lowest_price":"phân khúc"}
    - action_ask_for_demand
* find_product
    - slot{"product_demand": ["chơi game đồ họa", "phục vụ công việc hàng ngày"]}
    - slot{"attr_level": ""}
    - action_suggest_product_by_attribute

## Story show detail
* intent_suggest_product_by_frontend
    - slot{"frontend_p1":"thỏ ngọc"}
    - slot{"product_name":"Iphone X"}
    - action_show_detail_product

## Story show history price
* show_history_product_price
    - slot{"product_name":"Iphone X"}
    - action_show_history_product

## Story show review product
* show_review_product
    - slot{"product_name":"Iphone X"}
    - action_show_review_product

## Story show video user experience product
* show_video_user_experience_product
    - slot{"product_name":"Iphone X"}
    - action_show_video_user_experience_product

## Story compare product name
* compare_product_by_name
    - slot{"product_name":["Iphone X","Samsung Note 9"]}
    - action_compare_product_by_name



## Story finish find product
* final_find_product
    - slot{"product_name":"Iphone X"}
    - action_finish_find_product

## Story happy
* happy_satisfied   
    - slot{"satisfied":"hài lòng"}
    - action_happy_product
