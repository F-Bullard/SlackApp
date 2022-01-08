import json, datetime, pytz, copy
import globals

class Home():
    def __init__(self, client):
        self.client = client
        with open("payloads/home.json","r") as file:
            self.home = json.load(file)

    def home_opened(self, body, event, logger):
        user = event["user"]
        tmp_home = copy.deepcopy(self.home)
        # tmp_home = self.home
        users = globals.G_Users
        duels = globals.G_Duels
        # Start loading in data from solver list and format for home page
        solv_summ = '*Reported Solves*\n'
        duel_summ = '*Current Duels*\n'
        if user in users and users[user]['solves']:
            # Specify timezone to be changed too
            tz = pytz.timezone("US/Pacific")
            for i in range(len(users[user]['solves'])):
                # Convert timestamp into a datetime and remove microseconds from display
                dt = datetime.datetime.fromtimestamp(float(users[user]['ts'][i])).replace(microsecond=0)
                # Change the datetime to PST
                dt_tz = tz.normalize(dt.astimezone(tz))
                # Convert time to a string
                time = str(dt_tz.time())
                # Convert Military time into standard time with AM/PM
                new_time = datetime.datetime.strptime(time,'%H:%M:%S').strftime('%I:%M %p')
                solve = users[user]['solves'][i]
                solv_summ += f'{new_time} - {solve} \n'
            tmp_home['blocks'][2]['fields'][0]['text'] = solv_summ
        # Start loading in data from duels and format for home page
        for duel_key in duels.keys():
            if user in duel_key:
                user_name0 = self.client.users_info(user = duel_key[0])
                user_name1 = self.client.users_info(user = duel_key[1])
                duel_summ += '<@%s> - Submissions: %s Total: %s | <@%s> - Submissions: %s Total: %s \n'%(user_name0['user']['id'],duels[duel_key][duel_key[0]]['submissions'],duels[duel_key][duel_key[0]]['total'],user_name1['user']['id'],duels[duel_key][duel_key[1]]['submissions'],duels[duel_key][duel_key[1]]['total'])
                #duel_summ += '%s - Submissions: %s Total: %s | %s - Submissions: %s Total: %s \n'%({user_name0['user']['name']},duels[duel_key][duel_key[0]]['submissions'],duels[duel_key][duel_key[0]]['total'],{user_name1['user']['name']},duels[duel_key][duel_key[1]]['submissions'],duels[duel_key][duel_key[1]]['total'])
                tmp_home['blocks'][2]['fields'][1]['text'] = duel_summ               
        try:
            # Call the views_publish method using the WebClient passed to Commands when initiated
            result = self.client.views_publish(
                user_id=user,
                view=str(tmp_home)
            )

            logger.info(result)

        except SlackApiError as e:
            logger.error("Error fetching conversations: {}".format(e))