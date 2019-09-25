import telebot
import requests
import pandas as pd
import json

from datetime import date, timedelta

# Author: Ismael Estalayo

TOKEN = open('token.txt', 'r').read()
MY_ID = 150853329

HEADERS = {
    'Accept': 'application/json',
    'Cookie': 'schoolname="_ZWh1"; schoolname="_ZWh1"; JSESSIONID=851928A91F077D9F60EDA49243EDD9FB; ObGAURCookie=blEjfmYSeSPz4hqbjzhjEujaYNstepBrudLz9PQjfw4=',
    'Referer': 'https://gestion.ehu.es/WebUntis/?school=ehu',
    'User-Agent': 'Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/78.0.3872.0 Mobile Safari/537.36',
}

commands = {  
              'start': 'First things first',
              'thisweek': 'Gets the schedule of this week.',
              'nextweek': 'Gets the schedule of the next week.'
}

courses = {
    '306-1º-01 Master Teleco': '5883',
    '306-1º-02 Master Teleco': '5903',
    '306-1º-31 Master Teleco': '5885',
    '306-1º-61 Master Teleco': '5889',
    
    '306-1º-01 Master Teleco': '5847',
    '306-1º-31 Master Teleco': '5849',
    '306-2º-16 Master Teleco': '5851',
    '306-2º-46 Master Teleco': '5853',
}

bot = telebot.TeleBot(TOKEN)

# Outputs the incoming messages in the console
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


def createDaySchedule(endpoint, day=date.today(), verbose=False):
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
        
        i = day.strftime('%Y%m%d')
        group = df.query('date==@i')
        
        schedule = ("\n--------------------------------------------\n")
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
    except KeyError as ex:
        schedule = 'I could not find any classes for that day.'
    except Exception as ex:
        schedule = 'Oopsie Woopsie! Something went wrong...\n'
        schedule += 'Error: %s' % ex
    return schedule


def createWeekSchedule(endpoint, verbose=False):
    resp = requests.get(endpoint, headers=HEADERS)
    raw = json.loads(resp.content)
    data = raw['data']['result']['data']
    
    try:
        elements = data['elements']
        elementIds = data['elementIds']
        elementId = str(data['elementIds'][0])
        elementPeriods = data['elementPeriods']
        
        df = pd.DataFrame(elementPeriods[elementId])
        df = df.sort_values(by=['date', 'startTime'])
        schedule = ""
        for i, group in df.groupby(['date']):
            schedule += ("\n--------------------------------------------\n")
            schedule += "%s-%s-%s \n" % (str(i)[0:4], str(i)[4:6], str(i)[6:8])
            
            for j, row in group.groupby(['lessonId']):
                start = "%.4d" % row.iloc[0]['startTime']
                end = "%.4d" % row.iloc[-1]['endTime']
                schedule += "    🕐%s:%s - %s:%s \n" % (
                    start[:2], start[2:], end[:2], end[2:])
                classIds = [elem['id'] for elem in row['elements'].iloc[0]]
                line1 = list(filter(lambda elem: elem['id'] == classIds[0],
                                    elements))[0]['name'] + " - "
                line2 = list(filter(lambda elem: elem['id'] == classIds[1],
                                    elements))[0]['longName']
                line1 += list(filter(lambda elem: elem['id'] == classIds[2],
                                     elements))[0]['name']
                if verbose:
                    schedule += ("      " + line1 + '\n')
                schedule += ("      " + line2 + '\n')
    except KeyError:
        schedule = 'I could not find any classes for that week.'
    except Exception as ex:
        schedule = 'Oopsie Woopsie! Something went wrong...\n'
        schedule += 'Error: %s' % ex
    return schedule

# #############################################################################
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


    # #########################################################################
    @bot.message_handler(commands=['today'])
    def command_today(m):
        cid = m.chat.id

        week = date.today().strftime('%Y-%m-%d')
        endpoint = createURL(week=week)
        day = date.today()
        schedule = createDaySchedule(endpoint, day)

        bot.send_message(cid, schedule)
    
    @bot.message_handler(commands=['tomorrow'])
    def command_tomorrow(m):
        cid = m.chat.id

        week = date.today().strftime('%Y-%m-%d')
        endpoint = createURL(week=week)
        day = date.today() + timedelta(1)
        schedule = createDaySchedule(endpoint, day)

        bot.send_message(cid, schedule)
    
    @bot.message_handler(commands=['thisweek'])
    def command_thisweek(m):
        cid = m.chat.id

        week = date.today().strftime('%Y-%m-%d')
        endpoint = createURL(week=week)
        schedule = createWeekSchedule(endpoint)

        bot.send_message(cid, schedule)

    @bot.message_handler(commands=['nextweek'])
    def command_nextweek(m):
        cid = m.chat.id

        week = (date.today() + timedelta(7)).strftime('%Y-%m-%d')
        endpoint = createURL(week=week)
        schedule = createWeekSchedule(endpoint)

        bot.send_message(cid, schedule)
    
    @bot.message_handler()
    def command_404(m):
        print("Ooopsie woopsies, that command does not exist!")
        
    bot.polling()

    
    

try:
    main()

except KeyboardInterrupt:
    print("Exiting by Ctrl-C request...")
    

    




