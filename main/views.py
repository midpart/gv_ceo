from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from . forms import UploadFileForm
import pandas as pd
from django import forms

# Create your views here.

@login_required(login_url='login')
def index(request):
    return render(request, 'main/index.html')

@login_required(login_url='login')
def upload_student_file(request):
    template_name = 'main/upload-student.html'
    data = None
    if request.method == 'POST':
        form = UploadFileForm(request.POST, request.FILES)
        if form.is_valid():
            file = request.FILES['file']
            sheet_name = form.cleaned_data['sheet_name']
            try:
                # Check the file extension
                if file.name.endswith('.csv'):
                    df = pd.read_csv(file)
                elif file.name.endswith(('.xls', '.xlsx')):
                    all_df = pd.ExcelFile(file)
                    sheet_names = all_df.sheet_names
                    if sheet_name not in sheet_names:
                        raise ValueError(f"This sheet name not found in the file. We have {len(sheet_names)} sheet(s). They are {(", ".join(sheet_names))}")
                    df = pd.read_excel(file, sheet_name=sheet_name)
                else:
                    raise ValueError('Unsupported file type. Please upload CSV or Excel.')

                for index, row in df.iterrows():
                    name = row.get('Name')
                    print(name)
            except Exception as e:
                return render(request, template_name, { 'form': form,'error': str(e)})

            return render(request, template_name, {
            'form': form,
            'success': 'File processed successfully!'
        })

    else:
        form = UploadFileForm()

    return render(request, template_name, {'form': form})