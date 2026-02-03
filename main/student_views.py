from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from . forms import UploadFileForm, MarketForm
from . query import get_student_score_report, get_all_campus
from .common import *
import pandas as pd
from django import forms
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from . models import Student, Market, Simulation, StudentScore, ImportFileLog
from django.utils import timezone
from django.core.paginator import Paginator
from django.conf import settings
import re
import openpyxl
from django.http import HttpResponse

# Create your views here.

@csrf_exempt
def get_sheet_names(request):
    if request.method == "POST" and request.FILES.get("file"):
        excel_file = request.FILES["file"]
        try:
            check_file(excel_file)
            xls = pd.ExcelFile(excel_file)
            return JsonResponse({"success": True, "sheet_names": xls.sheet_names})
        except Exception as e:
            return JsonResponse({"success": False, "error": str(e)})
    return JsonResponse({"success": False, "error": "No file uploaded."})

@csrf_exempt
def process_sheet(request):
    if request.method == "POST" and request.FILES.get("file"):
        excel_file = request.FILES["file"]
        sheet_name = request.POST.get("sheet_name")
        try:
            check_file(excel_file)
            df = pd.read_excel(excel_file, sheet_name=sheet_name)
            
            filename = excel_file.name
            all_db_data = Student.objects.all()
            add_data = []
            update_data = []
            academic_year = get_active_academic_year()

            for index, row in df.iterrows():
                studienr = row.get('Studienr')
                name = str_to_str(row.get('Name'))
                emailAdress = str_to_str(row.get('EmailAdress'))
                campus = str_to_str(row.get('Campus'))
                subscriptionKey = row.get('SubscriptionKey')
                age = row.get('Age')
                gender = str_to_str(row.get('Gender'))
                
                temp_student = None
                temp_student = next((s for s in all_db_data if s.subscription_key == subscriptionKey), None)
                is_new = False
                if temp_student is None:
                    is_new = True
                    temp_student = Student(
                        subscription_key = subscriptionKey,
                        created_by = request.user,
                        creation_date_time = timezone.now()
                    )

                temp_student.studienr = str_to_bigint(studienr)
                temp_student.name = name
                temp_student.email_address = emailAdress
                temp_student.campus = campus
                temp_student.age_in_year = str_to_bigint(age)
                temp_student.gender = gender
                temp_student.academic_year = academic_year
                temp_student.modified_by = request.user
                temp_student.modification_date_time = timezone.now()
        
                if is_new:
                    add_data.append(temp_student)
                else:
                    update_data.append(temp_student)

            row_count = len(df)
            add_count = len(add_data)
            modify_count = len(update_data)

            if add_count > 0:
                Student.objects.bulk_create(add_data, batch_size=500)
            if modify_count > 0:
                Student.objects.bulk_update(update_data, ["studienr"
                                                          , "name"
                                                          , "email_address"
                                                          , "campus"
                                                          , "age_in_year"
                                                          , "gender"
                                                          , "academic_year"
                                                          , "modified_by"
                                                          , "modification_date_time"
                                                          ], batch_size=500)
            
            remarks = f"Successfully read {row_count}, add rows {add_count}, modify rows {modify_count} rows from sheet '{sheet_name}'."
            save_file_export_log(filename, remarks, row_count, add_count, modify_count, 0, 0, request.user)

            return JsonResponse({
                "success": True,
                "message": remarks
            })
        except Exception as e:
            return JsonResponse({"success": False, "error": f"Error reading sheet: {e}"})
    return JsonResponse({"success": False, "error": "Missing file or sheet name."})    

@login_required(login_url='login')
def upload_student_file(request):
    template_name = 'main/upload_student.html'
    academic_year = get_active_academic_year()
    form = UploadFileForm()

    return render(request, template_name, {'form': form, 'academic_year': academic_year})