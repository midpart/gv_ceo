from django import forms

class UploadFileForm(forms.Form):
    file = forms.FileField(label='File')
    sheet_name = forms.CharField(label='Sheet Name', max_length=255)
