from django import forms
from .models import Market, Simulation

class UploadFileForm(forms.Form):
    file = forms.FileField(label='File')
    sheet_name = forms.CharField(label='Sheet Name', max_length=255)


class MarketForm(forms.ModelForm):
    class Meta:
        model = Market
        fields = ['simulation', 'market_number', 'name']
        widgets = {
            'simulation': forms.Select(attrs={'class': 'form-control'}),
            'market_number': forms.NumberInput(attrs={'class': 'form-control'}),
            'name': forms.TextInput(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        academic_year = kwargs.pop('academic_year', None)
        super().__init__(*args, **kwargs)

        if academic_year:
            self.fields['simulation'].queryset = Simulation.objects.filter(
                academic_year=academic_year
            )