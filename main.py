#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Title: SRP Interactive (Slackbot for Service Responce Partners)
Authors: Forrest Bullard, Reece Resendez
Version: 0.03

Description: This slackbot will help streamline work processes for departments. It will also aid employees in staying compliant in regards to posting solves. Additions are being made for games that entice employees to preform better.

Current functionality: Includes a tracker for agents posting solves, and a slash command to request corrections to assembled schedule for breaks and lunches.


"""
import os
from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler
from listener import Listener

# Install the Slack app and get xoxb- token in advance
app = App(token=os.environ["SLACK_BOT_TOKEN"])
    
Listener(app)

if __name__ == "__main__":
    handler = SocketModeHandler(app, os.environ["SLACK_APP_TOKEN"])
    handler.start()