from core import Parameters, calculate_route_times
from core.optimization import LinearProblem, solve
import core.data_access as da
import pandas as pd



# Program parameters
params = Parameters(tonnage_demand=50, shift_length=12)


# Fetch data
server = 'localhost'
database = 'stg_Production'
username = 'sa'
password = 'Masteryoda12345!'

data = da.fetchFromSQLServer(server, database, username, password)


# Infer route times per segment and destinations

# Create a data frame from the dictionary
frame = pd.DataFrame(data)
# Locations TODO: How about the sources
locations = list(frame['destination'].unique())
# Machines
machines = list(frame['machine'].unique())
# Arc times in average TODO: Figure out the time unit here. I think minutes
times = calculate_route_times(frame)


# Instantiate and solve problems

# Compute all the location pairs (arcs in the graph)
arcs = [(a, b) for a in locations for b in locations if a != b]

# Solve the subproblems
subproblems = [LinearProblem(arc, times) for arc in arcs]

results = dict()
for p in subproblems:
    try:
        k = p.name
        solution = solve(p)
        results[k] = solution
    except Exception as e:
        print(e)

# Persist results
# TODO: Store it somewhere, perhaps Amazon's table storage for the API to retrieve later ond