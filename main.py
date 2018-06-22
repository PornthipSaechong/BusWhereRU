

from handler.handler import Handler
from google.appengine.api import memcache
from google.appengine.api import taskqueue

from database.user import User

import hmac
import hashlib
import datetime
import logging
import json
import urllib, urllib2, urlparse
import random
import traceback
import re

from keys import Keys


debug=True

BOTID = Keys.getBotID()
DATAMALL = Keys.getDataMallKeys()

#### EMOJI
screaming_face = '\xF0\x9F\x98\xB1'
grinning_face = '\xF0\x9F\x98\x81'
hatching_chick = '\xF0\x9F\x90\xA3'
smirking_face = '\xF0\x9F\x98\x8F'
delicious_face = '\xF0\x9F\x98\x8B'
smiley_eye_close = '\xF0\x9F\x98\x86'
white_smiley = '\xE2\x98\xBA'

"""
Commands:
stop - show timing for all bus at a given bus stop
list - list saved bus stop codes
save - save bus stop number
alarm - set reminder to catch a bus at a stop
remove - remove saved bus stop code
"""

class Parser():

    def getDateTimeFromNow(self,time,now): ## parse datetime of estimate arrival, compare with current time and return difference in minutes + seconds
        if time:
            time = time[:-6]
            dt = datetime.datetime.utcnow().strptime(time,"%Y-%m-%dT%X")
            seconds = (dt - now).total_seconds()
            minutes = int(seconds / 60)
            if minutes < 1:
                return "ARR"
            else:
                return str(minutes)
        else:
            return 'NA'

    def getPadding(self,text,rowPad):
        fixPad = 16
        pad = ''.join([" " for i in range(fixPad - len(text) + (rowPad-len(text)))])
        return pad

    def parseBusStopInfo(self,data):
        if data["Services"]:
            busStopCode = data["BusStopCode"]
            html = "Bus timings for bus stop: <i>" + busStopCode + "</i>"
            html += "\n<b>Service No.   Bus1              Bus2               Bus3</b>" ## header
            now = datetime.datetime.now() + datetime.timedelta(hours=8)
            for s in data["Services"]:
                bus1 = self.getDateTimeFromNow(s["NextBus"]["EstimatedArrival"],now) + " " +s["NextBus"]["Load"]
                bus2 = self.getDateTimeFromNow(s["NextBus2"]["EstimatedArrival"],now) + " " +s["NextBus2"]["Load"]
                bus3 = self.getDateTimeFromNow(s["NextBus3"]["EstimatedArrival"],now) + " " +s["NextBus3"]["Load"]
                html += "\n"
                html += s["ServiceNo"]
                html += self.getPadding(s["ServiceNo"],4)
                html += bus1
                html += self.getPadding(bus1,7)
                html += bus2
                html += self.getPadding(bus2,7)
                html += bus3
                html += self.getPadding(bus3,7)
            html += "\n SEA (for Seats Available) SDA (for Standing Available) LSD (for Limited Standing)"
            return True, html
        else:
            return False, "<b>Bus stop not found</b> Please provide another stop code."

    def parseDataAsButton(self,data):
        validArray = []
        for d in range(len(data)):
            validArray.append({"text":data[d], "callback_data": data[d]})
        return validArray

    def parseDataAsButtonDict(self,data):
        validArray = []
        for k,v in data.iteritems():
            validArray.append({"text":v, "callback_data": k})

        return validArray

    def checkAlarmTimeData(self,data):
        # { 'alarm1': '54621', 'alarm2': '07.50am', 'alarm3': '5'} in '<<chat_id>>_data'
        r = re.search('([0-9]{1,2})\\.([0-9]{2})(am|pm){1}', data)
        if r:
            groups = list(r.groups())
            try:
                groups[0] = int(groups[0])
                if groups[0] > 12:
                    # logging.info("Invalid hour:" + groups[0])
                    raise Exception('Invalid value')

                if groups[2] == 'pm': ## convert to 12 time format
                    groups[0] += 12

                groups[1] = int(groups[1])
                if groups[1] > 60:
                    # logging.info("Invalid minute:" + groups[1])
                    raise Exception('Invalid value')

                return groups
            except:
                return None
        else:
            return None

    def setAlarmTaskQueue(self,alarm_data,interval,chat_id):

        
        def getETA(alarm_data):

            hour = alarm_data["alarm2"][0]
            minute = alarm_data["alarm2"][1]
            period = alarm_data["alarm2"][2]


            now = datetime.datetime.now()
            # logging.info(hour)
            hour = hour - 8
            if hour < 0:
                ## need to set to 24 interval:
                hour += 24
            # logging.info('log now---')
            # logging.info(now.hour)
            # logging.info(now.minute)
            # logging.info('log now---')
            # logging.info('input ---')
            # logging.info(hour)
            # logging.info(minute)
            # logging.info('input ---')
            # # hourDiff =  hour - now.hour
            # logging.info('input ---1')
            # logging.info(hourDiff)
            if hourDiff < 0:
                hourDiff = 24 - (now.hour + 8)
                hourDiff += hour + 8
            else:
                hourDiff = abs(hourDiff)

            minuteDiff = minute - now.minute
            if minuteDiff < 0:
                minuteDiff = (60-now.minute) + minute
                hourDiff -= 1
            else:
                minuteDiff = abs(minuteDiff)

            countDown = ((hourDiff * 60) + minuteDiff)*60
            # logging.info(hourDiff)
            # logging.info(minuteDiff)
            # logging.info("count down:"+str(countDown))
            return countDown

        tq_data = {
            'params': {
                'busStop': alarm_data["alarm1"],
                'chat_id': chat_id
            },
            'countdown': getETA(alarm_data)
        }
        try:
            ## set taskqueue
            taskqueue.add(
                queue_name='alarmQueue',
                url='/run_alarm',
                method='post',
                params=tq_data["params"],
                countdown=tq_data["countdown"]
            )
        except Exception, e:
            logging.error('Problem adding task')
            logging.error(e)
        return 

    def getLocationData(self,data):
        location_data = {}
        for s in data["Services"]:
            logging.info(s["ServiceNo"])
            if "NextBus" in s.keys():
                location_data[s["ServiceNo"]] = {"location": {}}
                location_data[s["ServiceNo"]]["location"]["latitude"] = s["NextBus"]["Latitude"]
                location_data[s["ServiceNo"]]["location"]["longitude"] = s["NextBus"]["Longitude"]

        return location_data

    def parseButtonRow(self,data):
        def divideChunks(arr,n):
            for i in range(0,len(arr),n):
                yield arr[i:i+n]
        chunks = list(divideChunks(data,8))
        return chunks


class Alarm(Handler):
    def post(self):
        logging.info('running timed alarm')
        logging.info(self.request.body)

        params = urlparse.parse_qs(self.request.body)
        logging.info(params)
        parser = Parser()

        contents = callDataMall(params["busStop"][0])
        text = "Time to go!\n"
        text += parser.parseBusStopInfo(contents)
        reply = {"chat_id":params["chat_id"][0],"text":text, "parse_mode":"HTML"}
        reply = urllib.urlencode(reply)

        url = "https://api.telegram.org/bot{}/sendMessage?{}".format(BOTID,reply)

        response = urllib2.urlopen(url).read()
        response = json.loads(response)
        if response.get("ok") == True:
            chat_id = response["result"]["chat"]["id"]
        else:
            logging.info("fail")

def callDataMall(busStop):
    url = DATAMALL['url'].format(busStop)
    request = urllib2.Request(url, headers={"Accept" : "application/json", "AccountKey": DATAMALL["key"]})
    contents = urllib2.urlopen(request).read()
    contents = json.loads(contents)
    return contents

def sendMessage(sendType, chat_id, text, reply_markup, obj_res, parse_mode):
    func = "sendMessage"

    if sendType == "text":
        reply = {"chat_id":chat_id,"text":text, "parse_mode":"HTML"}
        
    elif sendType == "button":
        reply = {"chat_id":chat_id, "text":text, "reply_markup": json.dumps({"inline_keyboard":reply_markup})}

    elif sendType == "location":
        func = "sendLocation"
        obj_res["chat_id"] = chat_id
        reply = obj_res

    if parse_mode:
        reply["parse_mode"] = parse_mode
    # encode and send to telegram chat
    reply = urllib.urlencode(reply)

    url = "https://api.telegram.org/bot{}/{}?{}".format(BOTID,func,reply)
    # logging.info(url)
    response = urllib2.urlopen(url).read()
    response = json.loads(response)
    if response.get("ok") == True:
        chat_id = response["result"]["chat"]["id"]
    else:
        logging.info("fail")


class BusStop(Handler):

    def post(self):

        try:
            ## start - init params

            sendType = "text"
            parser = Parser()
            reply_markup = []
            text_msg = None
            text = None
            obj_res = None
            parse_mode = None

            request = json.loads(self.request.body)
            logging.info(request)
            
            if "message" in request.keys():
                message = request["message"]
            else:
                message = request["callback_query"]["message"]
                text_msg = request["callback_query"]["data"]
            chat_id = str(message["chat"]["id"])

            fromUser = message["from"]
            if message["chat"]["type"] == "group":             
                firstname = fromUser["first_name"]
                lastname = fromUser["last_name"]
            else:
                firstname = message["chat"]["first_name"]
                lastname = message["chat"]["last_name"]
            ## end - init params

            ## response for when user left the chat
            if "left_chat_member" in message and message["left_chat_member"]["username"]=="PickAFooodBot":
                text = "Thanks for using BusWhereRU. BB have a good day!"
            ## response for when user join chat
            elif (message["chat"]["type"] == "group" and "new_chat_member" in message and message["new_chat_member"]["username"]=="PickAFooodBot") or (message["text"]=="/start"):
                text = """HELLOOO Thank you for adding BusWhereRU bot. """
            ## repsonse for user commands
            else:
                if not text_msg:
                    text_msg = message["text"]

                if not text_msg:
                    text = "Invalid command"

                if "/stop" in text_msg:
                    if memcache.get("{}".format(chat_id)) == "stop":
                        text = "Waiting for your bus stop number..."
                    else:
                        text = "Please tell me the bus stop number."
                        command = "stop"
                        memcache.set("{}".format(chat_id),command)

                elif "/list" in text_msg:
                    command = "list"
                    memcache.set("{}".format(chat_id),command)
                    user = User.by_telegramID(chat_id).get()
                    if user:
                        if len(user.busStopList) == 0:
                            text = "You did not save any bus stop."
                        else:
                            text = "Your saved bus stop codes:"
                            sendType = "button"
                            reply_markup = [parser.parseDataAsButton(user.busStopList)]
                    else:
                        text = "You did not save any bus stop."

                elif "/save" in text_msg:
                    if memcache.get("{}".format(chat_id)) == "save":
                        text = "Waiting for your bus number to save..."
                    else:
                        text = "Please tell me the bus stop code to save :)"
                        command = "save"
                        memcache.set("{}".format(chat_id),command)

                elif "/alarm" in text_msg:
                    if memcache.get("{}".format(chat_id)) == "alarm1":
                        text = "Waiting for your bus stop number to set alarm..."
                    else:
                        text = "1. Please tell me the bus stop code to set alarm."
                        command = "alarm1"
                        memcache.set("{}".format(chat_id),command)

                elif "/remove" in text_msg:
                    if memcache.get("{}".format(chat_id)) == "remove1":
                        text = "Waiting for your selection for bus number..."
                    else:
                        command = "remove"
                        memcache.set("{}".format(chat_id),command)
                        user = User.by_telegramID(chat_id).get()
                        if user:
                            if len(user.busStopList) == 0:
                                text = "You did not save any bus stop."
                            else:
                                text = "Choose which bus stop code to remove:"
                                sendType = "button"
                                reply_markup = [parser.parseDataAsButton(user.busStopList)]
                        else:
                            text = "You did not save any bus stop."

                elif "/location" in text_msg:
                    location_data = memcache.get("{}_location".format(chat_id))
                    if location_data:
                        memcache.set('{}_data'.format(chat_id),location_data)
                        command = "location"
                        memcache.set("{}".format(chat_id),command)
                        text = "Choose available buses:"
                        sendType = "button"
                        reply_markup = parser.parseButtonRow(parser.parseDataAsButton(location_data.keys()))
                    else:
                        text = "Invalid command"

                else:
                    command = memcache.get("{}".format(chat_id))
                    # logging.info('command: ' + command)
                    try:
                        text_msg = int(text_msg)
                    except:
                        text = "Invalid bus stop/number"

                    

                    if command == "stop" or command == "list":      
                        contents = callDataMall(text_msg)
                        found, text = parser.parseBusStopInfo(contents)
                        parse_mode = "html"
                        sendType = "button"
                        if found:
                            reply_markup = [parser.parseDataAsButtonDict({"/location": "SHOW LOCATION"})]
                            ## save location data for when user click on show location
                            location_data = parser.getLocationData(contents)
                            memcache.set('{}_location'.format(chat_id),location_data)
                        
                    if command == "save":
                        # save bus stop to user
                        user = User.by_telegramID(chat_id).get()
                        if user:
                            # check if new bus stop is in the list, if not add new stop code
                            if text_msg in user.busStopList:
                                text = "Seems like you have already saved this bus stop code"
                                sendType = "button"
                                reply_markup = [parser.parseDataAsButton(user.busStopList)]
                            else:
                                ## check if bus stop code to add is valid
                                contents = callDataMall(text_msg)

                                if contents["Services"]:
                                    user.add_to_list(text_msg)
                                    user.put()
                                    text = "Successfully saved bus stop"
                                    sendType = "button"
                                    reply_markup = [parser.parseDataAsButton(user.busStopList)]
                                else:
                                    text = "Invalid bus stop code"
                        else:
                            contents = callDataMall(text_msg)

                            if contents["Services"]:
                                ## create user if this chat did not exist before
                                user = User(telegramID=chat_id, firstname=firstname, lastname=lastname)
                                user.add_to_list(text_msg)
                                user.put()
                                text = "Successfully saved bus stop."
                                sendType = "button"
                                reply_markup = [parser.parseDataAsButton(user.busStopList)]
                            else:
                                text = "Invalid bus stop code"

                    if command == "remove":
                        try:
                            user = User.by_telegramID(chat_id).get()
                            if user:
                                user.remove_from_list(text_msg)
                                user.put()
                                text = "Successfully removed bus stop code" + str(text_msg) + "."
                                if len(user.busStopList) == 0:
                                    sendType = "text"
                                    text += " No bus stop available."
                                else:
                                    sendType = "button"
                                    reply_markup = [parser.parseDataAsButton(user.busStopList)]
                            else:
                                text += "You did not save any bus stop."
                        except Exception,e:
                            logging.error(e)
                            text = "Invalid bus stop code"

                    if "alarm" in command:
                        if command == "alarm1":
                            ## set busStop code in cache
                            contents = callDataMall(text_msg)
                            if contents["Services"]:
                                alarm_data = {'alarm1': text_msg}
                                memcache.set('{}_data'.format(chat_id),alarm_data)
                                command = "alarm2"
                                memcache.set("{}".format(chat_id),command)
                                text = "Successfully set bus stop as " + str(text_msg) +"\n"
                                text += "2. Please tell me the time you should reach the bus stop."
                            else:
                                text = "Invalid bus stop code"
                        elif command == "alarm2":
                            parsedTime = parser.checkAlarmTimeData(text_msg)
                            if parsedTime:
                                alarm_data = memcache.get('{}_data'.format(chat_id))
                                alarm_data["alarm2"] = parsedTime
                                memcache.set('{}_data'.format(chat_id),alarm_data)
                                command = "alarm3"
                                memcache.set("{}".format(chat_id),command)
                                text = "Successfully set time to" + str(text_msg) + "\n"
                                text += "3. Please tell me amount of time you need to be at bus stop."
                            else:
                                text = "Invalid time"
                        elif command == "alarm3":
                            try:
                                interval = int(text_msg)
                                alarm_data = memcache.get('{}_data'.format(chat_id))
                                parser.setAlarmTaskQueue(alarm_data, interval, chat_id)
                                ## clear command
                                memcache.set("{}".format(chat_id),'')
                                text = "Successfully set buffer time to: " + str(text_msg)
                            except Exception, e:
                                text = "Invalid minutes"

                    if command == "location":
                        location_data = memcache.get("{}_location".format(chat_id))
                        sendType = "location"
                        text = "location"
                        obj_res = location_data[str(text_msg)]["location"]

            if text:
                sendMessage(sendType, chat_id, text, reply_markup, obj_res, parse_mode)

            self.response.out.write("Response sent")
            return
        except Exception,e:
            traceback.print_exc()
            # logging.error(e)

    def get(self):

        self.response.out.write("Nice seeing you here")
        return

