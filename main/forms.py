from django import forms
from .models import SimulationCompetition

class UploadFileForm(forms.Form):
    file = forms.FileField(label='File')
    sheet_name = forms.CharField(label='Sheet Name', max_length=255)


class SimulationCompetitionForm(forms.ModelForm):
    class Meta:
        model = SimulationCompetition
        fields = ['simulation', 'simulation_number', 'name']
        widgets = {
            'simulation': forms.Select(attrs={'class': 'form-control'}),
            'simulation_number': forms.NumberInput(attrs={'class': 'form-control'}),
            'name': forms.TextInput(attrs={'class': 'form-control'}),
        }