
import json
import requests
import pandas as pd

from datetime import date, datetime, timedelta

pd.set_option("display.max_rows", 30)
pd.set_option("display.max_columns", 20)
pd.set_option('max_colwidth', 150)

URL = 'https://gestion.ehu.es/WebUntis/api/public/timetable/weekly/data?elementType=1&elementId=5847&date=2019-10-07&formatId=64&filter.departmentId=238'
HEADERS = {
    # 'Sec-Fetch-Mode': 'cors' ,
    # 'Sec-Fetch-Site': 'same-origin' ,
    # 'DNT': '1' ,
    # 'Accept-Encoding': 'gzip, deflate, br' ,
    # 'Accept-Language': 'en-US,en;q=0.9,es;q=0.8' ,
    # 'Connection': 'keep-alive'
    'Accept': 'application/json',
    'Cookie': 'schoolname="_ZWh1"; schoolname="_ZWh1"; JSESSIONID=851928A91F077D9F60EDA49243EDD9FB; ObGAURCookie=blEjfmYSeSPz4hqbjzhjEujaYNstepBrudLz9PQjfw4=',
    'Referer': 'https://gestion.ehu.es/WebUntis/?school=ehu',
    'User-Agent': 'Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/78.0.3872.0 Mobile Safari/537.36'
}

resp = requests.get(URL, headers=HEADERS)
raw = json.loads(resp.content)
data = raw['data']['result']['data']

elements = data['elements']
elementIds = data['elementIds']
elementId = str(data['elementIds'][0])
elementPeriods = data['elementPeriods']

df = pd.DataFrame( elementPeriods[elementId] )
df.drop(columns=['lessonCode', 'periodText', 'hasPeriodText', 'hasInfo', 'priority', 'roomCapacity', 'studentCount'], inplace=True)
df = df.sort_values(by=['date', 'startTime'])

date = date.today().strftime('%Y%m%d')
df.query('date==@today')

for i, group in df.groupby(['date']):
    print("\n-----------------------------------------------------------------------------------")
    print("%s-%s-%s" % (str(i)[0:4], str(i)[4:6], str(i)[6:8]))
    
    for j, row in group.groupby(['lessonId']):
        start = "%.4d" % row.iloc[0]['startTime']
        end = "%.4d" % row.iloc[-1]['endTime']
        print("  - %s:%s - %s:%s" % (start[:2], start[2:], end[:2], end[2:]) )
        classIds = [elem['id'] for elem in row['elements'].iloc[0]]
        line1 = list(filter(lambda elem: elem['id'] == classIds[0], elements))[0]['name'] + " - "
        line2 = list(filter(lambda elem: elem['id'] == classIds[1], elements))[0]['longName']
        line1 += list(filter(lambda elem: elem['id'] == classIds[2], elements))[0]['name']
        print("    > " + line1)
        print("    > " + line2)
        