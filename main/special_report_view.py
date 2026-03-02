from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from .forms import UploadFileForm, MarketForm
from .query import get_team_member_report, get_all_campus
from .common import *
import pandas as pd
from django import forms
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from .models import Student, Simulation, Simulation2Survey, TeamMember, Team
from django.utils import timezone
from django.core.paginator import Paginator
from django.conf import settings
import re
import openpyxl
from django.http import HttpResponse
from .dto import TeamSim2Survey
import math
import io
import tempfile


@login_required(login_url='login')
def download_special_report(request):
    template_name = 'main/download_special_report.html' 
    simulations = Simulation.objects.all()
    academic_year = get_active_academic_year()

    return render(request, template_name, {'simulations': simulations, 'academic_year': academic_year})

@csrf_exempt
def process_download_special_report(request):
    if request.method == "POST" and request.FILES.get("file"):
        excel_file = request.FILES["file"]
        simulation_id = request.POST.get("simulation_id")
        academic_year = get_active_academic_year()
        try:
            check_file(excel_file)
            simulation_obj = Simulation.objects.filter(pk = simulation_id, academic_year=academic_year).first()
            if simulation_obj is None:
                raise ValueError(f"Unable to find simulation with id : {simulation_id}")
            
            with tempfile.NamedTemporaryFile(delete=False) as tmp:
                for chunk in excel_file.chunks():
                    tmp.write(chunk)
                tmp_path = tmp.name

            df = pd.read_csv(tmp_path, encoding='cp1252', sep=";")
            
            filename = excel_file.name
            all_students = Student.objects.filter(academic_year=academic_year).all()
            filters = {
                    "simulation_id": simulation_obj.id,
                    "academic_year": academic_year
                }
            all_score_report = get_student_score_report(filters)
            new_rows = []
            row_count = 0
            for index, row in df.iterrows():
                row_count +=1

                Studienummer = row["Studienummer"]
                Navn = row["Navn"]
                StadsPersonId = row["StadsPersonId"]
                Email = row["Email"]
                # Karakter = row["Karakter"]
                # dato = row["Mundtlig eksamen - dato"]
                # starttid = row["Mundtlig eksamen - starttid"]
                # sluttid = row["Mundtlig eksamen - sluttid"]
                # lokale = row["Mundtlig eksamen - lokale"]
                # Mødetid = row["Mødetid"]
                # Gruppe = row["Gruppe"]

                temp_student_score = next((s for s in all_score_report if s["email_address"] == Email), None)#all_students.filter( email_address = Email).first()
                temp_student = next((s for s in all_students if s.email_address== Email), None)
                balance_score = None
                rubic_score = None
                team_evaluation = None
                is_3pt = None
                is_mmf = None
                is_fix_alloc = None
                subscription_key = temp_student.subscription_key if temp_student is not None else ""
                isFoundStudent =  "1" if temp_student is not None else "0"
                if temp_student_score is not None:
                    balance_score = temp_student_score["balanced_score_percentage"]
                    rubic_score = temp_student_score["rubric_score_percentage"]
                    team_evaluation = temp_student_score["team_evaluation_percentage"]
                    is_3pt = "1" if temp_student_score["is_3pt"] == True else "0"
                    is_mmf = "1" if temp_student_score["is_mmf"] == True else "0"
                    is_fix_alloc = "1" if temp_student_score["is_fix_alloc"] == True else "0"

                new_rows.append({
                    "Studienummer": Studienummer,
                    "Navn": Navn,
                    "StadsPersonId": StadsPersonId,
                    "Email": Email,
                    "Subscription Key": subscription_key,
                    # "Karakter": Karakter,
                    # "Mundtlig eksamen - dato": dato,
                    # "Mundtlig eksamen - starttid": starttid,
                    # "Mundtlig eksamen - sluttid": sluttid,
                    # "Mundtlig eksamen - lokal": lokale,
                    # "Mødetid": Mødetid,
                    # "Gruppe": Gruppe,
                    "Balanced score": balance_score,
                    "Rubric Score": rubic_score,
                    "Team Evaluation": team_evaluation,
                    # "is_3pt": is_3pt,
                    # "is_mmf": is_mmf,
                    # "is_fix_alloc": is_fix_alloc,
                    "isFoundStudent": isFoundStudent,
                })
            
             # --- 3. CREATE NEW DATAFRAME ---
            new_df = pd.DataFrame(new_rows)

            # --- 4. CONVERT TO CSV STRING ---
            buffer = io.StringIO()
            new_df.to_csv(buffer, index=False, encoding="utf-8-sig")
            buffer.seek(0)
            csv_string = buffer.getvalue()

            # --- 5. RETURN FILE DOWNLOAD ---
            response = HttpResponse(csv_string, content_type="text/csv; charset=utf-8")
            response["Content-Disposition"] = 'attachment; filename=f"{filename}_processed.csv"'
            return response
        except Exception as e:
            return HttpResponse(f"Error reading sheet: {e}", status=400)
    return HttpResponse("Invalid request", status=400)  
