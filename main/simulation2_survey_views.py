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


@login_required(login_url='login')
def upload_simulation2_survey_file(request):
    template_name = 'main/upload_simulation2_survey.html' 
    simulations = Simulation.objects.all()

    return render(request, template_name, {'simulations': simulations})

@csrf_exempt
def process_simulation2_survey_file_sheet(request):
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
            all_survey_data = Simulation2Survey.objects.filter(simulation_id = simulation_obj.id).all()
            all_team_member_data = TeamMember.objects.filter(team__simulation_id = simulation_obj.id).all()
            all_team_data = Team.objects.filter(simulation_id = simulation_obj.id).all()
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

                original_subscrip_key = str_to_str(row.get('subscrip_key'))
                original_mail_confirm = str_to_str(row.get('mail_confirm'))
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
                match_by_field = 'mail_confirm'
                temp_student = next((s for s in all_student_data if s.email_address == mail_confirm), None)
                if temp_student is None:
                    temp_student = next((s for s in all_student_data if s.subscription_key == subscrip_key), None)
                    match_value = subscrip_key
                    match_by_field = 'subscription_key'
                
                if temp_student is None:
                    temp_student = next((s for s in all_student_data if s.email_address == email), None)
                    match_value = email
                    match_by_field = 'email'

                if temp_student is None:
                    no_student_found_list.append(row_no)
                    continue

                already_exists_in_sheet = False
                if len(all_survey_current_sheet) > 0:
                    already_exists_in_sheet = any(obj.student.id == temp_student.id for obj in all_survey_current_sheet)
                
                if already_exists_in_sheet == True:
                    duplicate_student_found_list.append(row_no)
                    continue

                temp_team_member = next((s for s in all_team_member_data if s.student.id == temp_student.id), None)#TeamMember.objects.filter(student_id = temp_student.id, team__simulation_id = simulation_obj.id).first()
                if temp_team_member is None:
                    no_team_found_list.append(row_no)
                    continue
                temp_team = next((s for s in all_team_data if s.id == temp_team_member.team_id), None)#Team.objects.get(pk = temp_team_member.team_id)

                is_new = True
                temp_survey = survey_lookup.get((temp_student.id, simulation_obj.id))#next((s for s in all_survey_data if s.student_id == temp_student.id and s.simulation_id == simulation_id), None)
                if temp_survey is None:
                    temp_survey = Simulation2Survey(
                        student = temp_student,
                        simulation = simulation_obj,
                        team = temp_team,
                        team_member = temp_team_member,
                        creation_date_time = timezone.now(),
                        created_by = request.user
                    )
                else:
                    is_new = False
                temp_survey.modification_date_time = timezone.now()
                temp_survey.modified_by = request.user

                temp_survey.subscrip_key = original_subscrip_key
                temp_survey.mail_confirm = original_mail_confirm
                temp_survey.email = email
                temp_survey.match_value = match_value
                temp_survey.match_by_field = match_by_field
                temp_survey.row_number = row_no

                all_survey_current_sheet.append(temp_survey)

                temp_dto = next((d for d in team_data_list if d.team_id == temp_team.id), None)
                if temp_dto is None:
                    temp_dto = TeamSim2Survey (
                        team_id=temp_team.id,
                        team_size= 3 if temp_team.is_3pt == True else 2,
                        team_size_found=1
                    )
                    team_data_list.append(temp_dto)
                else:
                    temp_dto.team_size_found +=1

                temp_survey.indiv_time_spent = str_to_bigint(row.get('indiv_time_spent'), 0)
                temp_dto.indiv_time_spent += temp_survey.indiv_time_spent

                temp_survey.joint_time_spent = str_to_bigint(row.get('joint_time_spent'), 0)
                temp_dto.joint_time_spent += temp_survey.joint_time_spent

                temp_survey.days_in_person = str_to_bigint(row.get('days_in_person'), 0)
                temp_dto.days_in_person += temp_survey.days_in_person

                temp_survey.responsib_clear = str_to_bigint(row.get('responsib_clear'), 0)
                temp_dto.responsib_clear += temp_survey.responsib_clear

                temp_survey.responsib_own = str_to_bigint(row.get('responsib_own'), 0)
                temp_dto.responsib_own += temp_survey.responsib_own

                temp_survey.responsib_change = str_to_bigint(row.get('responsib_change'), 0)
                temp_dto.responsib_change += temp_survey.responsib_change

                temp_survey.areas_change_1 = str_to_bigint(row.get('areas_change_1'), 0)
                temp_survey.areas_change_2 = str_to_bigint(row.get('areas_change_2'), 0)
                temp_survey.areas_change_3 = str_to_bigint(row.get('areas_change_3'), 0)
                temp_survey.areas_change_4 = str_to_bigint(row.get('areas_change_4'), 0)
                temp_survey.areas_change_indiv = (temp_survey.areas_change_1 + temp_survey.areas_change_2 + temp_survey.areas_change_3 
                                                  + temp_survey.areas_change_4) / 4
                temp_dto.areas_change_indiv += temp_survey.areas_change_indiv

                temp_survey.responsib_outside = str_to_bigint(row.get('responsib_outside'), 0)
                temp_dto.responsib_outside += temp_survey.responsib_outside

                
                # if temp_student.email_address == 'amunk25@student.sdu.dk':
                #     print(f"row {row_no}, { temp_survey.responsib_outside}, {original_subscrip_key}")
                
                temp_survey.ta_a = str_to_bigint(row.get('ta_a'), 0)
                temp_survey.ta_b = str_to_bigint(row.get('ta_b'), 0)
                temp_survey.ta_c = str_to_bigint(row.get('ta_c'), 0)
                temp_survey.ta_indiv = (temp_survey.ta_a + temp_survey.ta_b + temp_survey.ta_c) / 3
                temp_dto.ta_indiv += temp_survey.ta_indiv

                temp_survey.la_a = str_to_bigint(row.get('la_a'), 0)
                temp_survey.la_b = str_to_bigint(row.get('la_b'), 0)
                temp_survey.la_c = str_to_bigint(row.get('la_c'), 0)
                temp_survey.la_indiv = (temp_survey.la_a + temp_survey.la_b + temp_survey.la_c) / 3
                temp_dto.la_indiv += temp_survey.la_indiv

                temp_survey.tms_s1 = str_to_bigint(row.get('tms_s1'), 0)
                temp_survey.tms_s2 = str_to_bigint(row.get('tms_s2'), 0)
                temp_survey.tms_s3 = str_to_bigint(row.get('tms_s3'), 0)
                temp_survey.tms_s4 = str_to_bigint(row.get('tms_s4'), 0)
                temp_survey.tms_s5 = str_to_bigint(row.get('tms_s5'), 0)
                temp_survey.tms_spec_indiv = (temp_survey.tms_s1 + temp_survey.tms_s2 + temp_survey.tms_s3 + temp_survey.tms_s4 + temp_survey.tms_s5) / 5
                temp_dto.tms_spec_indiv += temp_survey.tms_spec_indiv

                temp_survey.tms_cred1 = str_to_bigint(row.get('tms_cred1'), 0)
                temp_survey.tms_cred2 = str_to_bigint(row.get('tms_cred2'), 0)
                temp_survey.tms_cred3 = str_to_bigint(row.get('tms_cred3'), 0)
                temp_survey.tms_cred4 = str_to_bigint(row.get('tms_cred4'), 0)
                temp_survey.tms_cred5 = str_to_bigint(row.get('tms_cred5'), 0)
                temp_survey.tms_cred_indiv = (temp_survey.tms_cred1 + temp_survey.tms_cred2 + temp_survey.tms_cred3 + temp_survey.tms_cred4
                                               + temp_survey.tms_cred5) / 5
                temp_dto.tms_cred_indiv += temp_survey.tms_cred_indiv

                temp_survey.tms_co1 = str_to_bigint(row.get('tms_co1'), 0)
                temp_survey.tms_co2 = str_to_bigint(row.get('tms_co2'), 0)
                temp_survey.tms_co3 = str_to_bigint(row.get('tms_co3'), 0)
                temp_survey.tms_co4 = str_to_bigint(row.get('tms_co4'), 0)
                temp_survey.tms_co5 = str_to_bigint(row.get('tms_co5'), 0)
                temp_survey.tms_coord_indiv = (temp_survey.tms_co1 + temp_survey.tms_co2 + temp_survey.tms_co3 + temp_survey.tms_co4
                                               + temp_survey.tms_co5) / 5
                temp_dto.tms_coord_indiv += temp_survey.tms_coord_indiv

                temp_survey.att_market_sales = str_to_bigint(row.get('att_market_sales'), 0)
                temp_survey.att_production = str_to_bigint(row.get('att_production'), 0)
                temp_survey.att_randd = str_to_bigint(row.get('att_randd'), 0)

                temp_survey.focus_shift_1 = str_to_bigint(row.get('focus_shift_1'), 0)
                temp_survey.focus_shift_2 = str_to_bigint(row.get('focus_shift_2'), 0)
                temp_survey.focus_shift_3 = str_to_bigint(row.get('focus_shift_3'), 0)
                temp_survey.focus_shift_4 = str_to_bigint(row.get('focus_shift_4'), 0)
                temp_survey.focus_shift_indiv = (temp_survey.focus_shift_1 + temp_survey.focus_shift_2 + temp_survey.focus_shift_3 
                                                 + temp_survey.focus_shift_4) / 4
                temp_dto.focus_shift_indiv += temp_survey.focus_shift_indiv

                temp_survey.compet_import1 = str_to_bigint(row.get('compet_import1'), 0)
                temp_survey.compet_import2 = str_to_bigint(row.get('compet_import2'), 0)
                temp_survey.compet_import3 = str_to_bigint(row.get('compet_import3'), 0)
                temp_survey.compet_import_indiv = ( temp_survey.compet_import1 +  temp_survey.compet_import2 +  temp_survey.compet_import3) / 3
                temp_dto.compet_import_indiv += temp_survey.compet_import_indiv

                temp_survey.pcs_1 = str_to_bigint(row.get('pcs_1'), 0)
                temp_survey.pcs_2 = str_to_bigint(row.get('pcs_2'), 0)
                temp_survey.pcs_3 = str_to_bigint(row.get('pcs_3'), 0)
                temp_survey.pcs_indiv = (temp_survey.pcs_1 + temp_survey.pcs_2 + temp_survey.pcs_3) / 3
                temp_dto.pcs_indiv += temp_survey.pcs_indiv

                temp_survey.comments = str_to_str(row.get('comments'))

                temp_survey.statoverall_1 = str_to_bigint(row.get('statoverall_1'), 0)
                temp_survey.statoverall_2 = str_to_bigint(row.get('statoverall_2'), 0)
                temp_survey.statoverall_3 = str_to_bigint(row.get('statoverall_3'), 0)
                temp_survey.statoverall_4 = str_to_bigint(row.get('statoverall_4'), 0)
                temp_survey.statoverall_5 = str_to_bigint(row.get('statoverall_5'), 0)
                temp_survey.statoverall_indiv = (temp_survey.statoverall_1 + temp_survey.statoverall_2 + temp_survey.statoverall_3 
                                                 + temp_survey.statoverall_4 + temp_survey.statoverall_5) / 5
                temp_dto.statoverall_indiv += temp_survey.statoverall_indiv

                if is_new == True:
                    add_data_list.append(temp_survey)
                else:
                    update_data_list.append(temp_survey)

            for dto in team_data_list:
                size = dto.team_size_found
                dto.indiv_time_spent_t = dto.indiv_time_spent / size
                dto.joint_time_spent_t = dto.joint_time_spent / size
                dto.days_in_person_t = dto.days_in_person / size
                dto.responsib_clear_t = dto.responsib_clear / size
                dto.responsib_own_t = dto.responsib_own / size
                dto.responsib_change_t = dto.responsib_change / size
                dto.areas_change_team = dto.areas_change_indiv / size
                dto.responsib_outside_t = dto.responsib_outside / size
                dto.ta_team = dto.ta_indiv / size
                dto.la_team = dto.la_indiv / size
                dto.tms_spec_team = dto.tms_spec_indiv / size
                dto.tms_cred_team = dto.tms_cred_indiv / size
                dto.tms_coord_team = dto.tms_coord_indiv / size
                dto.focus_shift_team = dto.focus_shift_indiv / size
                dto.compet_import_team = dto.compet_import_indiv / size
                dto.pcs_team = dto.pcs_indiv / size
                dto.statoverall_team = dto.statoverall_indiv / size

                temp_team_data_list = [obj for obj in all_survey_current_sheet if obj.team.id == dto.team_id]
                for tempData in temp_team_data_list:
                    tempData.indiv_time_spent_t = dto.indiv_time_spent_t
                    tempData.joint_time_spent_t = dto.joint_time_spent_t
                    tempData.days_in_person_t = dto.days_in_person_t
                    tempData.responsib_clear_t = dto.responsib_clear_t
                    tempData.responsib_own_t = dto.responsib_own_t
                    tempData.responsib_change_t = dto.responsib_change_t
                    tempData.areas_change_team = dto.areas_change_team
                    tempData.responsib_outside_t = dto.responsib_outside_t
                    tempData.ta_team = dto.ta_team
                    tempData.la_team = dto.la_team
                    tempData.tms_spec_team = dto.tms_spec_team
                    tempData.tms_cred_team = dto.tms_cred_team
                    tempData.tms_coord_team = dto.tms_coord_team
                    tempData.focus_shift_team = dto.focus_shift_team
                    tempData.compet_import_team = dto.compet_import_team
                    tempData.pcs_team = dto.pcs_team
                    tempData.statoverall_team = dto.statoverall_team
                    tempData.team_size = dto.team_size
                    tempData.team_size_found = dto.team_size_found

            if len(add_data_list) > 0:
                Simulation2Survey.objects.bulk_create(add_data_list, batch_size=500)
            if len(update_data_list) > 0:
                Simulation2Survey.objects.bulk_update(update_data_list, ["indiv_time_spent", "indiv_time_spent_t"
                                                          , "joint_time_spent", "joint_time_spent_t"
                                                          , "days_in_person", "days_in_person_t"
                                                          , "responsib_clear", "responsib_clear_t"
                                                          , "responsib_own", "responsib_own_t"
                                                          , "responsib_change", "responsib_change_t"
                                                          , "areas_change_1", "areas_change_2", "areas_change_3", "areas_change_4", "areas_change_indiv", "areas_change_team"
                                                          , "responsib_outside", "responsib_outside_t"
                                                          , "ta_a", "ta_b", "ta_c", "ta_indiv", "ta_team"
                                                          , "la_a", "la_b", "la_c", "la_indiv", "la_team"
                                                          , "tms_s1", "tms_s2", "tms_s3", "tms_s4", "tms_s5", "tms_spec_indiv", "tms_spec_team"
                                                          , "tms_cred1", "tms_cred2", "tms_cred3", "tms_cred4", "tms_cred5", "tms_cred_indiv", "tms_cred_team"
                                                          , "tms_co1", "tms_co2", "tms_co3", "tms_co4", "tms_co5", "tms_coord_indiv", "tms_coord_team"
                                                          , "att_market_sales"
                                                          , "att_production"
                                                          , "att_randd"
                                                          , "focus_shift_1", "focus_shift_2", "focus_shift_3", "focus_shift_4", "focus_shift_indiv", "focus_shift_team"
                                                          , "compet_import1", "compet_import2", "compet_import3", "compet_import_indiv", "compet_import_team"
                                                          , "pcs_1", "pcs_2", "pcs_3", "pcs_indiv", "pcs_team"
                                                          , "statoverall_1", "statoverall_2", "statoverall_3", "statoverall_4", "statoverall_5", "statoverall_indiv", "statoverall_team"
                                                          , "team_size"
                                                          , "team_size_found"
                                                          , "comments"
                                                          , "subscrip_key"
                                                          , "mail_confirm"
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

@login_required(login_url='login')
def simulation2_survey_report(request):
    template_name = 'main/simulation2_survey_report.html'
    error_message = ""
    rows = []
    total_rows = 0
    page_obj = None
    simulation_list = None
    filters = {}
    campus_list = None
    market_list = None
    try:
        per_page = request.GET.get("per_page", settings.PER_PAGE)
        filters = {
            "simulation_ids":  request.GET.getlist("simulation_ids", None),
            "student_name": request.GET.get("student_name", "").strip(),
            "teamID": request.GET.get("teamID", ""),
            "is_3pt": request.GET.get("is_3pt", -1),
            "is_fix_alloc": request.GET.get("is_fix_alloc", -1), 
            "is_mmf": request.GET.get("is_mmf", -1),
            "campus": request.GET.get("campus", ""), 
            "per_page": request.GET.get("per_page", settings.PER_PAGE),
        }
        simulation_list = Simulation.objects.all()
        campus_list = get_all_campus()
        rows = get_team_member_report(filters)
        paginator = Paginator(rows, per_page)
        page_number = request.GET.get('page')
        page_obj = paginator.get_page(page_number)
        total_rows = paginator.count
    except Exception as e:
        error_message = e
    return render(request, template_name, {"page_obj": page_obj, "filters": filters
                                           , "total_rows": total_rows, "simulation_list": simulation_list
                                           , "error_message": error_message, "campus_list" : campus_list})
