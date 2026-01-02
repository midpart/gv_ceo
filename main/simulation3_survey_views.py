from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from .forms import UploadFileForm, MarketForm
from .query import get_team_member_report, get_all_campus
from .common import *
import pandas as pd
from django import forms
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from .models import Student, Simulation, Simulation3Survey
from django.utils import timezone
from django.core.paginator import Paginator
from django.conf import settings
import re
import openpyxl
from django.http import HttpResponse
import math


@login_required(login_url='login')
def upload_simulation3_survey_file(request):
    template_name = 'main/upload_simulation3_survey.html' 
    simulations = Simulation.objects.all()

    return render(request, template_name, {'simulations': simulations})

@csrf_exempt
def process_simulation3_survey_file_sheet(request):
    if request.method == "POST" and request.FILES.get("file"):
        excel_file = request.FILES["file"]
        sheet_name = request.POST.get("sheet_name")
        simulation_id = request.POST.get("simulation_id")
        try:
            check_file(excel_file)
            simulation_obj = Simulation.objects.filter(pk = simulation_id).first()
            if simulation_obj is None:
                raise ValueError(f"Unable to find simulation with id : {simulation_id}")
            df = pd.read_excel(excel_file, sheet_name=sheet_name)
            
            filename = excel_file.name
            all_student_data = Student.objects.all()
            all_survey_data = Simulation3Survey.objects.filter(simulation_id = simulation_obj.id).all()
            all_survey_current_sheet = []
            no_student_found_list = []
            duplicate_student_found_list = []
            no_team_found_list = []

            add_data_list = []
            update_data_list = []

            row_count = 0
            row_no = 1
            team_data_list = []
            survey_lookup = {
                (s.student_id, s.simulation_id): s
                for s in all_survey_data
            }
            for index, row in df.iterrows():
                row_no +=1
                row_count +=1

                original_subscrip_key = str_to_str(row.get('sim3_subkey'))
                original_mail_confirm = str_to_str(row.get('sim3_confirm_email'))
                email = str_to_str(row.get('email'))

                subscrip_key = original_subscrip_key
                mail_confirm = original_mail_confirm

                if not subscrip_key and not mail_confirm and not email:
                    no_student_found_list.append(row_no)
                    continue

                if mail_confirm:
                    mail_confirm = mail_confirm.lower()
                    mail_confirm = mail_confirm.replace("@student.sdu.com", "@student.sdu.dk")
                    mail_confirm = mail_confirm.replace("@sdu.student.dk", "@student.sdu.dk")
                    mail_confirm = mail_confirm.replace("@student.dk", "@student.sdu.dk")
                    mail_confirm = mail_confirm.replace("@atudent.dk", "@student.sdu.dk")
                    mail_confirm = mail_confirm.replace("@sdu.student.dk", "@student.sdu.dk")
                    mail_confirm = mail_confirm.replace("@studnet.sdu.dk", "@student.sdu.dk")

                if subscrip_key:
                    subscrip_key = subscrip_key.lower()
                    subscrip_key = subscrip_key.replace(".", "")

                temp_student = None 
                temp_team = None
                temp_team_member = None

                match_value = mail_confirm
                match_by_field = 'sim3_confirm_email'
                temp_student = next((s for s in all_student_data if s.email_address == mail_confirm), None)
                if temp_student is None:
                    temp_student = next((s for s in all_student_data if s.subscription_key == subscrip_key), None)
                    match_value = subscrip_key
                    match_by_field = 'sim3_subkey'
                
                if temp_student is None:
                    temp_student = next((s for s in all_student_data if s.email_address == email), None)
                    match_value = email
                    match_by_field = 'email'

                if temp_student is None:
                    no_student_found_list.append(row_no)
                    continue
                
                
                statoverall_4 = str_to_bigint(row.get('statoverall_4'), 0)
                is_complete = False
                if statoverall_4 == 1:
                    is_complete = True

                already_exists_in_sheet = None
                if len(all_survey_current_sheet) > 0:
                    already_exists_in_sheet = next((s for s in all_survey_current_sheet if s.student.id == temp_student.id), None)#any(obj.student.id == temp_student.id for obj in all_survey_current_sheet)
                
                # already have found this row and current row is not complete
                if already_exists_in_sheet is not None and is_complete == False:
                    duplicate_student_found_list.append(row_no)
                    continue

                 # already have found this row and that was complete also   
                if  already_exists_in_sheet is not None and already_exists_in_sheet.statoverall_4 == 1:
                    duplicate_student_found_list.append(row_no)
                    continue

                is_new = True
                temp_survey = survey_lookup.get((temp_student.id, simulation_obj.id))#next((s for s in all_survey_data if s.student_id == temp_student.id and s.simulation_id == simulation_id), None)
                if temp_survey is None:
                    if already_exists_in_sheet is None:
                        temp_survey = Simulation3Survey(
                            student = temp_student,
                            simulation = simulation_obj,
                            creation_date_time = timezone.now(),
                            created_by = request.user
                        )
                    else:
                        temp_survey = already_exists_in_sheet 
                else:
                    is_new = False
                temp_survey.modification_date_time = timezone.now()
                temp_survey.modified_by = request.user

                temp_survey.sim3_subkey = original_subscrip_key
                temp_survey.sim3_confirm_email = original_mail_confirm
                temp_survey.email = email
                temp_survey.match_value = match_value
                temp_survey.match_by_field = match_by_field
                temp_survey.row_number = row_no

                all_survey_current_sheet.append(temp_survey)

                temp_survey.sim3_day1 = str_to_str(row.get('sim3_day1'))
                temp_survey.sim3_day2 = str_to_str(row.get('sim3_day2'))
                temp_survey.sim3_day3 = str_to_str(row.get('sim3_day3'))
                temp_survey.sim3_day4 = str_to_str(row.get('sim3_day4'))
                temp_survey.sim3_day5 = str_to_str(row.get('sim3_day5'))

                temp_survey.statoverall_1 = str_to_bigint(row.get('statoverall_1'), 0)
                temp_survey.statoverall_2 = str_to_bigint(row.get('statoverall_2'), 0)
                temp_survey.statoverall_3 = str_to_bigint(row.get('statoverall_3'), 0)
                temp_survey.statoverall_4 = str_to_bigint(row.get('statoverall_4'), 0)
                temp_survey.statoverall_5 = str_to_bigint(row.get('statoverall_5'), 0)

                # only add when we did not do that before
                if already_exists_in_sheet is None:
                    if is_new == True:
                        add_data_list.append(temp_survey)
                    else:
                        update_data_list.append(temp_survey)

            if len(add_data_list) > 0:
                Simulation3Survey.objects.bulk_create(add_data_list, batch_size=500)
            if len(update_data_list) > 0:
                Simulation3Survey.objects.bulk_update(update_data_list, ["sim3_day1", "sim3_day2", "sim3_day3", "sim3_day4", "sim3_day5" 
                                                          , "statoverall_1", "statoverall_2", "statoverall_3", "statoverall_4", "statoverall_5"
                                                          , "sim3_subkey"
                                                          , "sim3_confirm_email"
                                                          , "email"
                                                          , "match_value"
                                                          , "match_by_field"
                                                          , "row_number"
                                                          , "modified_by"
                                                          , "modification_date_time"
                                                          ], batch_size=500)
            

            additional_info = ""
            failed_count = 0
            if len(no_student_found_list) > 0:
                additional_info += f", no student found for row no {len(no_student_found_list)} [{', '.join(map(str,no_student_found_list))}]"
                failed_count += len(no_student_found_list)
            if len(no_team_found_list) > 0:
                additional_info += f", no team found for row no {len(no_team_found_list)} [{', '.join(map(str,no_team_found_list))}]"
                failed_count += len(no_team_found_list)
            if len(duplicate_student_found_list) > 0:
                additional_info += f", duplicate student found for row no {len(duplicate_student_found_list)} [{', '.join(map(str,duplicate_student_found_list))}]"
                failed_count += len(duplicate_student_found_list)

            remarks = f"Successfully read {len(df)}, add teams {len(add_data_list)}, modify teams {len(update_data_list)} {additional_info} rows from sheet '{sheet_name}'."
            save_file_export_log(filename, remarks, len(df), len(add_data_list), len(update_data_list), len(no_student_found_list), len(duplicate_student_found_list), request.user)
            return JsonResponse({
                "success": True,
                "message": remarks
            })
        except Exception as e:
            return JsonResponse({"success": False, "error": f"Error reading sheet: {e}"})
    return JsonResponse({"success": False, "error": "Missing file or sheet name."})    

