""" Module file for Core """
import json
from pulp import LpStatus


class Parameters(object):
    """ User provided parameters of the application """

    def __init__(self, tonnage_demand, shift_length):
        self.tonnage_demand = tonnage_demand
        self.shift_length = shift_length



def calculate_route_times(frame):
    """ Computes the average time in a route per truck by using the data """


    # Group by destination TODO: Add source to this filtering, verify the validity of this grouping
    grouped = frame.groupby("destination")

    # Compute the micro average time for each destination
    averages = dict()
    for k, v in grouped:
        avg_time = (60/(v.loads/v.haul_time)).mean()
        averages[k] = avg_time

    return dict(averages)


class ProblemResults(object):
    """ Represents the result of a LP problem """
    def __init__(self, status, variables):
        self.status = status
        self.variables = variables

    def to_json(self):
        x = dict()

        x['status'] = LpStatus[self.status]

        variables = dict()
        for k, v in self.variables.items():
            variables[k] = {a.name:a.value() for a in v}

        x['variables'] = variables#{v.name():{a.name():a.value() for a in v} for k, v in self.variables.items()}

        jstring = json.dumps(x)

        return jstring
