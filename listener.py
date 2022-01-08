from listeners.assemble_lis import Assemble_Lis
from listeners.home_lis import Home_Lis
from listeners.solver_lis import Solver_Lis
from listeners.trades_lis import Trades_Lis

class Listener():
    def __init__(self, app):
        Assemble_Lis(app)
        Home_Lis(app)
        Solver_Lis(app)
        Trades_Lis(app)