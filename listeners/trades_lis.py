from commands.trades import Trades

class Trades_Lis():
## Listeners for Solver commands
    def __init__(self, app):
    
        T = Trades(app.client)

        @app.command("/trade")
        def trade_request(body, ack, logger):
            T.trade_request(body, ack, logger)

        @app.view("shiftCoverageForm")
        def view_submission(ack, body, client, logger, view):
            ack()