from django.shortcuts import render
from datetime import datetime
# Create your views here.
from django.conf import settings
from django.http import HttpResponse, HttpResponseBadRequest, HttpResponseForbidden
from django.views.decorators.csrf import csrf_exempt

from linebot import LineBotApi, WebhookParser
from linebot.exceptions import InvalidSignatureError, LineBotApiError
from linebot.models import MessageEvent, TextSendMessage

import requests, time

line_bot_api = LineBotApi(settings.LINE_CHANNEL_ACCESS_TOKEN)
parser = WebhookParser(settings.LINE_CHANNEL_SECRET)
 

'''
功能: !現在
Output: 現在城市的天氣

'''
city_list = ["宜蘭縣", "桃園市", "新竹縣", "苗栗縣",
                 "彰化縣", "南投縣", "雲林縣", "嘉義縣",
                 "屏東縣", "臺東縣", "花蓮縣", "澎湖縣",
                 "基隆市", "新竹市", "嘉義市", "臺北市",
                 "高雄市", "新北市", "臺中市", "臺南市",
                 "連江縣", "金門縣"]
# 全域變數，用於儲存使用者當前的狀態
user_state = {}

@csrf_exempt
def callback(request):
    if request.method == 'POST':
        signature = request.META['HTTP_X_LINE_SIGNATURE']
        body = request.body.decode('utf-8')
        try:
            events = parser.parse(body, signature)  # 解析傳入的事件
        except InvalidSignatureError:
            return HttpResponseForbidden()
        except LineBotApiError:
            return HttpResponseBadRequest()

        for event in events:
            if isinstance(event, MessageEvent):  # 如果是訊息事件
                user_id = event.source.user_id  # 取得使用者 ID
                message_text = event.message.text  # 取得使用者輸入的訊息

                if user_id not in user_state:
                    user_state[user_id] = {}  # 初始化使用者狀態

                if 'country' not in user_state[user_id]:  # 如果使用者尚未輸入縣市
                    if message_text in city_list:  # 檢查是否為有效的縣市
                        user_state[user_id]['country'] = message_text
                        line_bot_api.reply_message(
                            event.reply_token,
                            TextSendMessage(text="輸入城鎮名")
                        )
                    else:
                        line_bot_api.reply_message(
                            event.reply_token,
                            TextSendMessage(text="請輸入有效的縣市名稱")
                        )
                else:  # 如果使用者已經輸入縣市，等待輸入城鎮
                    county = user_state[user_id]['country']
                    town = message_text
                    weather_data = weather(county, town)  # 取得天氣資料
                    line_bot_api.reply_message(
                        event.reply_token,
                        TextSendMessage(text=weather_data)
                    )
                    del user_state[user_id]  # 清除使用者狀態
        return HttpResponse()
    else:
        return HttpResponseBadRequest()


def weather(city_name, town_name):
    # 將主要縣市個別的 JSON 代碼列出
    api_list = {"宜蘭縣":"F-D0047-001","桃園市":"F-D0047-005","新竹縣":"F-D0047-009","苗栗縣":"F-D0047-013",
            "彰化縣":"F-D0047-017","南投縣":"F-D0047-021","雲林縣":"F-D0047-025","嘉義縣":"F-D0047-029",
            "屏東縣":"F-D0047-033","臺東縣":"F-D0047-037","花蓮縣":"F-D0047-041","澎湖縣":"F-D0047-045",
            "基隆市":"F-D0047-049","新竹市":"F-D0047-053","嘉義市":"F-D0047-057","臺北市":"F-D0047-061",
            "高雄市":"F-D0047-065","新北市":"F-D0047-069","臺中市":"F-D0047-073","臺南市":"F-D0047-077",
            "連江縣":"F-D0047-081","金門縣":"F-D0047-085"}
    
   
    code = 'CWA-5B67EBB4-391E-48B5-94A4-E0D56DBB8C30'

    #ToDo !宜蘭市 間隔三小時天氣預報

    city = api_list[city_name]
    # t = time.time()
    # t1 = time.localtime(t)       # 因為 colab 所在時區，要額外增加八小時 28800 秒
    # t2 = time.localtime(t) # 因為 colab 所在時區，要額外增加八小時 28800 秒與三小時 10800 秒
    # now = time.strftime('%Y-%m-%dT%H:%M:%S',t1)
    # now2 = time.strftime('%Y-%m-%dT%H:%M:%S',t2)

    url = f'https://opendata.cwa.gov.tw/api/v1/rest/datastore/{city}?Authorization={code}&limit=30&format=JSON'
    req = requests.get(url)   # 取得主要縣市預報資料
    data = req.json()         # json 格式化訊息內容

    result = Normal_Temperature_Data(data)
    #ToDo  指定某個鄉
    result = result[town_name]
    print(result[:20])
    
    # ToDo:
    # 每天傳送明天區間時間的天氣資訊
    # Get 現在時間 2025-01-30T17:20
    # 回傳字串:
    # 時間: 2025-01-30T18:00 ~ 2025-01-30T21:00，
    # 溫度17度C，體感溫度13度C，稍有寒意
    


    tomorrow_data = Get_Tomorrow_Data(result)
    Tomorow_Temperature_Text = Print_Tomorow_Temperature_Text(tomorrow_data)
    
    return Tomorow_Temperature_Text

def Normal_Temperature_Data(data):
    '''
    使用:
    result = Normal_Temperature_Data(data)
    result['板橋區'][:2]

    Return:
    [{'時間': '2025-01-30T18:00:00+08:00', '溫度': {'Temperature': '19'}, '體感溫度': {'ApparentTemperature': '15'}, '舒適度指數': {'ComfortIndex': '18', 'ComfortIndexDescription': '稍有寒意'}}, {'時間': '2025-01-30T19:00:00+08:00', '溫度': {'Temperature': '18'}, '體感溫度': {'ApparentTemperature': '16'}, '舒適度指數': {'ComfortIndex': '17', 'ComfortIndexDescription': '稍有寒意'}}]
    '''

    # 要處理的四個指定屬性
    target_attributes = ["溫度", "體感溫度", "相對濕度", "舒適度指數"]

    # 初始化結果字典
    result = {}

    # 抓取資料中的所有地點
    locations = data["records"]["Locations"][0]["Location"]

    # 處理每個地點的資料
    for location in locations:
        location_name = location["LocationName"]
        weather_elements = location["WeatherElement"]

        # 建立每個地點的字典結構
        result[location_name] = []

        # 建立時間為索引的資料結構
        time_data = {}

        # 結合不同 ElementName 的資料
        for element in weather_elements:
            element_name = element["ElementName"]

            # 忽略不在目標屬性的資料
            if element_name not in target_attributes:
                continue
            
            for time_entry in element["Time"]:
                time = time_entry["DataTime"]
                value = time_entry["ElementValue"][0]

                # 確保該時間的字典結構存在
                if time not in time_data:
                    time_data[time] = {"時間": time}

                # 加入不同屬性的資料
                time_data[time][element_name] = value

        # 擷取前 10 筆資料並加入結果
        result[location_name].extend(list(time_data.values()))
    return result

def Get_Tomorrow_Data(result):
    '''
    Input: 氣象資料
    Output: [{'時間': '2025-01-31T00:00:00+08:00', '溫度': {'Temperature': '17'}, '體感溫度': {'ApparentTemperature': '15'}, '舒適度指數': {'ComfortIndex': '16', 'ComfortIndexDescription': '稍有寒意'}}, {'時間': '2025-01-31T01:00:00+08:00', '溫度': {'Temperature': '17'}, '體感溫度': {'ApparentTemperature': '15'}, '舒適度指數': {'ComfortIndex': '16', 'ComfortIndexDescription': '稍有寒意'}}, {'時間': '2025-01-31T02:00:00+08:00', '溫度': {'Temperature': '17'}, '體感溫度': {'ApparentTemperature': '15'}]
    '''

    now = datetime.now()
    #print(f"now: {now}")
    formatted_now = now.strftime("%Y-%m-%dT%H:%M")
    print("格式化時間:", formatted_now)

    date_part = formatted_now.split('T')[0] #現在時間2025-01-30
    #print(date_part)
    tomorrow_data = []
    #取出所有非2025-01-30的24筆資料 即2525-01-31的每小時資料
    i = 0
    for data in result:   
        #print(data)  #{'時間': '2025-01-30T18:00:00+08:00', '溫度': {'Temperature': '19'}, '體感溫度': {'ApparentTemperature': '15'}, '舒適度指數': {'ComfortIndex': '18', 'ComfortIndexDescription': '稍有寒意'}}
        if i==24:
            break
        if data['時間'].split('T')[0] != date_part:    #天氣資料的日期不等於今天日期
            tomorrow_data.append(data)
            i += 1
    #print(f"tomorrow_data: {tomorrow_data}")    
    return tomorrow_data


def Print_Tomorow_Temperature_Text(tomorrow_data):
    # Input:
    # tomorrow_data   function:Get_Tomorrow_Data()
    # 回傳字串:
    # 2025-01-31
    # 00:00:00 溫度17度C，體感溫度13度C，稍有寒意
    # 01:00:00 溫度17度C，體感溫度13度C，稍有寒意
    #.....
    Text = f"{tomorrow_data[0]['時間'].split('T')[0]}\n"
    next_line = "\n"
    for i,t_data in enumerate(tomorrow_data):
        tomorrow_day = t_data['時間'].split('T')[0]
        Temperature = t_data['溫度']['Temperature']
        Body_feeling_Temperature = t_data['體感溫度']['ApparentTemperature']
        ComfortIndexDescription = t_data['舒適度指數']['ComfortIndexDescription']
        RelativeHumidity = t_data['相對濕度']['RelativeHumidity']

        tomorrow_hour = t_data['時間'].split('T')[1].split('+')[0]  #13:00:00
        if i==len(tomorrow_data)-1:
            next_line = ""
        Text = Text + f"時間{tomorrow_hour} 溫度{Temperature}度C，體感溫度{Body_feeling_Temperature}度C，相對濕度{RelativeHumidity}%，{ComfortIndexDescription}。" + f"{next_line}"
    
    print(Text)
    return Text