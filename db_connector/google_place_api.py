import googlemaps
from datetime import datetime
import requests

gmaps = googlemaps.Client(key='AIJc')

def get_coordinate(location):
    geocode_result = gmaps.geocode(location, language='vi-VN')
    loc_coordinate = geocode_result[0]['geometry']['location']
    loc_coordinate['loc'] = location
    
    return loc_coordinate

def get_nearest_place(place_list):
    # Geocoding an address
    geocode_result = gmaps.geocode('Đại Học Duy Tân, Nguyễn Văn Linh, Thanh Khê, Đà Nẵng')
    current_loc = geocode_result[0]['geometry']['location']
    standard_current_coordinate = str(current_loc['lat']) + ',' + str(current_loc['lng'])
    # test_location = [
    #     '110 Nguyễn Văn Linh , P.Nam Dương, Q.Hải Châu, Đà Nẵng',
    #     '155 Lê Đình Lý, P. Hòa Thuận Đông, Q. Hải Châu, TP. Đà Nẵng',
    #     'Khu 5, TT.Ái Nghĩa, H.Đại Lộc, T.Quảng Nam',
    #     'Điện Máy Xanh Đường Nguyễn Tất Thành, TT. Ái Nghĩa, H. Đại Lộc, T. Quảng Nam'
    # ]

    coordinate_list = []
    for loc in place_list:
        coordinate_list.append(get_coordinate(loc))

    standard_coordinate_list = ''
    for coordinate in coordinate_list:
        if coordinate == coordinate_list[0]:
            standard_coordinate_list += str(coordinate['lat']) + ',' + str(coordinate['lng'])
        else:
            standard_coordinate_list += '|' + str(coordinate['lat']) + ',' + str(coordinate['lng'])

    # Defind url parameter
    api_key = 'AIzaSyARzjq0LxJraV0W-KJ8a1CRMzLSzB6R5Jc'
    output_format = 'json'
    language = 'vi-VN'
    parameters = 'origins=' + standard_current_coordinate + '&destinations=' + standard_coordinate_list + '&key=' + api_key + '&language=' + language

    url = 'https://maps.googleapis.com/maps/api/distancematrix/' + output_format + '?' + parameters
    response = requests.get(url)
    response_data = response.json()

    distance_list = response_data['rows'][0]['elements']
    nearest_location = place_list[0]
    nearest_distance = distance_list[0]['distance']['text']
    nearest_duration = distance_list[0]['duration']['text']
    nearest_distance_value = distance_list[0]['distance']['value']
    for index, location in enumerate(place_list):
        temp_distance_value = distance_list[index]['distance']['value']
        if(temp_distance_value < nearest_distance_value):
            nearest_location = location
            nearest_distance = distance_list[index]['distance']['text']
            nearest_duration = distance_list[index]['duration']['text']
    
    return nearest_location, nearest_distance, nearest_duration
