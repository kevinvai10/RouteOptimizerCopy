""" Module file for Core """

class Parameters(object):
    """ User provided parameters of the application """

    def __init__(self, tonnage_demand, shift_length):
        self.tonnage_demand = tonnage_demand
        self.shift_length = shift_length



def calculate_route_times(frame):
    """ Computes the average time in a route per truck by using the data """


    # Group by machine and destination TODO: Add source to this filtering
    grouped = frame.groupby(["machine", "destination"])

    # Compute average time
    averages = grouped["haul_time"].mean()

    return dict(averages)