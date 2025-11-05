from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from .forms import UploadFileForm, MarketForm
from .query import get_student_score_report, get_all_campus
from .common import *
import pandas as pd
from django import forms
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from .models import Student, Market, Simulation, StudentScore, ImportFileLog, Team, TeamMember
from django.utils import timezone
from django.core.paginator import Paginator
from django.conf import settings
import re
import openpyxl
from django.http import HttpResponse


@login_required(login_url='login')
def upload_team_file(request):
    template_name = 'main/upload_team.html' 
    simulations = Simulation.objects.all()

    return render(request, template_name, {'simulations': simulations})

@csrf_exempt
def process_team_file_sheet(request):
    if request.method == "POST" and request.FILES.get("file"):
        excel_file = request.FILES["file"]
        sheet_name = request.POST.get("sheet_name")
        simulation_id = request.POST.get("simulation_id")
        try:
            print(excel_file.name)
            print(sheet_name)
            print(simulation_id)

            check_file(excel_file)
            simulation_obj = Simulation.objects.filter(pk = simulation_id).first()
            if simulation_obj is None:
                raise ValueError(f"Unable to find simulation with id : {simulation_id}")
            df = pd.read_excel(excel_file, sheet_name=sheet_name)
            
            filename = excel_file.name
            all_student_data = Student.objects.all()
            all_team_data = Team.objects.filter(simulation_id = simulation_id).all()
            all_team_current_sheet = []
            add_team_data = []
            update_team_data = []
            no_student_found_list = []


            for index, row in df.iterrows():
                subscriptionKey = row.get('SubscriptionKey')
                studienr = row.get('Studienr')
                main_student =  next((s for s in all_student_data if s.subscription_key == subscriptionKey), None)
                if main_student is None: 
                    no_student_found_list.append(studienr)
                    continue
                
                p1_email = row.get('Sim2P1mail')
                p2_email = row.get('Sim2P2mail')
                p3_email = row.get('Sim2P3mail')
                team_id = row.get('TeamID')
                sim_team_id = row.get('Sim2TeamID')
                fix_alloc = row.get('FixAlloc')

                team_id_parse = str_to_bigint(team_id)
                temp_team_in_db = next((t for t in all_team_data if t.team_id == team_id_parse), None)
                if temp_team_in_db is None:
                    print("Not in DB")
                else:
                    print("In DB")

                temp_team_in_current_sheet = None
                if len(all_team_current_sheet) > 0:
                    temp_team_in_current_sheet = next((t for t in all_team_current_sheet if t.team_id == team_id_parse), None)
                print(len(all_team_current_sheet))
                if temp_team_in_current_sheet is None:
                    print("Not in current sheet")
                    temp_team = Team(
                        simulation = simulation_obj,
                        team_id = team_id_parse,
                        created_by = request.user,
                        creation_date_time = timezone.now()
                    )
                    all_team_current_sheet.append(temp_team)
                else:
                    #print("In current sheet")
                    print(f"P1: {p1_email}, P2: {p2_email}, P3: {p3_email}, t_id: {team_id}, s_t_id: {sim_team_id}, f_all: {fix_alloc}")
                
                

                # marketMemberNum = row.get('MarketMemberNum')
                # simulationNumber = row.get('SimulationNumber')
                # age = row.get('Age')
                # gender = str_to_str(row.get('Gender'))
                
                # temp_student = None
                # temp_student = next((s for s in all_db_data if s.subscription_key == subscriptionKey), None)
                # is_new = False
                # if temp_student is None:
                #     is_new = True
                #     temp_student = Student(
                #         subscription_key = subscriptionKey,
                #         created_by = request.user,
                #         creation_date_time = timezone.now()
                #     )

                # temp_student.studienr = str_to_bigint(studienr)
                # temp_student.name = name
                # temp_student.email_address = emailAdress
                # temp_student.campus = campus
                # temp_student.market_member_num = str_to_bigint(marketMemberNum)
                # temp_student.simulation_number = str_to_bigint(simulationNumber)
                # temp_student.age_in_year = str_to_bigint(age)
                # temp_student.gender = gender
                # temp_student.modified_by = request.user
                # temp_student.modification_date_time = timezone.now()
        
                # if is_new:
                #     add_data.append(temp_student)
                # else:
                #     update_data.append(temp_student)

            # row_count = len(df)
            # add_count = len(add_data)
            # modify_count = len(update_data)

            # if add_count > 0:
            #     Student.objects.bulk_create(add_data, batch_size=500)
            # if modify_count > 0:
            #     Student.objects.bulk_update(update_data, ["studienr"
            #                                               , "name"
            #                                               , "email_address"
            #                                               , "campus"
            #                                               , "market_member_num"
            #                                               , "simulation_number"
            #                                               , "age_in_year"
            #                                               , "gender"
            #                                               , "modified_by"
            #                                               , "modification_date_time"
            #                                               ], batch_size=500)
            
            # remarks = f"Successfully read {row_count}, add rows {add_count}, modify rows {modify_count} rows from sheet '{sheet_name}'."
            # save_file_export_log(filename, remarks, row_count, add_count, modify_count, 0, 0, request.user)
            remarks = ""
            return JsonResponse({
                "success": True,
                "message": remarks
            })
        except Exception as e:
            return JsonResponse({"success": False, "error": f"Error reading sheet: {e}"})
    return JsonResponse({"success": False, "error": "Missing file or sheet name."})    
