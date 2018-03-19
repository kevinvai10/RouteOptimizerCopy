""" Contains all the elements related to the optimization via MLP """

class LinearProblemn(object):
    """ Represents an instance of a subproblem to be solved by the fleet optimizator"""

    def __init__(self, name, arc_times):
        """ Constructor """
        self.name = name
        self.arc_times = arc_times


def solve(problem):
    """ Core of the fleet optimization algorithm. Runs the MLP for the particular subproblem
        Returns the assignment and the optimized target
    """

    # TODO: Code it

    pass