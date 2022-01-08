from commands.home import Home

class Home_Lis():
## Listeners for app home
    def __init__(self, app):
        H = Home(app.client)

        @app.event("app_home_opened")
        def app_home_opened(body, event, logger):
            H.home_opened(body, event, logger)
            
        @app.action("ignore")
        def update_message(ack):
            ack()