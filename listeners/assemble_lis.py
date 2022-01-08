from commands.assemble_fix import Assemble_Fix

class Assemble_Lis():
## Listeners for assembled fix
    def __init__(self, app):
        AF = Assemble_Fix(app.client)
            
        @app.command("/assembled-fix")
        def assembled_fix(body, ack, logger):
            AF.handle_assembled_fix(body, ack, logger)
            
        @app.view("assembled_mod")
        def view_submission(ack, body, client, logger, view):
            AF.handle_view_submission(ack, body, logger, view)