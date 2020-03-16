import calendar
import telebot
import requests
import pandas as pd
import json

from datetime import date, timedelta
from os import path

# Author: Ismael Estalayo

try:
    with open('token.txt', 'r') as f:
        TOKEN = f.read()
except Exception as ex:
    print("> token.txt file not found... \n", ex)
    exit(1)


if path.exists('users.txt'):
    with open('users.txt', 'r') as f:
        USERS = json.load(f)
else:
    print("> users.txt file not found. Creating one... \n")
    with open('users.txt', 'w') as f:
        f.write("{}")
    USERS = {}


MY_ID = 150853329

DAYS = ['Lunes', 'Martes', 'Miercoles', 'Jueves', 'Viernes', 'Sabado', 'Domingo']
MONTHS = ['NULL', 'Ene', 'Feb', 'Mar', 'Abr', 'May', 'Jun', 'Jul', 'Ago', 'Sep', 'Oct',
         'Nov', 'Dic']

HEADERS = {
    'Accept': 'application/json',
    'Cookie': 'schoolname="_ZWh1"; schoolname="_ZWh1"; JSESSIONID=851928A91F077D9F60EDA49243EDD9FB; ObGAURCookie=blEjfmYSeSPz4hqbjzhjEujaYNstepBrudLz9PQjfw4=',
    'Referer': 'https://gestion.ehu.es/WebUntis/?school=ehu',
    'User-Agent': 'Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/78.0.3872.0 Mobile Safari/537.36',
}

COMMANDS = {  
              "start": "First things first",
              "config": "Set your course id",
              "today": "Classes for today (full info)",
              "tomorrow": "Classes for tomorrow (full info)",
              "thisweek": "Summary of this week's classes",
              "nextweek": "Summary of next week's classes",
              "nextnextweek": "Summary of next-next week's classes",
              "help": "Call 911"
}

COURSES = {
    '306-1º-01 Master Teleco': '5883',
    '306-1º-02 Master Teleco': '5903',
    '306-1º-31 Master Teleco': '5885',
    '306-1º-61 Master Teleco': '5889',
    
    '306-1º-01 Master Teleco': '5847',
    '306-2º-16 Master Teleco': '5851',
}

def update_users(users):
    USERS = users


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
    schedule = ""
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
        year, month, day = str(i)[0:4], str(i)[4:6], str(i)[6:8]
        weekDay = DAYS[date(int(year), int(month), int(day)).weekday()]
        month = MONTHS[int(month)]
        schedule += "%s %s %s (%s) \n" % (year, month, day, weekDay)
        schedule += ("———————————————————————\n")
        
        for j, row in group.groupby(['lessonId'], sort=False):
            start = "%.4d" % row.iloc[0]['startTime']
            end = "%.4d" % row.iloc[-1]['endTime']
            schedule += "🕐 %s:%s - %s:%s" % (start[:2], start[2:], end[:2], end[2:])
            classIds = [elem['id'] for elem in row['elements'].iloc[0]]
            
            teacher = list(filter(lambda elem: elem['id'] == classIds[0], elements))[0]['name']
            subject = list(filter(lambda elem: elem['id'] == classIds[1], elements))[0]['longName']
            classroom = list(filter(lambda elem: elem['id'] == classIds[2], elements))[0]['name']
            teacher = teacher.split('-')[0]
            classroom = classroom.split('_')[0]
            
            schedule += (" (%s - %s)\n" % (teacher, classroom))
            schedule += ("      %s\n" % subject)
    except KeyError as ex:
        schedule = 'I could not find any classes for that day.'
    except Exception as ex:
        schedule = 'Oopsie Woopsie! Something went wrong...\n'
        schedule += 'Error: %s' % ex
    return schedule


def createWeekSchedule(endpoint, verbose=False):
    schedule = ""
    resp = requests.get(endpoint, headers=HEADERS)
    raw = json.loads(resp.content)
    data = raw['data']['result']['data']
    
    try:
        elements = data['elements']
        elementIds = data['elementIds']
        elementId = str(data['elementIds'][0])
        elementPeriods = data['elementPeriods']
        
        df = pd.DataFrame(elementPeriods[elementId])
        today = date.today()
        df = df[ df['date'] >= int(today.strftime('%Y%m%d')) ]
        df = df.sort_values(by=['date', 'startTime'])
        if df.empty:
            raise TypeError 
        for i, group in df.groupby(['date']):
            year, month, day = str(i)[0:4], str(i)[4:6], str(i)[6:8]
            weekDay = DAYS[date(int(year), int(month), int(day)).weekday()]
            month = MONTHS[int(month)]
            schedule += "%s %s %s (%s) \n" % (year, month, day, weekDay)
            schedule += ("———————————————————————\n")
            
            for j, row in group.groupby(['lessonId'], sort=False):
                start = "%.4d" % row.iloc[0]['startTime']
                end = "%.4d" % row.iloc[-1]['endTime']
                classType = row.iloc[0]['lessonText']
                
                schedule += "🕐 %s:%s - %s:%s (%s)\n" % (
                    start[:2], start[2:], end[:2], end[2:], classType)
                classIds = [elem['id'] for elem in row['elements'].iloc[0]]
                subject = list(filter(lambda elem: elem['id'] == classIds[1],
                                    elements))[0]['longName']
                if len(subject) > 35:
                    subject = subject[:35] + '...'
                schedule += ("      %s \n" % subject)
            schedule += "\n"
    except KeyError:
        schedule = 'I could not find any classes for that week.'
    except TypeError:
        schedule = 'I could not find any future classes for that week.'
    except Exception as ex:
        schedule = 'Oopsie Woopsie! Something went wrong...\n'
        schedule += 'Error: %s' % ex
    return schedule

# #############################################################################
def main():
    # bot = telebot.TeleBot(TOKEN)
    bot.set_update_listener(listener)  # register listener


    @bot.message_handler(commands=['start'])
    def command_start(m):
        cid = m.chat.id 
        bot.send_message(cid, "Bip, bop, I'm a bot!")
        command_help(m)


    @bot.message_handler(commands=['help'])
    def command_help(m):
        cid = m.chat.id
        help_text = "This are the available commands: \n"
        for key in COMMANDS:
            help_text += "/" + key + ": "
            help_text += COMMANDS[key] + "\n"

        bot.send_message(cid, help_text)


    # #########################################################################
    @bot.message_handler(commands=['today'])
    def command_today(m):
        cid = m.chat.id
        course = USERS.get(str(cid), 0)
        if course != 0:
            course = course['course']
            week = date.today().strftime('%Y-%m-%d')
            endpoint = createURL(elementID=course, week=week)
            day = date.today()
            message = createDaySchedule(endpoint, day)
        else:
            message = "You haven't configured a course yet..."
        
        bot.send_message(cid, message)
    
    @bot.message_handler(commands=['tomorrow'])
    def command_tomorrow(m):
        cid = m.chat.id
        course = USERS.get(str(cid), 0)
        if course != 0:
            course = course['course']
            week = date.today().strftime('%Y-%m-%d')
            endpoint = createURL(elementID=course, week=week)
            day = date.today() + timedelta(1)
            message = createDaySchedule(endpoint, day)
        else:
            message = "You haven't configured a course yet..."
        
        bot.send_message(cid, message)
    
    @bot.message_handler(commands=['thisweek'])
    def command_thisweek(m):
        cid = m.chat.id
        course = USERS.get(str(cid), 0)
        if course != 0:
            course = course['course']
            week = date.today().strftime('%Y-%m-%d')
            endpoint = createURL(elementID=course, week=week)
            message = createWeekSchedule(endpoint)
        else:
            message = "You haven't configured a course yet..."
        
        bot.send_message(cid, message)

    @bot.message_handler(commands=['nextweek'])
    def command_nextweek(m):
        cid = m.chat.id
        course = USERS.get(str(cid), 0)
        if course != 0:
            course = course['course']
            week = (date.today() + timedelta(7)).strftime('%Y-%m-%d')
            endpoint = createURL(elementID=course, week=week)
            message = createWeekSchedule(endpoint)
        else:
            message = "You haven't configured a course yet..."
        
        bot.send_message(cid, message)
    
    @bot.message_handler(commands=['nextnextweek'])
    def command_nextnextweek(m):
        cid = m.chat.id
        course = USERS.get(str(cid), 0)
        if course != 0:
            course = course['course']
            week = (date.today() + timedelta(14)).strftime('%Y-%m-%d')
            endpoint = createURL(elementID=course, week=week)
            message = createWeekSchedule(endpoint)
        else:
            message = "You haven't configured a course yet..."
        bot.send_message(cid, message)
    
    @bot.message_handler(commands=['config'])
    def command_nextnextweek(m):
        cid = m.chat.id
        
        try:
            course = int(m.text.split(" ")[1])
            USERS[str(cid)] = {'course': course, 'name': m.chat.first_name}
            update_users(USERS)
            file_object = open('users.txt', 'w')
            json.dump(USERS, file_object)
            log = 'new user %s configured on %s' % (m.chat.first_name, course)
            bot.send_message(MY_ID, log)
            message = "Updated your course!"
        except IndexError: 
            message = "You did not indicate your course id. Usage\n"
            message += "/config XXXX (where XXXX is the id of the course) \n"
            for key in COURSES:
                message += "  - %s: %s \n " % (key, COURSES[key])
        except ValueError: 
            message = "Ooopsie woopsies, your course id format is not correct!"
        finally:
            bot.send_message(cid, message)
    
    @bot.message_handler()
    def command_404(m):
        cid = m.chat.id
        print(USERS)
        message = "Ooopsie woopsies, that command does not exist!"
        bot.send_message(cid, message)
        
    bot.polling()

    
    

try:
    main()

except KeyboardInterrupt:
    print("> Exiting by Ctrl-C request...")
except ConnectionError:
    print("YIEE1")
except requests.exceptions.ConnectionError:
    print("> Error on the internet connection")
except Exception as ex:
    print("> Not caught exception! \n", ex)
