"""State representation of the mine"""

import copy
import itertools as it
from collections import defaultdict


class FleetState(object):
    """ Represents the current status of the fleet """

    def __init__(self, config, trucks, route_demands, max_segment, warm_start=False):
        """ Parameters:
                - config: MineConfiguration instance
                - truck_capacities: Map from truck name to tonnage capacity. Fleet members are inferred from this parameter
                - route_demands: Map key: Tuple of locations,
        """

        self.config = config
        self.trucks = trucks
        self.route_demands = route_demands
        self.garage = list(filter(lambda l: l.name == "garage", config.locations()))[0]
        self.max_segment = max_segment

        if not warm_start:
            # Internal book keeping of the state
            self.trips = 0
            self.covered_demands = {k: 0 for k in route_demands}
            self.resident_trucks = {loc: set() for loc in config.locations()}
            self.segment = 1
            # Assume all trucks are on the garage
            for t in self.trucks: self.resident_trucks[self.garage].add(t)


    def __eq__(self, other):
        """ Compares two fleet states to check equivalence """
        # We can ignore the mine configuration and truck capacities, as they're constant throughout the process
        return self.covered_demands == other.covered_demands and self.__factorize_assignments() == other.__factorize_assignments()

    def __hash__(self):
        """ Custom hash implementation to consider only elements of interest """
        #elements = (frozenset(self.covered_demands.items()), frozenset(map(lambda x: (x[0], frozenset(x[1])), self.resident_trucks.items())))

        elements = (frozenset(self.covered_demands.items()), self.__factorize_assignments())

        return hash(elements)

    def __factorize_assignments(self):

        # Generate tuples for the resident truck configurations of the following format:
        # (location, # of trucks, total capacity)
        return frozenset((k, len(v), sum(t.tonnage_capacity for t in v)) for k, v in self.resident_trucks.items())



    def clone(self):
        """ Creates a new instance of the state with the same values """
        cl = FleetState(self.config, self.trucks, self.route_demands, self.max_segment, warm_start=True)
        cl.covered_demands = {k: v for k, v in self.covered_demands.items()}
        cl.resident_trucks = {k: copy.copy(v) for k, v in self.resident_trucks.items()}
        cl.trucks = self.trucks # No need to copy this as it's immutable
        cl.trips = self.trips
        cl.segment = self.segment

        return cl



    def is_successful(self):
        """ Returns true whether this is a successful state """

        # All trucks should be in the garage
        all_in_garage = len(self.resident_trucks[self.garage]) == len(self.trucks)

        if not all_in_garage:
            return False
        else:
            # All the demands must be covered
            all_covered = True
            for route in self.route_demands:
                if self.covered_demands[route] < self.route_demands[route]:
                    all_covered = False
                    break

            if self.segment <= self.max_segment and all_covered:
                return True
            else:
                return False

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
            destinations = list()
            # Compute how many trucks we can move at most
            num_moves = 0
            for d in config.destinations(src):
                slots_available = d.resident_capacity - len(self.resident_trucks[d])
                if slots_available > 0:
                    destinations.append(d)
                    num_moves += slots_available

            # Consider only the same number of trucks as the possible number of moves
            # and pick the trucks with the highest capacity
            local_trucks = sorted(self.resident_trucks[src], key=lambda t: t.tonnage_capacity, reverse=True)[:num_moves]
            possible_movements = self.__permutate_assignemnts(src, local_trucks, destinations)
            factors.append(possible_movements)

        # Return the cartesian product of the possible actions amount the qualifying restinations
        # TODO: Perhaps filter by a criteria to avoid combinatorial explosion
        ret = set()
        for p in it.product(*factors):
            movements = p[0]
            ret.add(Action(*movements))

        return ret

    def execute_action(self, action):
        """ Actual implementation of execute action that mutates an instance of FleetState
            This function is not meant to be called directly, but by the instance method defined above """

        self.segment += 1

        # TODO: Consider the resident fleet here. Right now is being neglected for simplification purpuses
        # Iterate over each movement of the action
        for movement in action.movements:
            truck, source, destination = movement.truck, movement.source, movement.destination
            # Increment the trip counter for this truck that was reassigned
            self.trips += 1

            # If the destination is the endpoint of a route, don't change the location of the current truck,
            # as the outcome of the action represents a round-trip from source to destination
            if not (source, destination) in self.route_demands:
                # Change the location of truck on the fleet state
                self.resident_trucks[source].remove(truck)
                self.resident_trucks[destination].add(truck)

            # If it is, then we decrement the remaining demand to be covered
            else:
                # Fetch the capacity of the truck
                capacity = truck.tonnage_capacity
                # Increment the covered demand by the capacity
                self.covered_demands[(source, destination)] += capacity

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
        trucks = list(trucks)

        truck_capacities = {k:list(g) for k, g in it.groupby(sorted(trucks, key=lambda t: t.tonnage_capacity), key = lambda t: t.tonnage_capacity)}

        surrogates = list(it.chain.from_iterable(it.repeat(k, len(v)) for k, v in truck_capacities.items()))

        # Build the movement sequence
        movements = list()
        # for perm in it.permutations(trucks, num_slots):
        #     x = list()
        #     for ix, truck in enumerate(perm):
        #         dst = slots[ix]
        #         m = Movement(truck, src, dst)
        #         x.append(m)
        #     movements.append(x)

        for perm in it.permutations(slots, len(surrogates)):
            x = list()
            for ix, slot in enumerate(perm):
                dst = slot
                #truck = trucks[ix]
                surrogate_key = surrogates[ix]
                truck = truck_capacities[surrogate_key].pop()
                m = Movement(truck, src, dst)
                x.append(m)
            movements.append(x)

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

    def __hash__(self):
        capacities = defaultdict(list)
        for m in self.movements:
            src, dst, truck = m.source, m.destination, m.truck
            capacities[(src, dst)].append(truck)

        elements = frozenset((k[0], k[1], len(v), sum(t.tonnage_capacity for t in v)) for k, v in capacities.items())
        return hash(elements)