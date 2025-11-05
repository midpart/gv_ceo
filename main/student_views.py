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

            for index, row in df.iterrows():
                studienr = row.get('Studienr')
                name = str_to_str(row.get('Name'))
                emailAdress = str_to_str(row.get('EmailAdress'))
                campus = str_to_str(row.get('Campus'))
                subscriptionKey = row.get('SubscriptionKey')
                marketMemberNum = row.get('MarketMemberNum')
                simulationNumber = row.get('SimulationNumber')
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
                temp_student.market_member_num = str_to_bigint(marketMemberNum)
                temp_student.simulation_number = str_to_bigint(simulationNumber)
                temp_student.age_in_year = str_to_bigint(age)
                temp_student.gender = gender
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
                                                          , "market_member_num"
                                                          , "simulation_number"
                                                          , "age_in_year"
                                                          , "gender"
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
    form = UploadFileForm()

    return render(request, template_name, {'form': form})

    # Get your filtered data
    rows = []
    filters = get_filter(request)
    rows = get_student_score_report(filters)

    # Create workbook
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = f"Students_score_report"
    file_name = f"Students_score_report_{timezone.now().strftime("%Y-%m-%d-%H-%M-%S")}"
    # Add header
    ws.append(["ID", "Studienr", "Name", "Age", "Gender", "EmailAddress", "Campus", "SubscriptionKey", "Player Id", "Company"
               , "GoVenture Subscription Key | Simulation Number", "Rubric Score", "Balanced Score", "Participation Score"
               , "Participation Score Info", "Rank Score", "HR Score", "Ethics Score", "Competency Quiz", "Team Evaluation"
               , "Period joined", "Tutorial Quiz"])

    # Add data
    for row in rows:
        #ws.append(row)
        ws.append([row["id"], row["studienr"], row["name"], row["age"], row["gender"], row["email_address"], row["campus"], row["subscription_key"], row["player_id"], 
                   row["company"], f"{row["go_venture_subscription_key"]} | #{row["go_venture_simulation_number"]}", row["rubric_score_percentage"], 
                   row["balanced_score_percentage"], row["participation_percentage"], f"({row["participation_in"]} of {row["participation_total"]})"
                   , row["rank_score_percentage"], row["hr_score_percentage"], row["ethics_score_percentage"], row["competency_quiz_percentage"], 
                   row["team_evaluation_percentage"], row["period_joined"], row["tutorial_quiz_percentage"]])

    # Prepare response
    response = HttpResponse(
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
    response["Content-Disposition"] = f'attachment; filename="{file_name}.xlsx"'

    wb.save(response)
    return response