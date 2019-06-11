from django.shortcuts import render
from django.http import HttpResponse
from django.template import loader
import core_search.run
import pprint
import json

from .forms import FleetConfigurationForm

# Create your views here.
def index(request):
    simulation = None
    steps = None
    ran = False
    rawData = []
    animationData=[]

    # if this is a POST request we need to process the form data
    if request.method == 'POST':
        # for i in range(100):
            # create a form instance and populate it with data from the request:
        form = FleetConfigurationForm(request.POST)
        # check whether it's valid:
        if form.is_valid():
            # process the data in form.cleaned_data as required
            # ...
            # redirect to a new URL:
            num_segments = form.cleaned_data['num_segments']
            form_num_trucks = form.cleaned_data['num_trucks']

            # Simulate
            steps = list()
            simulation = core_search.run.run(num_segments, form_num_trucks, lambda s: steps.append("Iteration: %i\tEstimated Cost: %i\tAcutal Cost: %i\tSegment: %i\tProgress: %i tons" % s))
            
            # template = '{0}-{1}-{2}'
            # print(template.format(i+1, simulation.cost, simulation.state.total_covered_demand()))
            
            ran = True

            if simulation:

                steps.append("")
                steps.append("Total number of trips: %i" % simulation.cost)
                steps.append("")
                nodes = simulation.path_from_root()
                rawData = nodes[:]
                prev_seg = 1
                for ix, n in enumerate(nodes):
                    if n.action:
                        s = n.state
                        num_segments = s.segment - prev_seg
                        prev_seg = s.segment
                        steps.append("Dispatch: %i\tNumber of trips: %i\tTons moved: %i" % (
                        ix, num_segments, s.total_covered_demand()))
                        steps.append("")
                        for m in n.action.movements:
                            steps.append(str(m))
                        steps.append("")
                
                # Data for animation
                for d in rawData:
                    if d.action:
                        dispatches = [[t.truck.name, t.source.name, t.destination.name] for t in d.action.movements]
                        animationData.append(dispatches)

    # if a GET (or any other method) we'll create a blank form
    else:
        form = FleetConfigurationForm()

    return render(request, 'fleet_ui/index.html', {'form':form, 'ran':ran, 'simulation':simulation, 'steps':steps,'animationData':json.dumps(animationData[:])})

