from commands.solver import Solver

class Solver_Lis():
## Listeners for Solver commands
    def __init__(self, app):
    ## Listener to add and remove user from ignore list
        S = Solver(app.client)
        
        @app.command("/ignore")
        def ignore(body, ack):
        # Toggle ignore game requests for user
            S.ignore_toggle(body, ack)
        
        @app.command("/start")
        def start(ack, body, respond):
        # Add user to users list and allows access to commands below
            S.start(ack, body, respond)
        
        @app.event({"type":"message", "channel":"C01M1SM2NCW"})
        def solver(event, ack):
            S.commands(event, ack)
        
        ## Listeners for Duel
        
        @app.command("/duel")
        def handle_duel(body,ack,logger):
            S.request_duel(body,ack,logger)

        @app.action("actionId-0")  # Accepted response
        def duel_response(body,ack,say,logger,respond):
            S.accept_duel(body,ack,say,logger,respond)

        @app.action("actionId-1")  # Denied response
        def duel_response(body,ack,say,logger,respond):
            S.decline_duel(body,ack,say,logger,respond)