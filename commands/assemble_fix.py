import json
from slack_sdk.errors import SlackApiError

class Assemble_Fix():
    def __init__(self, client):
        self.client = client
        with open("payloads/assemble_pl.json","r") as file:
            self.assembled_pl = json.load(file)

    def timeConvert(time):
        miliTime = time
        hours, minutes = miliTime.split(":")
        hours, minutes = int(hours), int(minutes)
        setting = "AM"
        if hours > 12:
            setting = "PM"
            hours -= 12
        res = ("%02d:%02d " + setting) % (hours, minutes)
        return res

    def handle_assembled_fix(self, body, ack, logger):
        logger.info(body)
        ack()
        try:
            res = self.client.views_open(
                trigger_id=body["trigger_id"],
                view=self.assembled_pl,
                )
            logger.info(res)

        except SlackApiError as e:
            logger.error(f"Error publishing modal: {e}")

    def handle_view_submission(self, ack, body, logger, view):
        ack()
        name_text = view["state"]["values"]["name_block"]["name_field"]["value"]
        time_text = view["state"]["values"]["timeA_block"]["time_act"]["selected_time"]
        time1_text = view["state"]["values"]["timeB_block"]["time_set"]["selected_time"]
        reason_text = view["state"]["values"]["reason_block"]["reason_input"]["value"]
        user = body["user"]["id"]
        #E.sendEmail("reece.resendez@srp.support",f"SLACK REQUEST TO UPDATE ASSEMLED FOR {name_text}",f"Time agent took break: {time_text}\n Time agent's break was scheduled: {time1_text}\nAgent Reason: {reason_text}")
        time_text = self.timeConvert(time_text)
        time1_text = self.timeConvert(time1_text)

        response_channel = "G01Q7A7F8AX"
        self.client.chat_postMessage(channel=response_channel, 
                                text=f"New Assembled Fix submission from\n<@{user}>  \
                                \nTime agent took break: {time_text}\n Time agent's break was scheduled: {time1_text}\nAgent Reason: {reason_text}"
                               )
        self.client.chat_postMessage(channel=user,text=f"Hey <@{user}>\nYour submission for Assembled-Fix as been received!\nWe will get this resolved shortly.")