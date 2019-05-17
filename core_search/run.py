""" This file is a test script with a toy mine """

import pprint
from collections import OrderedDict

from core_search.entities import *
from core_search.search import *
from core_search.state import *

def run(num_segments = 48, num_trucks=29, listener=None, iteracion=22):
    # First build the locations
    shovel1 = Location("S1", 2)
    shovel2 = Location("S2", 2)
    loader1 = Location("L1", 2)
    loader2 = Location("L2", 2)
    waste_dump = Location("W", 2)
    crusher = Location("C", 2)
    garage = Location("garage", num_trucks)

    # Build the mine configuration
    connections = [
        (garage, loader1),
        (garage, loader2),
        (loader1, garage), # Once per shift, only applicable if truck doesn't have load
        (loader2, garage), # Once per shift, only applicable if truck doesn't have load
        (waste_dump, garage), # Once per shift
        (garage, shovel1),
        (garage, shovel2),
        (waste_dump, loader1),
        (loader1, waste_dump),
        (waste_dump, shovel1),
        (shovel1, waste_dump),
        (waste_dump, shovel2),
        (shovel2, waste_dump),
        (crusher, shovel1),
        (shovel1, crusher),
        (crusher, shovel2),
        (shovel2, crusher),
        (crusher, loader2),
        (loader2, crusher),
        (loader1, crusher)
    ]

    config = MineConfiguration(connections)

    # Generate the trucks
    trucks = [Truck("truck_%i" % i, c) for i, c in zip(range(1, num_trucks+1), it.cycle([100]))]


    # Build some fake demands
    demands = OrderedDict(
    [
        ((shovel2, crusher), 1200),
        ((loader1, crusher), 4000),
        ((shovel1, waste_dump), 1600),
        ((shovel2, waste_dump), 2000),
        ((loader1, waste_dump), 1000),
        ((shovel1, crusher), 8000),
    ]
    )


    # Create the initial state
    initial_state = FleetState(config, trucks, demands, num_segments)


    def heuristic(state):
        """ A* Heuristic:
            Estimate how many more trips remain to fulfill all the remaining demand assuming all the routes have the
            highest capacity trucks available runing on them
        """

        # Fetch the trucks ordered decreasingly by their tonnage capacity
        trucks = sorted(state.trucks, key=lambda t: t.tonnage_capacity, reverse=True)

        # Get the routes that haven't been completed yet
        routes = list()
        for k, v in state.route_demands.items():
            remaining = v - state.covered_demands[k]
            if remaining > 0:
                routes.append((k, remaining))

        routes = sorted(routes, key= lambda r: r[1], reverse=True)

        # Compute how many segments per route would take to cover the remaining demand,
        #  which approximates the number of trips needed to cover the demand
        segments_remaining = list()

        # How many trucks are needed to fill this demand
        num_taken_trucks = 0

        # Figure out the values for above's variables
        for k, remaining in routes:
            location_capacity = k[1].resident_capacity
            to_take = location_capacity if len(trucks) >= location_capacity else len(trucks)
            taken_trucks = trucks[:to_take]
            num_taken_trucks += len(taken_trucks)
            trucks = trucks[to_take:]

            if to_take != 0:
                capacity = sum(t.tonnage_capacity for t in taken_trucks)
                i = math.ceil(float(remaining)/capacity)
                segments_remaining.append(i)
            
            
        # Compute the heuristic, which is the number of segments required, and the number of trucks,
        #  as each truck needs to go back to the garage after it's finished
        if len(segments_remaining) > 0:
            return sum(segments_remaining) + num_taken_trucks
        else:
            return 0


    # Let it run!
    searcher = AStar(initial_state, heuristic, listener)

    solution = searcher.solve()

    return solution




if __name__ == "__main__":
    solution = run(listener=lambda t: print("Iteration: %i\tEstimated Cost: %i\tAcutal Cost: %i\tSegment: %i\tProgress: %i tons" % t))

    if solution:
        print()
        print("Total number of trips: %i" % solution.cost)
        print()
        nodes = solution.path_from_root()
        prev_seg = 1
        for ix, n in enumerate(nodes):
            if n.action:
                s = n.state
                num_segments = s.segment - prev_seg
                prev_seg = s.segment
                print("Dispatch: %i\tRepeated: %i times\tTons moved: %i" % (ix, num_segments, s.total_covered_demand()))
                pprint.pprint(n.action.movements)
                print()

    else:
        print("No solution found")