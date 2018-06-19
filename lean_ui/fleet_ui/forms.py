from django import forms


class FleetConfigurationForm(forms.Form):
    num_segments = forms.IntegerField(label="Number of segments", min_value=1)
    num_trucks = forms.IntegerField(label="Number of trucks", min_value=1)