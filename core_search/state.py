"""State representation of the mine"""

import copy
from core_search.entities import *


class FleetState(object):
    """ Represents the current status of the fleet """

    def __init__(self, config, truck_capacities, route_demands, warm_start=False):
        """ Parameters:
                - config: MineConfiguration instance
                - truck_capacities: Map from truck name to tonnage capacity. Fleet members are infered from this parameter
                - route_demands: Default tonnage demande per route
        """

        self.config = config
        self.truck_capacities = truck_capacities
        self.route_demands = route_demands

        if not warm_start:
            # Internal book keeping of the state
            self.covered_demands = {k: 0 for k in route_demands}
            self.resident_trucks = {loc: set() for loc in config.locations()}
            self.trucks = {truck for truck in truck_capacities}

        # Look for the garage and set all the trucks to be on it

    def clone(self):
        """ Creates a new instance of the state with the same values """
        cl = FleetState(self.config, self.truck_capacities, self.route_demands, warm_start=True)
        cl.covered_demands = copy.copy(self.covered_demands)
        cl.resident_trucks = copy.copy(self.resident_trucks)
        cl.trucks = self.trucks # No need to copy this as it's immutable

        return cl

    def __hash__(self):
        """ Custom hash implementation to consider only elements of interest """
        elements = (self.covered_demands, self.resident_trucks)

        return hash(elements)

    def is_successful(self):
        """ Returns true whether this is a successful state """

        # All trucks should be in the garage
        all_in_garage = len(self.resident_trucks["garage"]) == len(self.trucks)

        if not all_in_garage:
            return False
        else:
            # All the demands must be covered
            all_covered = True
            for route in self.route_demands:
                if self.covered_demands[route] < self.route_demands[route]:
                    all_covered = False
                    break

            return all_covered


    def possible_actions(self):
        """ Possible actions from the current outcome """
        # TODO: Implement this
        pass


class Movement(object):
    """ Represents an object """
class Action(object):
    """ Encodes the action to be taken as a series of movements from """

