from slack_sdk.errors import SlackApiError
from json.decoder import JSONDecodeError

from datetime import datetime
from threading import Timer
import json, pytz, copy
import globals

## Start of solver commands functions

# Use the Timer class imported above to creat two repeating timers. One to save user data and the other to send reminder
class RepeatTimer0(Timer):
    def run(self):
        while not self.finished.wait(self.interval):
            self.interval = 3600
            self.function(*self.args, **self.kwargs) 
          
class RepeatTimer1(Timer):
    def run(self):
        while not self.finished.wait(self.interval):
            self.interval = 3600
            self.function(*self.args, **self.kwargs)

## Start of solver commands functions
            
class Solver():
    def __init__(self, client):
        self.client = client
        self.users = {}                # {user : {'solves': [list], 'ts': [list], 'flag' : boolean, 'msg_ts' : float}}
        self.ignore = []               # [user_id, ...]
        self.duels = {}                # {(user1, user2) : { user1 : {'submissions' : int, 'total' : int}, { user2 : {'submissions' : int, 'total' : int}, length : 4, duel_ts : timestamp}
        self.duel_instances = {}       # {user : {'instances' : int , 'wins' : int , 'loses' : int}}
        self.pending_duels = []
        self.__get_data()
        self.__run_tmethods()
    
    """Commands for solver"""
    def start(self, ack, body, respond):
        ack()
        user = body['user_id']
        try:
          if body['text'].lower() == "silent":
            silent_ch = True
          else:
            respond("Looks like you used the wrong parameter try /start silent")
            silent_ch = False
            return
        except KeyError:
            silent_ch = False

        if user not in globals.G_Users:
            globals.G_Users[user] = {'solves' : [],
                                     'ts' : [],
                                     'flag' : True,
                                     'silent' : silent_ch,
                                    }
            if globals.G_Users[user]['silent']:
              respond("Lets start solving cases silently!")
            else:
              respond("Lets start solving cases!")
        else:
            respond("You're already solving cases!")

    # This method will take input from main, all other methods will be handled internally  
    def commands(self, event, ack):
        ack()
        text = event['text']
            
        # Adds solvers input to solver list. Outputs total solves so far as direct message to user
        if text.isdigit() and 0 <= int(text) <= 99:
            self.__add(event['user'], event['text'], event['channel'], event['ts'])
        
        # Remove the last solve and timestamp from the users dictionary
        elif event['text'].lower() == 'oops':
            self.__oops(event['user'], event['channel'], event['ts'])
        
        # Outputs users total solves and removes solver from dictionary
        elif event['text'].lower() == 'eod':
            self.__eod(event['user'], event['channel'], event['ts'])
        
        # Outputs users posted solves and the time submitted
        elif event['text'] == 'solves':
            self.__solves(event['user'], event['channel'], event['ts'])

    def ignore_toggle(self, body, ack):
    # This function will allow users to toggle whether they are accepting duels by adding their user_id to an ignore list
        ack()
        user = body["user_id"]
        if user not in self.ignore:
            self.ignore.append(user)
            self.client.chat_postEphemeral(channel=body["channel_id"],
                                           user=user,
                                           text="Now ignoring duels"
                                          )
        else:
            self.ignore.remove(user)
            self.client.chat_postEphemeral(channel=body["channel_id"],
                                           user=user,
                                           text="Now accepting duels"
                                          )
    
    """Public Methods for Duel function"""
    def request_duel(self,body,ack,logger):
    # Send invite to user from slash command (/duel <@user>) if not on ignore list, toggle ignore command
        logger.info(body)
        ack()
        user_snd = body["user_id"]
        try:
        #Check if the duel invite is being input correctly and send error response if not
            user_recv,recv_throw_away = body['text'].split('|')
        except ValueError as e:
            user_recv,recv_throw_away = ("X","X")
            
            self.client.chat_postEphemeral(channel=body["channel_id"],
                                           user=user_snd,
                                           text="Please use the following format /dual [@user]"
                                          )
            return
        
        user_recv = user_recv[2:]
        if user_snd in globals.G_Duel_Instances.keys() and globals.G_Duel_Instances[user_snd]['instances'] > 2:
        # Check if user sending duel request has maximum number of duels running
            self.client.chat_postEphemeral(channel=body["channel_id"],
                                           user=user_snd,
                                           text="You're dueling the maximum number of people!"
                                          )
            return
        duel_check = [(user_snd,user_recv),(user_recv,user_snd)]  
        for c in duel_check:
            if c in globals.G_Duels.keys():
                self.client.chat_postEphemeral(channel=body["channel_id"],
                                               user=user_snd,
                                               text="Looks like you are already dueling that user")
                return
          
        if user_snd not in globals.G_Users:
            self.client.chat_postEphemeral(channel=body["channel_id"],
                                           user=user_snd,
                                           text="You must be solving cases in order to duel someone. Type /start to get started!")
            return
        elif user_recv not in globals.G_Users:
            self.client.chat_postEphemeral(channel=body["channel_id"],
                                           user=user_snd,
                                           text=f"It looks like <@{user_recv}> is not currently solving cases. Check back later!")
            return
        
        if user_snd == user_recv:
            self.client.chat_postEphemeral(channel=body["channel_id"],
                                           user=user_snd,
                                           text="Nice try smarty pants! You can't duel yourself!")
            return
          
        if user_recv in self.pending_duels:
            self.client.chat_postEphemeral(channel=body["channel_id"],
                                           user=user_snd,
                                           text=f"It looks like <@{user_recv}> has not accepted their last duel request. Lets give them a minute.")
            return  
          
        
        if user_recv in globals.G_Duel_Instances.keys() and globals.G_Duel_Instances[user_recv]['instances'] > 2:
        # Check if user receiving duel request has maximum number of duels running
            self.client.chat_postEphemeral(channel=body["channel_id"],
                                           user=user_snd,
                                           text="They're dueling the maximum number of people!"
                                          )
        try:
            result = self.client.users_info(user=user_recv)
            if user_recv not in self.ignore:
                self.client.chat_postMessage(channel=user_snd,
                                             text=f"You have successfully challenged <@{user_recv}> to a solve contest!\nWe will let you know once they have responded to your request!"
                                            )
                self.duel_init['blocks'][0]['text']['text'] = self.duel_init['blocks'][0]['text']['text'] + f"<@{user_snd}>!"

                self.client.chat_postMessage(channel=user_recv,
                                             blocks=self.duel_init["blocks"],
                                             text=f"You have been challenged by <@{user_snd}> to a solve contest!\n How do you respond?"
                                            )
                self.pending_duels.append(user_recv)
            else:
                self.client.chat_postEphemeral(channel=body["channel_id"],
                                               user=user_snd,
                                               text="That user is not currently accepting duel requests."
                                              )
        except SlackApiError as e:
            self.client.chat_postEphemeral(channel=body["channel_id"],
                                           user=user_snd,
                                           text=f"Unable to send a dual request. Check that the user exists!"
                                          )
            
    def accept_duel(self,body,ack,say,logger,respond):
        ack()
        try:
            respond("You accepted the challenge!", 
                    replace_original=True
                   )
            throw_away,user_snd = body["message"]["text"].split("@")
            user_snd = user_snd.split(">")[0]
            user_recv = body['user']['id']
            self.client.chat_postMessage(channel=user_snd,
                                         text=f"Your solve contest with <@{user_recv}> has been accepted!"
                                        )
            self.pending_duels.remove(user_recv)
            # Add users to dictionary tracking duel instances for users and append dictionary if already added
            if user_snd in globals.G_Duel_Instances.keys():
                globals.G_Duel_Instances[user_snd]['instances'] += 1
            else:
                globals.G_Duel_Instances[user_snd] = {
                                        'instances':0,
                                        'wins':0,
                                        'loses':0}
            if user_recv in globals.G_Duel_Instances.keys():
                globals.G_Duel_Instances[user_recv]['instances'] += 1
            else:
                globals.G_Duel_Instances[user_recv] = {
                                        'instances':0,
                                        'wins':0,
                                        'loses':0}
            globals.G_Duels[(user_snd, body['user']['id'])] = {user_snd : {'submissions' : 0, 'total' : 0}, body['user']['id'] : {'submissions' : 0, 'total' : 0}, 'length' : 4, 'duel_ts': body['container']['message_ts']}
            
            # add users to duel list here (use number of submissions for contest duration)
            # makes 2 options for contest length
            
        except SlackApiError as e:
            logger.error(f"Error opening msg: {e}")
        
    def decline_duel(self,body,ack,say,logger,respond):
        ack()
        try:
            throw_away,user_snd = body["message"]["text"].split("@")
            user_snd = user_snd.split(">")[0]
            self.client.chat_postMessage(channel=user_snd,text=f"Your solve contest with <@{body['user']['id']}> has been declined!")
            self.pending_duels.remove(body['user']['id'])
            respond("You successfully declined the challenge!",replace_original=True)
        except SlackApiError as e:
            logger.error(f"Error opening msg: {e}")

    """Public Method"""
    # Store users dictionary to json file  
    def store_data(self):
        with open(".data/users.json", "w+", encoding='utf8') as file:
            json.dump(globals.G_Users, file)
        with open(".data/ignore.json", "w+", encoding='utf8') as file:
            json.dump(self.ignore,file)
        with open(".data/duel_instances.json", "w+", encoding='utf8') as file:
            json.dump(globals.G_Duel_Instances,file)
        # Json does not accept tuples as keys so we will need to convert to string  
        str_key = {str(k):v for k,v in globals.G_Duels.items()}
        with open(".data/duels.json", "w+", encoding='utf8') as file:
            json.dump(str_key,file)
    
    # If user hasn't posted in last 15 minutes send a reminder, set a flag once they are sent a reminder. The flag is always checked before a reminder is sent so users are not spammed
    def post_reminder(self):
        dt_now = datetime.now()
        for user in globals.G_Users:
        # If the user is in our users list check if they need a reminder sent
            try:
                dt_user = datetime.fromtimestamp(float(globals.G_Users[user]['ts'][-1]))
                dt_delta = dt_now - dt_user
                if dt_delta.seconds > 900 and globals.G_Users[user]['flag']:
                    globals.G_Users[user]['flag'] = False
                    self.client.chat_postMessage(channel = user,
                                                 text = "Don't forget to post your solves for the hour!"
                                                )
            except IndexError:
                if globals.G_Users[user]['flag']:
                    globals.G_Users[user]['flag'] = False
                    self.client.chat_postMessage(channel = user,
                                                 text = "Don't forget to post your solves for the hour!"
                                                )
    """Private Methods"""
    
    def __replace(self,k):
    # this will split up stored key daya for duels and return it's tuple
        u1, u2 = k.split(', ')
        disallowed_char = "()'"
        for char in disallowed_char:
            u1 = u1.replace(char,"")
            u2 = u2.replace(char,"")
        return (u1,u2)
     
    # Attempt to import stored data when program starts
    def __get_data(self):
        with open(".data/users.json", "r") as file:
        # Read in stored solver users data
            globals.G_Users = json.load(file)
        with open(".data/ignore.json", "r") as file:
        # Read in stored ignore list
            self.ignore = json.load(file)
        with open("payloads/duel_init.json","r") as file:
        # Read in payload for duel invite
            self.duel_init = json.load(file)
        with open(".data/duels.json", "r") as file:
        # Read in stored duels list, string keys need to be reverted back to tuple
            try:
              str_key = json.load(file)
              globals.G_Duels = {self.__replace(k):v for k,v in str_key.items()}
            except JSONDecodeError:
              pass

        with open(".data/duel_instances.json", "r") as file:
        # Read in ignore list
            try:
              globals.G_Duel_Instances = json.load(file)
            except JSONDecodeError:
              pass
      
    # Send out a reminder to post solves at every time interval XX:10 and store data every 60 minutes starting 15 minutes past the hour
    def __run_tmethods(self):
        wait = datetime.now().minute
        if wait < 10:
            wait = 10 - wait
        elif wait == 10:
            wait = 0
        else:
            wait = 70 - wait
        remind = RepeatTimer1(wait*60,self.post_reminder)
        remind.start()
        store = RepeatTimer0((wait+5)*60, self.store_data)
        store.start()
        
    """Private User Methods accessed from run"""
    # Explanations for private user methods can be found in User Commands below
    
    def __add(self, user, text, channel, ts):
    # This functions will add users posted solves to a list as well as the time it was posted to be checked for the reminder (also adds those values to the duels dictionary)
        if user in globals.G_Users:
            globals.G_Users[user]['solves'].append(int(text))
            globals.G_Users[user]['ts'].append(ts)
            globals.G_Users[user]['flag'] = True
            if int(text) >= 10 :
                self.client.reactions_add(channel = channel,
                                          name = 'fire',
                                          timestamp = ts
                                         )
            if globals.G_Users[user]['silent'] == False:
                self.client.chat_postEphemeral(channel = channel,
                                               user = user,
                                               ts = ts,
                                               text = f"Your reported solves: {total}"
                                               )
            # Loop through duel keys and check if user is in key pair, also check if duel is over
            for duel_key in globals.G_Duels.keys():
              
                if user == duel_key[0]:
                  user2 = duel_key[1]
                else:
                  user2 = duel_key[0]
                  
                if user in duel_key:                  
                    if globals.G_Duels[duel_key][user]['submissions'] < 4:
                      globals.G_Duels[duel_key][user]['submissions'] += 1
                      globals.G_Duels[duel_key][user]['total'] += int(text)
                    #print(self.duels[duel_key][user][0], self.duels[duel_key][user][1])
                    
                #Check if both users are at their max submissions. This will trigger the result section to start working.
                if globals.G_Duels[duel_key][user]['submissions'] == globals.G_Duels[duel_key]['length'] and globals.G_Duels[duel_key][user2]['submissions'] == globals.G_Duels[duel_key]['length']:
                    
                    if globals.G_Duels[duel_key][user]['total'] == globals.G_Duels[duel_key][user2]['total']:
                        self.client.chat_postMessage(channel = user,
                                                     text = f"You tied with <@{user2}>"
                                                    )
                        self.client.chat_postMessage(channel = user2,
                                                     text = f"You tied with <@{user}>"
                                                    )
                    elif globals.G_Duels[duel_key][user]['total'] > globals.G_Duels[duel_key][user2]['total']:
                        
                        globals.G_Duel_Instances[user]['wins'] += 1
                        globals.G_Duel_Instances[user2]['loses'] += 1
                        self.client.chat_postMessage(channel = user,
                                                     text = f":tada: You won your duel vs <@{user2}>! :tada:"
                                                    )
                        self.client.chat_postMessage(channel = user2,
                                                     text = f":crying_cat_face: You lost your duel vs <@{user}> :crying_cat_face:"
                                                    )
                    else:
                        globals.G_Duel_Instances[user2]['wins'] += 1
                        globals.G_Duel_Instances[user]['loses'] += 1
                        self.client.chat_postMessage(channel = user2,
                                                     text = f":tada: You won your duel vs <@{user}>! :tada:"
                                                    )
                        self.client.chat_postMessage(channel = user,
                                                     text = f":crying_cat_face: You lost your duel vs <@{user2}> :crying_cat_face:"
                                                    )
                    globals.G_Duel_Instances[user]['instances'] -= 1
                    globals.G_Duel_Instances[user2]['instances'] -= 1
                    del globals.G_Duels[duel_key]
    
    def __oops(self, user, channel, ts):
        remove = globals.G_Users[user]['solves'].pop()
        del globals.G_Users[user]['ts'][-1]
        total = sum(globals.G_Users[user]['solves'])
        self.client.chat_postEphemeral(channel = channel,
                                       user = user,
                                       ts = ts,
                                       text = f"Removing {remove} solves from total. \nYour reported solves: {total}"
                                      )
        for duel_key in globals.G_Duels.keys():
            if user in duel_key and globals.G_Duels[duel_key][user]['total'] > 0:
                globals.G_Duels[duel_key][user]['submissions'] -= 1
                sglobals.G_Duels[duel_key][user]['total'] -= remove
                
    def __eod(self, user, channel, ts):
        if user in globals.G_Users:
            total = sum(globals.G_Users[user]['solves'])
            self.client.chat_postEphemeral(channel = channel,
                                           user = user,
                                           ts = ts,
                                           text = f"Your total reported solves: {total}"
                                          )
            del globals.G_Users[user]
    
    # def __solves(self, user, channel, ts):
    #     summary = ''
    #     tz = timezone('US/Pacific')
    #     for i in range(len(self.users[user]['solves'])):
    #         dt = datetime.fromtimestamp(float(self.users[user]['ts'][i])).replace(microsecond=0)
    #         dt_tz = tz.normalize(dt.astimezone(tz))
    #         time = str(dt_tz.time())
    #         new_time = datetime.strptime(time,'%H:%M:%S').strftime('%I:%M %p')
    #         solve = self.users[user]['solves'][i]
    #         summary += f'{new_time} - *{solve}* \n'
    #     self.client.chat_postEphemeral(channel = channel,
    #                                    user = user,
    #                                    ts = ts,
    #                                    text = summary
    #                                   )