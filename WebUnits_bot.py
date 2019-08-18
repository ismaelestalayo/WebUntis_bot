import telebot
import requests
import pandas as pd
import json

from datetime import date

# Author: Ismael Estalayo

TOKEN = ""
MY_ID = 150853329

HEADERS = {
    'Sec-Fetch-Mode': 'cors' ,
    'Sec-Fetch-Site': 'same-origin' ,
    'DNT': '1' ,
    'Accept-Encoding': 'gzip, deflate, br' ,
    'Accept-Language': 'en-US,en;q=0.9,es;q=0.8' ,
    'User-Agent': 'Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/78.0.3872.0 Mobile Safari/537.36',
    'Accept': 'application/json',
    'Referer': 'https://gestion.ehu.es/WebUntis/?school=ehu',
    'Cookie': 'schoolname="_ZWh1"; schoolname="_ZWh1"; JSESSIONID=851928A91F077D9F60EDA49243EDD9FB; ObGAURCookie=blEjfmYSeSPz4hqbjzhjEujaYNstepBrudLz9PQjfw4=',
    'Connection': 'keep-alive'
}

commands = {  
              'start': 'First things first',
              'thisWeek': 'Gets the schedule of this week.',
              'nextWeek': 'Gets the schedule of the next week.',
              'help': 'Shows info about the available commands'
}

bot = telebot.TeleBot(TOKEN)

#Outputs the incoming messages in the console
def listener(messages):
    for m in messages:
        if (m.content_type == 'text') and m.chat.first_name:
            # print the sent message to the console
            print("   >" + m.chat.first_name + " [" + str(m.chat.id) + "]: " + m.text)

            if(m.chat.id != MY_ID):
            	bot.send_message(MY_ID, "[" + m.chat.first_name + "]: " + m.text)

# by default gets schedule for my university
def createURL(elementID=5847, week='2019-10-07', formatId=64, departmentId=238):
    URL = 'https://gestion.ehu.es/WebUntis/api/public/timetable/weekly/data?elementType=1'
    URL += '&elementId=%s' % elementID
    URL += '&date=%s' % week
    URL += '&formatId=%s' % formatId
    URL += '&filter.departmentId=%s' % departmentId
    return URL


def createSchedule(endpoint, verbose=False):
    resp = requests.get(endpoint, headers=HEADERS)
    raw = json.loads(resp.content)
    data = raw['data']['result']['data']
    
    try:
        elements = data['elements']
        elementIds = data['elementIds']
        elementId = str(data['elementIds'][0])
        elementPeriods = data['elementPeriods']

        df = pd.DataFrame( elementPeriods[elementId] )
        df = df.sort_values(by=['date', 'startTime'])
        
        schedule = ""
        for i, group in df.groupby(['date']):
            schedule += ("\n--------------------------------------------\n")
            schedule += "%s-%s-%s \n" % (str(i)[0:4], str(i)[4:6], str(i)[6:8])
            
            for j, row in group.groupby(['lessonId']):
                start = "%.4d" % row.iloc[0]['startTime']
                end = "%.4d" % row.iloc[-1]['endTime']
                schedule += "    🕐%s:%s - %s:%s \n" % (start[:2], start[2:], end[:2], end[2:]) 
                classIds = [elem['id'] for elem in row['elements'].iloc[0]]
                line1 = list(filter(lambda elem: elem['id'] == classIds[0], elements))[0]['name'] + " - "
                line2 = list(filter(lambda elem: elem['id'] == classIds[1], elements))[0]['longName']
                line1 += list(filter(lambda elem: elem['id'] == classIds[2], elements))[0]['name']
                if verbose:
                    schedule += ("      " + line1 + '\n')
                schedule += ("      " + line2 + '\n')
        return schedule
        
    except Exception as ex:
        error = 'Error: \n' + ex + '\n\n'
        error += 'Oopsie Woopsie! Something went wrong...'


# ############################################################################
def main():
    bot = telebot.TeleBot(TOKEN)
    bot.set_update_listener(listener)  # register listener


    @bot.message_handler(commands=['start'])
    def command_start(m):
        cid = m.chat.id 
        # show the new user the help page
        bot.send_message(cid, "Bip, bop, I'm a bot!")
        command_help(m)


    @bot.message_handler(commands=['help'])
    def command_help(m):
        cid = m.chat.id
        help_text = "This are the available commands: \n"
        for key in commands:
            help_text += "/" + key + ": "
            help_text += commands[key] + "\n"

        bot.send_message(cid, help_text)


    # ############################################################################
    @bot.message_handler(commands=['thisWeek'])
    def command_palette(m):
        cid = m.chat.id

        week = date.today().strftime('%Y-%m-%d')
        endpoint = createURL()
        schedule = createSchedule(endpoint)

        bot.send_message(cid, schedule)

    @bot.message_handler(commands=['nextWeek'])
    def command_palette(m):
        cid = m.chat.id

        bot.send_message(cid, 'ooopsie wooopsies')

    bot.polling()

    
    

try:
    main()

except KeyboardInterrupt:
    print("Exiting by Ctrl-C request...")
    

    




