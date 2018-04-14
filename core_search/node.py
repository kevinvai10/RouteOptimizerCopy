
from core_search.state import FleetState

class SearchNode(object):
    """ Represents a node in the search tree or graph """

    def __init__(self, state, action = None, cost = 0):
        """ Parameters:
                - state: Instance of fleet state
                - action: Action taken leading to this particular state
                - cost: Cummulative cost leading to the current state"""

        self.state = state
        self.action = action
        self.cost = cost

    def is_successful(self):
        return self.state.is_successful()

    def get_children(self):
        return self.state.possible_actions()

    def __hash__(self):
        """ Custom hash function """
        element = (self.action, self.action, self.cost)
        return hash(element)