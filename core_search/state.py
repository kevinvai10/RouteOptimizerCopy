"""State representation of the mine"""

import copy
from core_search.entities import *


class FleetState(object):
    """ Represents the current status of the fleet """

    def __init__(self, config, truck_capacities, route_demands, warm_start=False):
        """ Parameters:
                - config: MineConfiguration instance
                - truck_capacities: Map from truck name to tonnage capacity. Fleet members are inferred from this parameter
                - route_demands: Map key: Tuple of locations,
        """

        self.config = config
        self.truck_capacities = truck_capacities
        self.route_demands = route_demands
        self.trips = 0

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

    def execute_action(self, action):
        """ Executes an action and returns a copy of the mutated state"""

        # First create a copy of the current state
        cl = self.clone()

        # Now execute the action over the clone and mutate its state
        FleetState.__execute_action(cl, action)

        # Return the mutated state
        return cl

    @staticmethod
    def __execute_action(instance, action):
        """ Actual implementation of execute action that mutates an instance of FleetState
            This function is not meant to be called directly, but by the instance method defined above """

        reassigned_trucks = set()
        # Iterate over each movement of the action
        for truck, source, destination in action.movements:
            # Change the location of truck on the fleet state
            instance.resident_trucks[source].remove(truck)
            instance.resident_trucks[destination].add(truck)
            # Increment the trip counter for this truck that was reasigned
            instance.trips += 1
            # Keep track of this truck reasignment
            reassigned_trucks.add(truck)

        # Figure out the trucks that didn't change route (using set difference)
        non_reassigned_trucks = instance.trucks() - reassigned_trucks

        # Iterate throughout the connections in the configuration and update the demands with respect to the resident
        # trucks. TODO: Consider the resident fleet here. Right now is being neglected for simplification purpuses
        connections = instance.config.connections
        for src, dst in connections:
            # Consider only those connections where the garaje is not an endpoint
            if src == "garage" or dst == "garage":
                continue

            # Consider only those connections that have a demand
            if not (src, dst) in instance.route_demands:
                continue

            # Which trucks are in the current source of the edge
            trucks = instance.resident_trucks[src]
            for truck in trucks:
                # Fetch the capacity of the truck
                capacity = truck.tonnage_capacity
                # Increment the covered demand by the capacity
                instance.covered_demands[(src, dst)] += capacity


class Movement(object):
    """ Represents an object """

    def __init__(self, truck, source, destination):
        """ Represents a movement that will be executed in an action """
        self.truck = truck
        self.source = source
        self.destination = self.destination

    def __repr__(self):
        return "Move %s from %s to %s" % (self.truck, self.source, self.destination)

    def __str__(self):
        return repr(self)

class Action(object):
    """ Encodes the action to be taken as a series of movements """

    def __init__(self, *movements):
        """ Keeps track of the movements that will happen during this action """
        self.movements = movements

