import pprint
import zulip
import sys
import re
import json
import httplib2
import os
import math
import threading
import numpy as np
from datetime import datetime
from meeting import getAllUsers
from topnews import News
from todo import Todo,displayTodo
from translate import Translate
from location import Location
from weather import fetch_api_key, get_weather
from currencyExchange import fetch_currency_exchange_rate
from summarizer import summarizeDoc
from digest import digest
import schedule
from checkSpam import checkSpam
client = zulip.Client(config_file="~/.zuliprc")

BOT_MAIL = "neo-bot@bint.zulipchat.com"

# Reminder bot format : neo discussion on <subject> at <time> <Date>

class Neo(object):
    '''
    A docstring documenting this bot.
    '''

    def __init__(self):
        self.client = zulip.Client(site="https://bint.zulipchat.com/api/")
        self.subscribe_all()
        self.translate = Translate()
        self.location = Location()
        self.news = News()
        self.subKeys=["hello","sample"]
        self.todoList=[]
    
    #  This will subscribe and listen to messages on all streams.
    def subscribe_all(self):
        json = self.client.get_streams()["streams"]
        streams = [{"name": stream["name"]} for stream in json]
        self.client.add_subscriptions(streams)

    def process(self, msg):
		# array  consisting of all the words
        message_id=msg["id"]
        content = msg["content"].split()
        sender_email = msg["sender_email"]
        ttype = msg["type"]
        stream_name = msg['display_recipient']
        stream_topic = msg['subject']
        timestamp = msg['timestamp']

        if sender_email== BOT_MAIL:
            return 

        if content[0].lower() == "neo" or content[0] == "@**neo**":
            message = ""
            if content[1].lower() == "hello":
                message="Hi"
            elif content[1].lower() == "news":
                try:
                    news = self.news.getTopNews()
                    for item in news:
                        message += "**"+item.title+"**"
                        message += '\n'
                        message += item.des
                        message += '\n\n'
                except:
                    message = "Unable to get news"
           
            elif content[1].lower() == "translate":
                try:
                    message = content[2:]
                    message = " ".join(message)
                    print(message)
                    message = self.translate.translateMsg(message)
                except:
                    message = "Type in following format : neo translate **word**"
            
            elif content[1].lower() == "weather":
                try:
                    api_key = fetch_api_key()
                    if len(content) > 2 and content[2].lower() != "":
                        # Query format: Neo weather London
                        weather = get_weather(api_key, content[2].lower())
                        if str(weather['cod']) != "404":
                            message += "[](http://openweathermap.org/img/w/{}.png)".format(weather['weather'][0]['icon'])
                            message += "**Weather report for {}**\n".format(content[2].lower())
                            message += "Temperature: **{}**\n".format(str(weather['main']['temp']) + "° C")
                            message += "Pressure: **{}**\n".format(str(weather['main']['pressure']) + " hPa")
                            message += "Humidity: **{}**\n".format(str(weather['main']['humidity']) + "%")
                            message += "Wind Speed: **{}**".format(str(weather['wind']['speed']) + " $$m/s^2$$")
                        else:
                            message = "City not found!\nabc"
                    else:
                        message = "Please add a location name."
                except:
                    message = "Something went wrong"
            
            elif content[1].lower() == "geolocation":
                try:
                    place = content[2]
                    result = self.location.getLocation(place)
                    message = "**Latitude** : "+str(result.lat)+"\n"+"**Longitude** : "+str(result.lng)
                except:
                    message = "Type a correct place in following format : neo geolocation **place**"
            
            elif content[1].lower() == "currency":
                if len(content) == 3 and content[2].lower() != "":
                    # Query format: Neo currency USD
                    currency = fetch_currency_exchange_rate("", content[2].upper())
                    message += "**Showing all currency conversions for 1 {}:**\n".format(content[2].upper())
                    for curr in currency['rates']:
                        message += "1 {} = ".format(content[2].upper()) + "{}".format(format(currency['rates'][curr], '.2f')) + " {}\n".format(curr)
                    message += "Last Updated: *{}*".format(currency['date'])
                elif len(content) == 5 and content[2].lower() != "" and content[4].lower() != "":
                    # Query format: Neo currency INR to USD
                    currency = fetch_currency_exchange_rate(content[2].upper(), content[4].upper())
                    message += "1 {} = ".format(content[4].upper()) + "{}".format(format(currency['rates'][content[2].upper()], '.2f')) + " {}\n".format(content[4].upper())
                    message += "Last Updated: *{}*".format(currency['date'])
                else:
                    message = "Please ask the query in correct format."
            
            elif content[1].lower() == "todo":
                # Has to do some more modifications
                try:
                    if content[2].lower() == "add":
                        todoItem=" ".join(content[3:]).lower()
                        Todo("add",self.todoList,todoItem)
                        message="** The todo is added **\n The current Todo List is :\n\n"
                        message=displayTodo(message,self.todoList)
                    elif content[2].lower() =="done":
                        if content[3].lower().isdigit(): 
                            itemNo=int(content[3].lower())
                            # print(itemNo)
                            message+="** The item is marked as done **\n"
                            Todo("done",self.todoList,"",itemNo)
                            message=displayTodo(message,self.todoList)
                        else:
                            message="Enter the Todo item number"
                    elif content[2].lower() =="undone":
                        if content[3].lower().isdigit(): 
                            itemNo=int(content[3].lower())
                            # print(itemNo)
                            message+="** The item is marked as undone **\n"
                            Todo("undone",self.todoList,"",itemNo)
                            message=displayTodo(message,self.todoList)
                        else:
                            message="Enter the Todo item number"
                    elif content[2].lower() == "remove":
                        if content[3].lower()!="all":
                            if content[3].lower().isdigit():
                                itemNo=int(content[3].lower())
                                Todo("remove",self.todoList,"",itemNo)
                                message="** The todo item is removed **\nThe current Todo List is :\n\n"
                                message=displayTodo(message,self.todoList)
                            else:
                                message="Enter the Todo item number"
                        elif content[3].lower() == "all":
                            Todo("remove_all",self.todoList,"",-1)
                            message="The Todo list is cleared"
                        else:
                            message="Invalid todo command"
                    else:
                        message="Invalid todo command."
                except:
                    message = "Something went wrong"
            elif content[1].lower()=="summarize":
                try:
                    sentenceCount=int(content[2].lower())
                    summarizerType=content[3].upper()
                    document=" ".join(content[4:]).lower()
                    summary=summarizeDoc(summarizerType,document,sentenceCount)
                    message="The summary is:\n"+summary
                except:
                    message="Something went wrong with the command you typed. Please check"
            elif content[1].lower()=="digest":
                # Get all users
                (message,summary)=digest(stream_name,message_id,sender_email,BOT_MAIL)
                message+="\n** The summary of the messages is : **\n"+summary
            elif content[1].lower() == "checkspam":
                message = ""
                users = client.get_members()
                emails = []
                flag_admin=1
                for member in users["members"]:
                    if(member["email"]==sender_email):
                        if(not member["is_admin"]):
                            flag_admin=0
                            break
                    emails.append(member["email"])
                if(flag_admin):  
                    results = checkSpam("announce",message_id,emails)
                    flag=1
                    for item in results:
                        if((item.similarityRank > 5) and (item.timeRank > 3)):
                            message += "**"+item.email+"** : Suspected\n"
                            flag=0
                            print(message)
                    if(flag):
                        message = "There is no suspected users"
                else:
                    message = "Function access denied"
            elif content[1].lower() == "discussion":
                # Reminder bot format : neo discussion on <subject> at <time> <Date>
                print(content)

                # Get subject
                subject = ""
                i = 0
                while content[i].lower() != "on":
                    i += 1
                i += 1
                while content[i].lower() != "at":
                    subject += content[i] + " "
                    i += 1
                print("Subject: {}".format(subject))

                
                # time (Assumed to be UTC)
                time = ""
                i = 0
                while content[i].lower() != "at":
                    i += 1
                i += 1
                time += content[i]
                i += 2
                date = content[i]
                print("Time: {}".format(time))
                print("Date: {}".format(date))
                privateText = "{} arranged a meeting about {} at {} on {}.".format(sender_email, subject, time, date)
                emails = getAllUsers(sender_email, BOT_MAIL)
                print(emails)
                for email in emails:
                    request = {
                        "type": "private",
                        "to": email,
                        "content": privateText
                    }
                    self.client.send_message(request)
                message = "Meeting arranged successfully."
                # print("abc {}".format(timestamp))
                
                # Reminder
                dt = datetime.utcnow()
                print(dt)
                dt64 = np.datetime64(dt)
                ts = (dt64 - np.datetime64('1970-01-01T00:00:00Z')) / np.timedelta64(1, 's')
                currSec = int(ts)
                print("Timestamp now: {}".format(currSec))
                meetingTime = date + " " + time
                dt64 = np.datetime64(meetingTime)
                ts = (dt64 - np.datetime64('1970-01-01T00:00:00Z')) / np.timedelta64(1, 's')
                meetingSec = int(ts)
                print("Timestamp meeting: {}".format(currSec))
                diff = meetingSec - currSec - 1800
                if diff > 0:
                    print("Reminder after {} seconds".format(diff))
                    privateText = "REMINDER: {} arranged a meeting about {} at {} on {}.".format(sender_email, subject, time, date)
                    def abc():
                        print("REMINDER")
                        for email in emails:
                            request = {
                                "type": "private",
                                "to": email,
                                "content": privateText
                            }
                            result = self.client.send_message(request)
                            print("Email:{}, Status:{}".format(email, result['result']))
                        timer.cancel()
                    timer = threading.Timer(diff, abc)
                    timer.start()
            else:
                message="HELP options : \n"
                message += "**1**. To show top 10 news : **neo news**\n"
                message += "**2**. To set a meeting easier : **neo discussion on <subject> at <time> <date>**\n"
                message += "**3**. To check spam users : **neo checkspam**\n"
                message += "**4**. To summerize any paragraph : **neo summarize <sentence count> <summarization type> <sentences>**\n"
                message += "**5**. To get the summary of previous messages in the stream : **neo digest**\n"
                message += "**6**. ToDo Funtionalities : **neo todo add <name of task>**\n"
                message += "** --** **neo todo done <index of task>**\n"
                message += "** --** **neo todo remove/undone <index of task>**\n"
                message += "** --** **neo todo remove all**\n"
                message += "**7**. To display relative currency values : **neo currency <currency type>**\n"
                message += "** --** **neo currency <type 1> to <type 2>**\n"
                message += "**8**. To get the geolocation : **neo geolocation <place name>**\n"
                message += "**9**. To translate any language to english : **neo translate <word>**\n"
                message += "**10**. To get the weather report of a place : **neo weather <place>**\n"
            self.client.send_message({
                "type": "stream",
                "subject": msg["subject"],
                "to": msg["display_recipient"],
                "content": message
            })

def main():
    neo= Neo()
    neo.client.call_on_each_message(neo.process)

if __name__ == "__main__":
	try:
		main()
	except KeyboardInterrupt:
		print("Thanks for using Neo Bot. Bye!")
		sys.exit(0)
