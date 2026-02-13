from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from .forms import UploadFileForm, MarketForm
from .query import get_student_score_report, get_all_campus
from .common import *
import pandas as pd
from django import forms
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from .models import Student, Market, Simulation, StudentScore, Team, TeamMember
from django.utils import timezone
from django.core.paginator import Paginator
from django.conf import settings
import re
import openpyxl
from django.http import HttpResponse

# Create your views here.

@login_required(login_url='login')
def upload_student_score_file(request):
    academic_year = get_active_academic_year()
    template_name = 'main/upload_student_score.html' 
    simulations = Simulation.objects.filter(academic_year=academic_year).all()

    return render(request, template_name, {'simulations': simulations, 'academic_year': academic_year})

@csrf_exempt
def get_markets(request):
    if request.method == "POST" and request.FILES.get("file"):
        uploaded_file = request.FILES["file"]
        academic_year = get_active_academic_year()
        try:
            check_file(uploaded_file)
            file_name = uploaded_file.name
            simulation_id = request.POST.get('simulation_id')
            simulation_obj = get_object_or_404(Simulation, pk=simulation_id)
            if simulation_obj.academic_year != academic_year:
                raise ValueError (f"This simulation({simulation_obj.name}) is not for current academic year({academic_year}).")
            name_array = parse_file_name(file_name)
            market_number = None
            if name_array is not None and len(name_array) == 2:
                market_number = str_to_bigint(name_array[0])
                name = name_array[1]

                market_obj = Market.objects.filter(market_number = market_number).first()
                if market_obj is None: 
                    market_obj = Market(
                        simulation = simulation_obj,
                        market_number = market_number,
                        name = name,
                        creation_date_time = timezone.now(),
                        modification_date_time = timezone.now(),
                        created_by = request.user,
                        modified_by = request.user
                    )
                    market_obj.save()

            markets = Market.objects.filter(simulation_id = simulation_id).order_by("name").values("id", "name")
            selected_market = markets.filter(market_number = market_number).first()
            if selected_market is None:
                selected_id = None
            else:
                selected_id = selected_market["id"]

            return JsonResponse({"success": True, "markets": list(markets), "selected_id": selected_id})
        except Exception as e:
            return JsonResponse({"success": False, "error": str(e)})
    return JsonResponse({"success": False, "error": "No file uploaded."})

@csrf_exempt
def process_student_score_file(request):
    if request.method == "POST" and request.FILES.get("file"):
        uploaded_file = request.FILES["file"]
        market_id = request.POST.get("market_id")
        simulation_id = request.POST.get("simulation_id")
        is_team = request.POST.get("is_team")
        filename = ""
        try:
            is_team_options = ["1", "0"]
            if is_team is None:
                raise ValueError (f"Please select is team option")
            elif is_team not in is_team_options:
                raise ValueError (f"invalid team option")

            check_file(uploaded_file)
            academic_year = get_active_academic_year()
            market_obj = Market.objects.filter(simulation_id = simulation_id, simulation__academic_year = academic_year, id = market_id).first()
            if market_obj is None:
                raise ValueError (f"Unable to find Market with id : {market_id}")
            if market_obj.simulation.academic_year != academic_year:
                raise ValueError (f"This market({market_obj.name}) is not for current academic year({academic_year}).")

            filename = uploaded_file.name
            if uploaded_file.name.endswith('.csv'):
                    df = pd.read_csv(uploaded_file)
            elif uploaded_file.name.endswith(('.xls', '.xlsx')):
                df = pd.read_excel(uploaded_file)

            row_count = len(df)
            all_students = Student.objects.filter(academic_year=academic_year).all()
            no_student_found_list = []
            no_team_found_list = []
            duplicate_student_found_list = []
            student_with_other_market_found_list = []
            score_obj_add_list = []
            score_obj_update_list = []
            now = timezone.now()
            user = request.user
            for index, row in df.iterrows():
                player_id = row.get('Player Id')
                subscription_key__simulation_number = row.get('GoVenture Subscription Key | Simulation Number')
                (subscription_key_parsed, simulation_number) = str_to_subscription_key_simulation_number(subscription_key__simulation_number)
                
                temp_student = all_students.filter( subscription_key = subscription_key_parsed).first()
                if temp_student is None:
                    no_student_found_list.append(player_id)
                    continue
                temp_team = None
                temp_team_member = None
                if is_team == "1":
                    temp_team_member = TeamMember.objects.filter(team__simulation_id = simulation_id, student_id = temp_student.id).first()
                    if temp_team_member is None:
                        no_team_found_list.append(player_id)
                        continue
                    temp_team = Team.objects.get(pk = temp_team_member.team_id)
                    if temp_team is None:
                        no_team_found_list.append(player_id)
                        continue
                    
                already_exists = False
                if len(score_obj_add_list) > 0:
                    already_exists = any(obj.go_venture_subscription_key == subscription_key_parsed for obj in score_obj_add_list)
                if already_exists == False and len(score_obj_update_list) > 0:
                    already_exists = any(obj.go_venture_subscription_key == subscription_key_parsed for obj in score_obj_update_list)

                if already_exists:
                    duplicate_student_found_list.append(player_id)
                    continue

                temp_score = StudentScore.objects.filter(student_id = temp_student.id, market_id = market_obj.id).first()
                if temp_score is not None and temp_score.market.id != market_obj.id:
                    student_with_other_market_found_list.append(player_id)
                    continue
                
                company = str_to_str(row.get('Company'))
                first_name = str_to_str(row.get('First Name'))
                last_name = str_to_str(row.get('Last Name'))
                rubric_score = row.get('Rubric Score')
                balanced_score = row.get('Balanced Score')
                participation = row.get('Participation')
                rank_score = row.get('Rank Score')
                hr_score = row.get('HR Score')
                ethics_score = row.get('Ethics Score')
                competency_quiz = row.get('Competency Quiz')
                team_evaluation = row.get('Team Evaluation')
                period_joined = row.get('Period Joined')
                tutorial_quiz = row.get('Tutorial Quiz')

                player_id_parsed = str_to_bigint(player_id)
                rubric_score_parsed = str_to_bigint(str_remove_percentage(rubric_score))
                balanced_score_parsed = str_to_bigint(str_remove_percentage(balanced_score))
                participation_parsed = None
                participation_total = None
                participation_in = None
                if participation is not None:
                    parts = participation.split("%")
                    if len(parts) == 2:
                        participation_parsed = parts[0]
                        participation_info = parts[1]
                        if participation_info is not None:
                            parts = participation_info.replace("(", "").replace(")", "").split("of")
                            if len(parts) == 2:
                                participation_total = str_to_bigint(parts[1])
                                participation_in = str_to_bigint(parts[0])
                
                rank_score_parsed = str_to_bigint(str_remove_percentage(rank_score))
                hr_score_parsed = str_to_bigint(str_remove_percentage(hr_score))
                ethics_score_parsed = str_to_bigint(str_remove_percentage(ethics_score))
                competency_quiz_parsed = str_to_bigint(str_remove_percentage(competency_quiz))
                team_evaluation_parsed = str_to_bigint(str_remove_percentage(team_evaluation))
                period_joined_parsed = str_to_bigint(period_joined)
                tutorial_quiz_parsed = str_to_bigint(str_remove_percentage(tutorial_quiz))

                is_new = True
                if temp_score is not None:
                    is_new = False
                else: 
                    temp_score = StudentScore (
                        student = temp_student,
                        market = market_obj,
                        creation_date_time = now,
                        created_by = user
                    )
                temp_score.team = temp_team
                temp_score.team_member = temp_team_member
                temp_score.player_id = player_id_parsed
                temp_score.company = company
                temp_score.first_name = first_name
                temp_score.last_name = last_name
                temp_score.go_venture_subscription_key = subscription_key_parsed
                temp_score.simulation_number = simulation_number
                temp_score.rubric_score_percentage = rubric_score_parsed
                temp_score.balanced_score_percentage = balanced_score_parsed
                temp_score.participation_percentage = participation_parsed
                temp_score.participation_total = participation_total
                temp_score.participation_in = participation_in
                temp_score.rank_score_percentage = rank_score_parsed
                temp_score.hr_score_percentage = hr_score_parsed
                temp_score.ethics_score_percentage = ethics_score_parsed
                temp_score.competency_quiz_percentage = competency_quiz_parsed
                temp_score.team_evaluation_percentage = team_evaluation_parsed
                temp_score.period_joined = period_joined_parsed
                temp_score.tutorial_quiz_percentage = tutorial_quiz_parsed

                temp_score.modification_date_time = now
                temp_score.modified_by = user
            
                if is_new: 
                    score_obj_add_list.append(temp_score)
                else:
                    score_obj_update_list.append(temp_score)

            if len(score_obj_add_list) > 0:
                StudentScore.objects.bulk_create(score_obj_add_list, batch_size=500)
            if len(score_obj_update_list) > 0:
                StudentScore.objects.bulk_update(score_obj_update_list, ["player_id"
                                                          , "company"
                                                          , "first_name"
                                                          , "last_name"
                                                          , "simulation_number"
                                                          , "rubric_score_percentage"
                                                          , "balanced_score_percentage"
                                                          , "participation_percentage"
                                                          , "participation_total"
                                                          , "participation_in"
                                                          , "rank_score_percentage"
                                                          , "hr_score_percentage"
                                                          , "ethics_score_percentage"
                                                          , "competency_quiz_percentage"
                                                          , "team_evaluation_percentage"
                                                          , "period_joined"
                                                          , "tutorial_quiz_percentage"
                                                          , "modified_by"
                                                          , "modification_date_time"
                                                          ], batch_size=500)

            additional_info = ""
            failed_count = 0
            if len(no_student_found_list) > 0:
                additional_info += f", no student found {len(no_student_found_list)} [{', '.join(map(str,no_student_found_list))}]"
                failed_count += len(no_student_found_list)
            if len(no_team_found_list) > 0:
                additional_info += f", no team found {len(no_team_found_list)} [{', '.join(map(str,no_team_found_list))}]"
                failed_count += len(no_team_found_list)
            if len(duplicate_student_found_list) > 0:
                additional_info += f", duplicate student found {len(duplicate_student_found_list)} [{', '.join(map(str,duplicate_student_found_list))}]"
                failed_count += len(duplicate_student_found_list)
            if len(student_with_other_market_found_list) > 0:
                additional_info += f", duplicate student found {len(student_with_other_market_found_list)} [{', '.join(map(str,student_with_other_market_found_list))}]"
                failed_count += len(student_with_other_market_found_list)
            
            remarks = f"Successfully read {row_count}, add rows {len(score_obj_add_list)}, modify rows {len(score_obj_update_list)} rows{additional_info}. \nFrom file {filename}"
            save_file_export_log(filename, remarks, row_count, len(score_obj_add_list), len(score_obj_update_list), len(no_student_found_list), len(duplicate_student_found_list), request.user)
            
            return JsonResponse({
                "success": True,
                "message": remarks
            })
        except Exception as e:
            return JsonResponse({"success": False, "error": f"Error reading sheet: {e}"})
    return JsonResponse({"success": False, "error": "Missing file or sheet name."})    

@login_required(login_url='login')
def student_score_report(request):
    template_name = 'main/student_score_report.html'
    error_message = ""
    rows = []
    total_rows = 0
    page_obj = None
    simulation_list = None
    filters = {}
    campus_list = None
    market_list = None
    try:
        academic_year = get_active_academic_year()
        per_page = request.GET.get("per_page", settings.PER_PAGE)
        simulation_ids = [int(i) for i in request.GET.getlist("simulation_ids", []) if i.isdigit()]
        market_ids = [int(i) for i in request.GET.getlist("market_ids", []) if i.isdigit()]
        filters = get_filter(request, academic_year)
        simulation_list = Simulation.objects.filter(academic_year=academic_year).all()
        campus_list = get_all_campus(academic_year)
        if simulation_ids and len(simulation_ids) > 0:
            market_list = Market.objects.filter(simulation_id__in=simulation_ids).all()
        elif market_ids:
            market_list = Market.objects.filter(simulation__academic_year=academic_year).all()

        rows = get_student_score_report(filters, academic_year)
        paginator = Paginator(rows, per_page)
        page_number = request.GET.get('page')
        page_obj = paginator.get_page(page_number)
        total_rows = paginator.count
    except Exception as e:
        error_message = e
    return render(request, template_name, {"page_obj": page_obj, "filters": filters
                                           , "total_rows": total_rows, "simulation_list": simulation_list, "market_list": market_list
                                           , "error_message": error_message, "campus_list" : campus_list, "academic_year": academic_year})

@csrf_exempt
def get_markets_list(request):
    is_success = False
    error_message = ""
    market_obj = []
    if request.method == "POST":
        academic_year = get_active_academic_year()
        try:
            print(request.POST.getlist("simulation_ids", []))
            simulation_ids = [int(i) for i in request.POST.getlist("simulation_ids", []) if i.isdigit()]
            if len(simulation_ids) > 0:
                market_obj = Market.objects.filter(simulation_id__in = simulation_ids, simulation__academic_year=academic_year).all()
            else:
                market_obj = Market.objects.filter(simulation__academic_year=academic_year).all()
            market_obj = list(market_obj.values("id", "name"))
            is_success = True
        except Exception as e:
            error_message = str(e)
    return JsonResponse({"success": is_success, "error": error_message, "markets": list(market_obj)})

def get_filter(request, academic_year):
    filters = {
            "report_type": request.GET.get("report_type", 1),
            "student_name": request.GET.get("student_name", "").strip(),
            "gender": request.GET.get("gender", ""), 
            "campus": request.GET.get("campus", ""), 
            "simulation_ids":  request.GET.getlist("simulation_ids", None),
            "simulation_id": request.GET.get("simulation_id", None),
            "market_id": request.GET.get("market_id", None),
            "market_ids": request.GET.getlist("market_ids", None),
            "age_from": request.GET.get("age_from", None),
            "age_to": request.GET.get("age_to", None),
            "per_page": request.GET.get("per_page", settings.PER_PAGE),
            "academic_year": academic_year
        }
    return filters

def get_true_false(value):
    return 1 if value == True else 0

@login_required(login_url='login')
def student_score_report_xlx(request):
    # Get your filtered data
    rows = []
    academic_year = get_active_academic_year()
    filters = get_filter(request, academic_year)
    rows = get_student_score_report(filters)

    # Create workbook
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = f"Students_score_report"
    file_name = f"Students_score_report__{academic_year}_{timezone.now().strftime("%Y-%m-%d-%H-%M-%S")}"
    # Add header
    ws.append(["ID", "academic_year", "Studienr", "TeamID", "is_3pt", "is_mmf", "is_fix_alloc", "role", "Name", "Age", "Gender", "EmailAddress", "Campus", "SubscriptionKey", "Player Id", "Company"
               , "GoVenture Subscription Key | Simulation Number", "Rubric Score", "Balanced Score", "Participation Score"
               , "Participation Score Info", "Rank Score", "HR Score", "Ethics Score", "Competency Quiz", "Team Evaluation"
               , "Period joined", "Tutorial Quiz"])

    # Add data
    for row in rows:
        #ws.append(row)
        ws.append([row["id"], row["academic_year"], row["studienr"], row["teamID"], get_true_false(row["is_3pt"]), get_true_false(row["is_mmf"]), get_true_false(row["is_fix_alloc"])
                   , row["role"], row["name"], row["age"], row["gender"], row["email_address"], row["campus"], row["subscription_key"], row["player_id"], 
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


@login_required(login_url='login')
def student_score_report_with_survey_xlx(request):
    # Get your filtered data
    rows = []
    academic_year = get_active_academic_year()
    filters = get_filter(request, academic_year)
    rows = get_student_score_report(filters, True)

    # Create workbook
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = f"Score_report_with_survey"
    file_name = f"Score_report__{academic_year}_with_survey_{timezone.now().strftime("%Y-%m-%d-%H-%M-%S")}"
    # Add header
    ws.append(["ID", "academic_year","Studienr", "TeamID", "is_3pt", "is_mmf", "is_fix_alloc", "role", "Name", "Age", "Gender", "EmailAddress", "Campus", "SubscriptionKey", "Player Id", "Company"
               , "GoVenture Subscription Key | Simulation Number", "Rubric Score", "Balanced Score", "Participation Score"
               , "Participation Score Info", "Rank Score", "HR Score", "Ethics Score", "Competency Quiz", "Team Evaluation"
               , "Period joined", "Tutorial Quiz", "sim2_complete", "indiv_time_spent", "indiv_time_spent_t", "joint_time_spent", "joint_time_spent_t", "days_in_person", "days_in_person_t", "responsib_clear", "responsib_clear_t"
               , "responsib_own", "responsib_own_t", "responsib_change", "responsib_change_t", "areas_change_1", "areas_change_2", "areas_change_3"
               , "areas_change_4", "areas_change_indiv"
               , "areas_change_team", "responsib_outside", "responsib_outside_t", "ta_a", "ta_b", "ta_c", "ta_indiv", "ta_team", "la_a", "la_b", "la_c", "la_indiv", "la_team"
               , "tms_s1", "tms_s2", "tms_s3", "tms_s4", "tms_s5", "tms_spec_indiv", "tms_spec_team", "tms_cred1", "tms_cred2", "tms_cred3", "tms_cred4", "tms_cred5", "tms_cred_indiv"
               , "tms_cred_team", "tms_co1", "tms_co2", "tms_co3", "tms_co4", "tms_co5", "tms_coord_indiv", "tms_coord_team", "att_market_sales", "att_production", "att_randd"
               , "focus_shift_1", "focus_shift_2", "focus_shift_3", "focus_shift_4", "focus_shift_indiv", "focus_shift_team", "compet_import1", "compet_import2", "compet_import3"
               , "compet_import_indiv", "pcs_1", "pcs_2", "pcs_3", "pcs_indiv", "pcs_team", "statoverall_1", "statoverall_2", "statoverall_3", "statoverall_4", "statoverall_5"
               , "team_size", "team_size_found", "comments", "subscrip_key", "mail_confirm", "email", "match_value", "match_by_field"
               , "row_number"])

    # Add data
    for row in rows:
        #ws.append(row)
        ws.append([row["id"], row["academic_year"], row["studienr"], row["teamID"], get_true_false(row["is_3pt"]), get_true_false(row["is_mmf"]), get_true_false(row["is_fix_alloc"])
                   , row["role"], row["name"], row["age"], row["gender"], row["email_address"], row["campus"], row["subscription_key"], row["player_id"], 
                   row["company"], f"{row["go_venture_subscription_key"]} | #{row["go_venture_simulation_number"]}", row["rubric_score_percentage"], 
                   row["balanced_score_percentage"], row["participation_percentage"], f"({row["participation_in"]} of {row["participation_total"]})"
                   , row["rank_score_percentage"], row["hr_score_percentage"], row["ethics_score_percentage"], row["competency_quiz_percentage"], 
                   row["team_evaluation_percentage"], row["period_joined"], row["tutorial_quiz_percentage"], row["sim2_complete"]
                   , row["indiv_time_spent"], row["indiv_time_spent_t"], row["joint_time_spent"], row["joint_time_spent_t"], row["days_in_person"], row["days_in_person_t"], row["responsib_clear"], row["responsib_clear_t"]
                   , row["responsib_own"], row["responsib_own_t"], row["responsib_change"], row["responsib_change_t"], row["areas_change_1"], row["areas_change_2"], row["areas_change_3"]
               , row["areas_change_4"], row["areas_change_indiv"], row["areas_change_team"], row["responsib_outside"], row["responsib_outside_t"]
               , row["ta_a"], row["ta_b"], row["ta_c"], row["ta_indiv"], row["ta_team"], row["la_a"], row["la_b"], row["la_c"], row["la_indiv"], row["la_team"]
               , row["tms_s1"], row["tms_s2"], row["tms_s3"], row["tms_s4"], row["tms_s5"], row["tms_spec_indiv"], row["tms_spec_team"], row["tms_cred1"], row["tms_cred2"]
               , row["tms_cred3"], row["tms_cred4"], row["tms_cred5"], row["tms_cred_indiv"], row["tms_cred_team"], row["tms_co1"], row["tms_co2"]
               , row["tms_co3"], row["tms_co4"], row["tms_co5"], row["tms_coord_indiv"], row["tms_coord_team"], row["att_market_sales"], row["att_production"], row["att_randd"]
               , row["focus_shift_1"], row["focus_shift_2"], row["focus_shift_3"], row["focus_shift_4"], row["focus_shift_indiv"], row["focus_shift_team"], row["compet_import1"]
               , row["compet_import2"], row["compet_import3"], row["compet_import_indiv"], row["pcs_1"], row["pcs_2"], row["pcs_3"], row["pcs_indiv"], row["pcs_team"]
               , row["statoverall_1"], row["statoverall_2"], row["statoverall_3"], row["statoverall_4"], row["statoverall_5"]
               , row["team_size"], row["team_size_found"], row["comments"], row["subscrip_key"], row["mail_confirm"], row["email"], row["match_value"], row["match_by_field"]
               , row["row_number"]])

    # Prepare response
    response = HttpResponse(
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
    response["Content-Disposition"] = f'attachment; filename="{file_name}.xlsx"'

    wb.save(response)
    return response
