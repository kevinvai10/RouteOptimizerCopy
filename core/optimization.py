""" Contains all the elements related to the optimization via MLP """

import math
import itertools as it
from pulp import *


class LinearProblem(object):
    """ Represents an instance of a subproblem to be solved by the fleet optimizator"""

    def __init__(self, name, arc_times, fleet_size):
        """ Constructor """
        self.name = name
        self.arc_times = arc_times
        self.locations = arc_times.keys
        self.fleet_size = fleet_size

        # TODO: Parameterize this
        # Ten hours and two shifts
        self.num_segments = math.ceil(10*60*2 / arc_times[name[1]])


def solve(problem):
    """ Core of the fleet optimization algorithm. Runs the MLP for the particular subproblem
        Returns the assignment and the optimized target
    """

    # Instance of the problem
    instance = LpProblem("Fleet Optimizer", LpMinimize)

    # Variables
    X = dict()
    for i in problem.name:
        X[i] = list()
        for j in range(problem.num_segments):
            x = LpVariable("X_%s_%i" % (i, j), lowBound=0, cat=LpInteger)
            X[i].append(x)

    # The target function
    target = LpAffineExpression([(x, 1) for x in it.chain.from_iterable(X.values())])
    instance += target


    # Constraints

    # Tonnage Demand
    #######################################################
    # TODO: Paremeterize this
    T = dict()
    for i in problem.name:
        T[i] = list()
        for j in range(problem.num_segments):
            t = 1
            T[i].append(t)
    #######################################################

    C = 100 # TODO: Parameterize this

    for i in problem.name:
        for j in range(problem.num_segments):
            tc = C*X[i][j] >= T[i][j]
            instance += tc

    # Fleet size
    for j in range(problem.num_segments):
        elements = list()
        for i in problem.name:
            elements.append((X[i][j], 1))

        fsc = LpAffineExpression(elements)
        instance += LpConstraint(elements, LpConstraintLE, "Fleet_conservation_%i" % j, problem.fleet_size)

    #instance.writeLP("test.lp")
    status = instance.solve()
    return status, X