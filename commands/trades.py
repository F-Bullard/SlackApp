import json
from slack_sdk.errors import SlackApiError

class Trades():
    def __init__(self, client):
        self.client = client
        with open("payloads/shiftCoverageForm.json","r") as file:
            self.trade_request_pl = json.load(file)
        
    def trade_request(self, body, ack, logger):
        logger.info(body)
        ack()
        try:
            res = self.client.views_open(
                trigger_id=body["trigger_id"],
                view=self.trade_request_pl,
                )
            logger.info(res)

        except SlackApiError as e:
            logger.error(f"Error publishing modal: {e}")