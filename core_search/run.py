""" This file is a test script with a toy mine """

from collections import OrderedDict

from core_search.entities import *
from core_search.search import *
from core_search.state import *

# First build the locations
shovel1 = Location("S1", 2)
shovel2 = Location("S2", 2)
loader1 = Location("L1", 2)
loader2 = Location("L2", 2)
waste_dump = Location("W", 2)
crusher = Location("C", 2)
garage = Location("garage", 21)

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
trucks = [Truck("truck_%i" % i, c) for i, c in zip(range(1, 22), it.cycle([100]))]


# Build some fake demands
demands = OrderedDict([((shovel1, crusher), 8000),
((shovel2, crusher), 1200),
((loader1, crusher), 4000),
((shovel1, waste_dump), 1600),
((shovel2, waste_dump), 2000),
((loader1, waste_dump), 1000)]
)

num_segments = 58

# Create the initial state
initial_state = FleetState(config, trucks, demands, num_segments)


def heuristic(state):
    max_segments = state.max_segment
    current_segment = state.segment
    to_go = max(max_segments - current_segment, 0)

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

if solution:
    print(solution.cost)
else:
    print("No solution found")
