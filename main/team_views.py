from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from .forms import UploadFileForm, MarketForm
from .query import get_team_member_report, get_all_campus
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

def get_team_member(all_old_members, team, player, user, role, order):
    temp_data = next((t for t in all_old_members if t.student_id == player.id), None) if len(all_old_members) > 0 else None
    #TeamMember.objects.filter(team_id = team.id , student_id = player.id).first()
    is_new = False
    if temp_data is None:
        is_new = True
        temp_data = TeamMember(
            team = team,
            student = player,
            creation_date_time = timezone.now(),
            created_by = user
        )
    temp_data.modification_date_time = timezone.now()
    temp_data.modified_by = user
    temp_data.role = role
    temp_data.teammember_order = order

    return (is_new, temp_data)

@csrf_exempt
def process_team_file_sheet(request):
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
            all_team_data = Team.objects.filter(simulation_id = simulation_id).all()
            all_team_current_sheet = []
            add_team_data = []
            update_team_data = []
            add_team_member_data = []
            update_team_member_data = []
            delete_team_member_data = []
            no_student_found_list = []
            row_count = 0
            for index, row in df.iterrows():
                teamID = row.get('TeamID')
                teamID_parse = str_to_bigint(teamID)
                row_count += 1

                temp_team = None
                is_new = False

                temp_team_in_current_sheet = None
                if len(all_team_current_sheet) > 0:
                    temp_team_in_current_sheet = next((t for t in all_team_current_sheet if t.teamID == teamID_parse), None)
                if temp_team_in_current_sheet is None:
                    temp_team = Team(
                        simulation = simulation_obj,
                        teamID = teamID_parse,
                        created_by = request.user,
                        creation_date_time = timezone.now()
                    )
                    all_team_current_sheet.append(temp_team)
                else:
                    continue

                temp_team_in_db = next((t for t in all_team_data if t.teamID == teamID_parse), None)
                if temp_team_in_db is None:
                    is_new = True
                else:
                    temp_team = temp_team_in_db
                
                p1_email = row.get('Sim2P1mail')
                p2_email = row.get('Sim2P2mail')
                p3_email = row.get('Sim2P3mail')
                sim_team_id = row.get('Sim2TeamID')
                fix_alloc = str_to_bigint(row.get('FixAlloc'))
                fix_alloc_parse = False
                if fix_alloc == 1:
                    fix_alloc_parse = True

                p1 = next((s for s in all_student_data if s.email_address == p1_email), None)
                p1 = p1 if p1 is not None else next((s for s in all_student_data if s.name == p1_email), None)

                p2 = next((s for s in all_student_data if s.email_address == p2_email), None)
                p2 = p2 if p2 is not None else next((s for s in all_student_data if s.name == p2_email), None)

                p3 = next((s for s in all_student_data if s.email_address == p3_email), None)
                p3 = p3 if p3 is not None else next((s for s in all_student_data if s.name == p3_email), None)

                if p1_email and pd.isna(p1_email) == False and p1 is None:
                    no_student_found_list.append(teamID)
                    continue

                if p2_email and pd.isna(p2_email) == False and p2 is None:
                    no_student_found_list.append(teamID)
                    continue

                if p3_email and pd.isna(p3_email) == False and p3 is None:
                    no_student_found_list.append(teamID)
                    continue
                
                male_count = 0
                female_count = 0
                all_old_members = []
                if is_new == False:
                  all_old_members = TeamMember.objects.filter(team_id = temp_team.id).all()
                new_members = []
                if p1 is not None:
                    role = "Production" if fix_alloc_parse == True else ""
                    (is_new_p1, memebr1) = get_team_member(all_old_members, temp_team, p1, request.user, role, 1)
                    new_members.append(memebr1)
                    if is_new_p1:
                        add_team_member_data.append(memebr1)
                    else: 
                        update_team_member_data.append(memebr1)

                    if p1.gender == "Male":
                        male_count += 1
                    elif p1.gender == "Female":
                        female_count += 1

                if p2 is not None:
                    role = "Marketing" if fix_alloc_parse == True else ""
                    (is_new_p2, memebr2) = get_team_member(all_old_members, temp_team, p2, request.user, role, 2)
                    new_members.append(memebr2)
                    if is_new_p2:
                        add_team_member_data.append(memebr2)
                    else: 
                        update_team_member_data.append(memebr2)

                    if p2.gender == "Male":
                        male_count += 1
                    elif p2.gender == "Female":
                        female_count += 1

                if p3 is not None:
                    role = "Rnd" if fix_alloc_parse == True else ""
                    (is_new_p3, memebr3) = get_team_member(all_old_members, temp_team, p3, request.user, role, 3)
                    new_members.append(memebr3)
                    if is_new_p3:
                        add_team_member_data.append(memebr3)
                    else: 
                        update_team_member_data.append(memebr3)

                    if p3.gender == "Male":
                        male_count += 1
                    elif p3.gender == "Female":
                        female_count += 1
                if len(all_old_members) > 0 and len(new_members) > 0:
                    for old_member in all_old_members:
                        has_team_member = next((t for t in new_members if t.student_id == old_member.student_id), None)
                        if has_team_member is None:
                            delete_team_member_data.append(old_member)
                
                if len(new_members) == 0:
                    no_student_found_list.append(teamID)
                    continue

                temp_team.sim_team_id = sim_team_id
                temp_team.is_fix_alloc = fix_alloc_parse
                temp_team.is_mmf = True if male_count > 0 and female_count > 0 else False
                temp_team.is_3pt = True if male_count + female_count == 3 else False
                temp_team.modification_date_time = timezone.now()
                temp_team.modified_by = request.user

                if is_new:
                    add_team_data.append(temp_team)
                else: 
                    update_team_data.append(temp_team)

            if len(add_team_data) > 0:
                Team.objects.bulk_create(add_team_data, batch_size=500)
            if len(update_team_data) > 0:
                Team.objects.bulk_update(update_team_data, ["name"
                                                          , "sim_team_id"
                                                          , "is_mmf"
                                                          , "is_3pt"
                                                          , "is_fix_alloc"
                                                          , "modified_by"
                                                          , "modification_date_time"
                                                          ], batch_size=500)

            if len(add_team_member_data) > 0:
                TeamMember.objects.bulk_create(add_team_member_data, batch_size=500)
            if len(update_team_member_data) > 0:
                TeamMember.objects.bulk_update(update_team_member_data, ["role"
                                                                        , "teammember_order" 
                                                                        , "modified_by"
                                                                        , "modification_date_time"
                                                                        ], batch_size=500)
            if len(delete_team_member_data) > 0:
                TeamMember.objects.filter(id__in=[obj.id for obj in delete_team_member_data]).delete()
            
            additional_info = ""
            failed_count = 0
            if len(no_student_found_list) > 0:
                additional_info += f", no student found for team id {len(no_student_found_list)} [{', '.join(map(str,no_student_found_list))}]"
                failed_count += len(no_student_found_list)

            remarks = f"Successfully read {len(df)}, add teams {len(add_team_data)}, modify teams {len(update_team_data)}, add team members {len(add_team_member_data)}, update team members {len(update_team_member_data)} {additional_info} rows from sheet '{sheet_name}'."
            save_file_export_log(filename, remarks, len(df), len(add_team_data), len(update_team_data), len(no_student_found_list), 0, request.user)
            return JsonResponse({
                "success": True,
                "message": remarks
            })
        except Exception as e:
            return JsonResponse({"success": False, "error": f"Error reading sheet: {e}"})
    return JsonResponse({"success": False, "error": "Missing file or sheet name."})    

@login_required(login_url='login')
def team_member_report(request):
    template_name = 'main/team_member_report.html'
    error_message = ""
    rows = []
    total_rows = 0
    page_obj = None
    simulation_list = None
    filters = {}
    campus_list = None
    market_list = None
    try:
        print(request.GET.getlist("simulation_ids", None))
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
