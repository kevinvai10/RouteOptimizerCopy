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

    # Given the current configuration, how many trips we need to do before finishing?
    for k, v in state.route_demands.items():
        remaining = v - state.covered_demands[k]
        if remaining > 0:
            s, d = k
            l = len(state.resident_trucks[s])
            if l == 0:
                return sys.maxsize
            attainable_trips += to_go * l
            capacity = sum(t.tonnage_capacity for t in state.resident_trucks[s])
            trips = int(v/capacity)
            total_trips += trips

    if total_trips <= attainable_trips:
        return total_trips
    else:
        return sys.maxsize


# Let it run!
searcher = UniformCostSearch(initial_state, heuristic)

solution = searcher.solve()

print(solution)

pass
