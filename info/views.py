from django.shortcuts import render

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
 
 
@csrf_exempt
def callback(request):
    #print(request.method)
    if request.method == 'POST':
        signature = request.META['HTTP_X_LINE_SIGNATURE']
        body = request.body.decode('utf-8')
        try:
            events = parser.parse(body, signature)  # 傳入的事件
        except InvalidSignatureError:
            return HttpResponseForbidden()
        except LineBotApiError:
            
            return HttpResponseBadRequest()
 
        for event in events:
            if isinstance(event, MessageEvent):  # 如果有訊息事件
                line_bot_api.reply_message(  # 回復傳入的訊息文字
                    event.reply_token,
                    TextSendMessage(text=event.message.text)
                )
        return HttpResponse()
    else:
        return HttpResponseBadRequest()


def weather(request):
    # 將主要縣市個別的 JSON 代碼列出
    api_list = {"宜蘭縣":"F-D0047-001","桃園市":"F-D0047-005","新竹縣":"F-D0047-009","苗栗縣":"F-D0047-013",
            "彰化縣":"F-D0047-017","南投縣":"F-D0047-021","雲林縣":"F-D0047-025","嘉義縣":"F-D0047-029",
            "屏東縣":"F-D0047-033","臺東縣":"F-D0047-037","花蓮縣":"F-D0047-041","澎湖縣":"F-D0047-045",
            "基隆市":"F-D0047-049","新竹市":"F-D0047-053","嘉義市":"F-D0047-057","臺北市":"F-D0047-061",
            "高雄市":"F-D0047-065","新北市":"F-D0047-069","臺中市":"F-D0047-073","臺南市":"F-D0047-077",
            "連江縣":"F-D0047-081","金門縣":"F-D0047-085"}
    
   
    code = 'CWA-5B67EBB4-391E-48B5-94A4-E0D56DBB8C30'

    #ToDo !宜蘭市 間隔三小時天氣預報

    city = 'F-D0047-069' #新北市
    # t = time.time()
    # t1 = time.localtime(t)       # 因為 colab 所在時區，要額外增加八小時 28800 秒
    # t2 = time.localtime(t) # 因為 colab 所在時區，要額外增加八小時 28800 秒與三小時 10800 秒
    # now = time.strftime('%Y-%m-%dT%H:%M:%S',t1)
    # now2 = time.strftime('%Y-%m-%dT%H:%M:%S',t2)

    url = f'https://opendata.cwa.gov.tw/api/v1/rest/datastore/{city}?Authorization={code}&limit=30&format=JSON'
    req = requests.get(url)   # 取得主要縣市預報資料
    data = req.json()         # json 格式化訊息內容
    

    
    

    result = Normal_Temperature_Data(data)
    
    print(result['板橋區'][:2])
    
    # ToDo:
    # Get 現在時間 2025-01-30T17:20
    # 回傳字串:
    # 現在時間: 2025-01-30T17:20，溫度17度C，體感溫度13度C，稍有寒意
    


    return HttpResponse('123')

def Normal_Temperature_Data(data):
    '''
    使用:
    result = Normal_Temperature_Data(data)
    result['板橋區'][:2]

    Return:
    [{'時間': '2025-01-30T18:00:00+08:00', '溫度': {'Temperature': '19'}, '體感溫度': {'ApparentTemperature': '15'}, '舒適度指數': {'ComfortIndex': '18', 'ComfortIndexDescription': '稍有寒意'}}, {'時間': '2025-01-30T19:00:00+08:00', '溫度': {'Temperature': '18'}, '體感溫度': {'ApparentTemperature': '16'}, '舒適度指數': {'ComfortIndex': '17', 'ComfortIndexDescription': '稍有寒意'}}]
    '''

    # 要處理的四個指定屬性
    target_attributes = ["溫度", "體感溫度", "相對溼度", "舒適度指數"]

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