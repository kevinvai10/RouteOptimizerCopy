"""State representation of the mine"""

import copy
import itertools as it


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

        config = self.config

        # First, figure out the locations in the mine that have any truck
        rt = self.resident_trucks
        locations = [l for l in rt if len(rt[l]) > 0]

        # For each location, analyze the possible locations to be
        # Keep track of the factors for the cartesian product of movements
        factors = list()
        for src in locations:
            # What are the possible destinations, only consider those with enough room
            destinations = [d for d in config.destinations(src) if self.resident_trucks[d] < d.resident_capacity]
            local_trucks = self.resident_trucks[src]
            possible_movements = self.__permutate_assignemnts(src, local_trucks, destinations)
            factors.append(possible_movements)

        # Return the cartesian product of the possible actions amount the qualifying restinations
        # TODO: Perhaps filter by a criteria to avoid combinatorial explosion
        return it.product(*factors)


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

        # TODO: Consider the resident fleet here. Right now is being neglected for simplification purpuses
        # Iterate over each movement of the action
        for truck, source, destination in action.movements:
            # Increment the trip counter for this truck that was reassigned
            instance.trips += 1

            # If the destination is the endpoint of a route, don't change the location of the current truck,
            # as the outcome of the action represents a round-trip from source to destination
            if not (source, destination) in instance.route_demands:
                # Change the location of truck on the fleet state
                instance.resident_trucks[source].remove(truck)
                instance.resident_trucks[destination].add(truck)

            # If it is, then we decrement the remaining demand to be covered
            else:
                # Fetch the capacity of the truck
                capacity = truck.tonnage_capacity
                # Increment the covered demand by the capacity
                instance.covered_demands[(source, destination)] += capacity

    def __permutate_assignemnts(self, src, trucks, locations):
        """ Returns a sequence of movements that contain all the possible assignments emanating from the source"""

        # Following the intuition behind the best answer in:
        #  https://stackoverflow.com/questions/22939260/every-way-to-organize-n-objects-in-m-list-slots
        # The "slots" are the places available on each destination. i.e. The shovel has no residing trucks
        # and a capacity of two trucks, the we can send two different trucks, hence there are two shovel slots.
        # We need the number of slots and their indices.
        slots = list(
            it.chain.from_iterable(it.repeat(l, l.resident_capacity - len(self.resident_trucks[l])) for l in locations)
        )
        num_slots = len(slots)

        # Build the movement sequence
        movements = list()
        for perm in it.combinations(trucks, num_slots):
            for ix, truck in enumerate(perm):
                dst = slots[ix]
                m = Movement(truck, src, dst)
                movements.append(m)

        return movements


class Movement(object):
    """ Represents an object """

    def __init__(self, truck, source, destination):
        """ Represents a movement that will be executed in an action """
        self.truck = truck
        self.source = source
        self.destination = destination

    def __repr__(self):
        return "Move %s from %s to %s" % (self.truck, self.source, self.destination)

    def __str__(self):
        return repr(self)

class Action(object):
    """ Encodes the action to be taken as a series of movements """

    def __init__(self, *movements):
        """ Keeps track of the movements that will happen during this action """
        self.movements = movements

