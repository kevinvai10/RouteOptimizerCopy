"""State representation of the mine"""

import copy
import math
import itertools as it
from functools import reduce
from operator import mul
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

        self.max_segment = max_segment

        if not warm_start:
            # Internal book keeping of the state
            self.trips = 0
            self.covered_demands = {k: 0 for k in route_demands}
            self.resident_trucks = {loc: set() for loc in config.locations()}
            self.segment = 1

            self.garage = list(filter(lambda l: l.name == "garage", config.locations()))[0]

            # Assume all trucks are on the garage
            for t in self.trucks: self.resident_trucks[self.garage].add(t)

            # Used for the heuristic computation
            self.max_capacity = max(t.tonnage_capacity for t in trucks)
            self.num_effective_routes = sum(d.resident_capacity for s, d in route_demands)

    def progress(self):
        return sum(self.covered_demands.values())

    def __eq__(self, other):
        """ Compares two fleet states to check equivalence """
        # We can ignore the mine configuration and truck capacities, as they're constant throughout the process
        #return self.covered_demands == other.covered_demands and self.__factorize_assignments() == other.__factorize_assignments()
        return hash(self) == hash(other)

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
        cl.garage = self.garage
        cl.max_capacity = self.max_capacity
        cl.num_effective_routes = self.num_effective_routes

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

    def possible_actions(self): return self._new_possible_actions()

    def _new_possible_actions(self):

        # If time's up, no actions left
        if self.segment >= self.max_segment:
            return list()

        movement_list = list()
        config = self.config

        # First, figure out the locations in the mine that have any truck
        rt = self.resident_trucks
        locations = sorted([l for l in rt if len(rt[l]) > 0], key=lambda l: l.name)

        factors = list()

        for src in locations:
            # What are the possible destinations, only consider those with enough room
            # Compute how many trucks we can move at most
            num_moves = 0
            ds = sorted(config.destinations(src), key=lambda l: l.name)

            local_trucks = sorted(self.resident_trucks[src], key=lambda t: t.tonnage_capacity, reverse=True)

            demand_ds = list()
            non_demand_ds = list()
            for d in ds:
                if (src, d) in self.route_demands:
                    demand_ds.append(d)
                else:
                    non_demand_ds.append(d)

            # If the pair has demand
            for d in demand_ds:
                key = (src, d)

                # If there's still demand to cover in this route
                if self.covered_demands[key] < self.route_demands[key]:
                    remaining_demand = self.route_demands[key] - self.covered_demands[key]
                    for i in range(d.resident_capacity):
                        if remaining_demand > 0 and len(local_trucks) > 0:
                            t = local_trucks.pop()
                            movement_list.append(Movement(t, src, d))
                            remaining_demand -= t.tonnage_capacity
                        else:
                            break

            eligible_ds = list()
            for d in non_demand_ds:
                for d2 in config.destinations(d):
                    key = (d, d2)
                    if key in self.route_demands:
                        remaining_demand = self.route_demands[key] - self.covered_demands[key]
                        if remaining_demand > 0:
                            eligible_ds.append(d)
                            break


            # Here do something with the elegibles
            for d in eligible_ds:
                if len(local_trucks) > 0:
                    num_slots = d.resident_capacity - len(self.resident_trucks[d])
                    for i in range(num_slots):
                        t = local_trucks.pop()
                        movement_list.append(Movement(t, src, d))
                else:
                    break


            if src != self.garage:
                # For the remaining trucks, send them back to the garage
                for t in local_trucks:
                    movement_list.append(Movement(t, src, self.garage))



        x = [Action(*movement_list)]

        return x


    def _old_possible_actions(self):
        """ Possible actions from the current outcome """

        if self.segment >= self.max_segment:
            return list()

        config = self.config

        # First, figure out the locations in the mine that have any truck
        rt = self.resident_trucks
        locations = sorted([l for l in rt if len(rt[l]) > 0], key= lambda l: l.name)

        # For each location, analyze the possible locations to be
        # Keep track of the factors for the cartesian product of movements
        factors = list()
        for src in locations:
            # What are the possible destinations, only consider those with enough room
            destinations = list()
            # Compute how many trucks we can move at most
            num_moves = 0
            ds = sorted(config.destinations(src), key=lambda l: l.name)
            for d in ds:
                key = (src, d)

                is_productive = False
                if key in self.route_demands:
                    is_productive = True
                    if self.covered_demands[key] >= self.route_demands[key]:
                        continue

                # TODO: Enable de resident truck capacity
                i = len(self.resident_trucks[d]) if not is_productive else 0
                slots_available = d.resident_capacity - len(self.resident_trucks[d])
                if slots_available > 0:
                    destinations.append(d)
                    num_moves += slots_available

            # Consider only the same number of trucks as the possible number of moves
            # and pick the trucks with the highest capacity
            local_trucks = sorted(self.resident_trucks[src], key=lambda t: t.tonnage_capacity, reverse=True)[:num_moves]
            possible_movements = self.__permutate_assignemnts(src, local_trucks, destinations) # TODO Check for undeterminism here

            if len(possible_movements) > 0:
                factors.append(possible_movements)

        # Return the cartesian product of the possible actions amount the qualifying restinations
        # TODO: Perhaps filter by a criteria to avoid combinatorial explosion
        # TODO: Add a heuristic to do a beam search
        total_combinations = reduce(mul, map(len, factors))

        #if total_combinations < 2000000:
        new_factors = factors
        #else:
        #new_factors = list()
        #for factor in factors:
        #    if len(factor) <= 5:
        #        new_factors.append(factor)
        #    else:
        #        reduced_factor = list(sorted(factor, key=self.beam_heuristic, reverse=True))[:5]
        #        new_factors.append(reduced_factor)

        ret = set()
        ordered_ret = list()
        for p in it.product(*new_factors):
            movements = p[0]
            action = Action(*movements)
            if action not in ret:
                ret.add(action)
                ordered_ret.append(action)

        #r = [(self.beam_heuristic(a.movements), a) for a in ret]
        #ranked_ret = sorted(r, key=lambda a: a[0], reverse=True)

        #true_ret = set()
        #for a in ranked_ret:
        #    true_ret.add(a[1])
        #    if len(true_ret) >= 100:
        #        break

        #return true_ret
        return ret#[r[1] for r in ranked_ret]

    def beam_heuristic(self, series):
        """ Computes the potential of contribution of each series of movements and gives it a score for ranking
            on a beam search """
        potential = 0
        reminders = { k: (self.route_demands[k]- self.covered_demands[k]) for k in self.route_demands}
        tails = {s for s, d in reminders}

        for movement in series:
            source = movement.source
            destination = movement.destination

            # Compute whether the change from location reasigns the truck to a route with "potential" in the sense
            # of being reassigned to a place with demand from another place with demand
            key = (source, destination)
            if key in reminders:
                reminder = reminders[key]
                if reminder > 0:
                    potential += 2
            elif destination in tails:
                potential += 1
            elif source in tails:
                potential -= 1

        return potential

    def execute_action(self, action):
        """ Actual implementation of execute action that mutates an instance of FleetState
            This function is not meant to be called directly, but by the instance method defined above """

        # Figure out if all the movements are on a route with demand
        shortcut = True if len(action.movements) > 0 else False

        for m in action.movements:
            s, d = (m.source, m.destination)
            if (s, d) not in self.route_demands:
                shortcut = False
                break
            elif self.covered_demands[(s, d)] >= self.route_demands[(s, d)]:
                shortcut = False
                break

        if not shortcut:
            # TODO: Consider the resident fleet here. Right now is being neglected for simplification purpouses
            self.segment += 1

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
                    # Compute the remaining capacity
                    remaining = self.route_demands[(source, destination)] - self.covered_demands[(source, destination)]
                    # Increment the covered demand by the capacity or the remaining capacity
                    self.covered_demands[(source, destination)] += min(capacity, remaining)

        else:

            groups = defaultdict(list)
            for movement in action.movements:
                truck, source, destination = movement.truck, movement.source, movement.destination
                k = (source, destination)
                groups[k].append(truck)

            remaining_demand = {k:(self.route_demands[k] - self.covered_demands[k]) for k in groups}

            candidate_segment_amounts = [self.max_segment-self.segment]
            for k in groups:
                trucks = groups[k]
                remaining = remaining_demand[k]
                capacity = float(sum(t.tonnage_capacity for t in trucks))
                segments = math.ceil(remaining/capacity)
                candidate_segment_amounts.append(segments)

            num_segments = min(candidate_segment_amounts)

            for k in groups:
                trucks = groups[k]
                capacity = float(sum(t.tonnage_capacity for t in trucks))
                self.covered_demands[k] += min(remaining_demand[k], (capacity * num_segments))
                if self.covered_demands[k] > self.route_demands[k]:
                    print("beeep!!")
                self.trips += (len(trucks) * num_segments)

            self.segment += num_segments


    def __permutate_assignemnts(self, src, trucks, locations):
        """ Returns a sequence of movements that contain all the possible assignments emanating from the source"""

        # Following the intuition behind the best answer in:
        #  https://stackoverflow.com/questions/22939260/every-way-to-organize-n-objects-in-m-list-slots
        # The "slots" are the places available on each destination. i.e. The shovel has no residing trucks
        # and a capacity of two trucks, the we can send two different trucks, hence there are two shovel slots.
        # We need the number of slots and their indices.
        slots = list(map(lambda x: x[0], sorted(
            it.chain.from_iterable(it.repeat((l, l.resident_capacity - len(self.resident_trucks[l])),
                                             l.resident_capacity - len(self.resident_trucks[l])) for l in locations
        ), key=lambda x: x[1], reverse=True)))

        trucks = sorted(list(trucks), key=lambda t: t.name)

        truck_capacities = {k:list(g) for k, g in it.groupby(sorted(trucks, key=lambda t: t.tonnage_capacity), key = lambda t: t.tonnage_capacity)}

        capacity_amounts = {k:len(v) for k, v in truck_capacities.items()}
        capacity_amounts[None] = len(slots)

        # Build the movement sequence
        movements = set()
        movements_ordered = list()

        assignments = self.helper(len(slots), capacity_amounts)

        for a in assignments:
            tc = {k:copy.copy(v) for k, v in truck_capacities.items()}
            local_movements = list()
            for ix, kind in enumerate(a):
                if kind:
                    dst = slots[ix]
                    truck = tc[kind].pop()
                    m = Movement(truck, src, dst)
                    local_movements.append(m)
            tupled_local_movements = tuple(local_movements)
            if tupled_local_movements not in movements:
                movements.add(tupled_local_movements)
                movements_ordered.append(tupled_local_movements)

        return sorted(movements_ordered, key=len, reverse=True)

    def helper(self, slots, capacities):
        if slots == 0 or sum(capacities.values()) == 0:
            return list()
        else:
            ret = list()
            for k, v in capacities.items():
                if v > 0:
                    elem = k
                    new_capacities = copy.copy(capacities)
                    new_capacities[k] -= 1
                    reminder = self.helper(slots-1, new_capacities)
                    if len(reminder) > 0:
                        x = [[elem] + r for r in reminder]
                        ret.extend(x)
                    else:
                        ret.append([elem])
            return ret


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

    def __hash__(self):
        return hash((self.truck, self.source, self.destination))

    def __eq__(self, other):
        return hash(self) == hash(other)


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

    def __eq__(self, other):
        return hash(self) == hash(other)