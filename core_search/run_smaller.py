""" This file is a test script """

import itertools as it
import math
import sys
from core_search.entities import *
from core_search.state import *
from core_search.search import *

# First build the locations
shovel1 = Location("S1", 2)
loader1 = Location("L1", 2)
crusher = Location("C", 2)
garage = Location("garage", 21)

# Build the mine configuration
connections = [
    (garage, loader1),
    (loader1, garage), # Once per shift, only applicable if truck doesn't have load
    (garage, shovel1),
    (shovel1, garage),
    (crusher, shovel1),
    (shovel1, crusher),
    (loader1, crusher),
    (crusher, loader1),
    (crusher, garage)
]

config = MineConfiguration(connections)

# Generate the trucks
trucks = [Truck("truck_%i" % i, c) for i, c in zip(range(1, 10), it.cycle([100]))]


# Build some fake demands
demands = {
    (shovel1, crusher): 400,
    (loader1, crusher): 400,
}

num_segments = 15

# Create the initial state
initial_state = FleetState(config, trucks, demands, num_segments)

def heuristic(state):
    max_segments = state.max_segment
    current_segment = state.segment
    to_go = max(max_segments - current_segment, 0)

    total_trips = 0
    attainable_trips = 0

    trucks = sorted(state.trucks, key=lambda t: t.tonnage_capacity, reverse=True)

    routes = list()
    for k, v in state.route_demands.items():
        remaining = v - state.covered_demands[k]
        if remaining > 0:
            routes.append((k, remaining))

    routes = sorted(routes, key= lambda r: r[1], reverse=True)

    segments_remaining = list()

    num_taken_trucks = 0

    for k, remaining in routes:
        location_capacity = k[1].resident_capacity
        to_take = location_capacity if len(trucks) >= location_capacity else len(trucks)
        taken_trucks = trucks[:to_take]
        num_taken_trucks += len(taken_trucks)
        trucks = trucks[to_take:]

        capacity = sum(t.tonnage_capacity for t in taken_trucks)
        i = math.ceil(float(remaining)/capacity)
        segments_remaining.append(i)

    if len(segments_remaining) > 0:
        return sum(segments_remaining) + num_taken_trucks
    else:
        return 0


# Let it run!
searcher = AStar(initial_state, heuristic)

solution = searcher.solve()

print(solution.cost)



pass
