from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from .forms import UploadFileForm, MarketForm
from .query import get_student_score_report, get_all_campus, get_all_student_simnulation_Count
from .common import *
import pandas as pd
from django import forms
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from .models import Student, Market, Simulation, StudentScore, Team, TeamMember, Simulation2Survey, Simulation3Survey
from django.utils import timezone
from django.core.paginator import Paginator
from django.conf import settings
import re
import openpyxl
from django.http import HttpResponse
from .dto import AllData

@login_required(login_url='login')
def student_all_report(request):
    template_name = 'main/student_all_report.html'
    error_message = ""
    rows = []
    total_rows = 0
    page_obj = None
    academic_year = 0
    try:
        academic_year = get_active_academic_year()
        per_page = request.GET.get("per_page", settings.PER_PAGE)
        
        rows = get_all_data()
        paginator = Paginator(rows, per_page)
        page_number = request.GET.get('page')
        page_obj = paginator.get_page(page_number)
        total_rows = paginator.count
    except Exception as e:
        error_message = e
    return render(request, template_name, {"page_obj": page_obj, "total_rows": total_rows, "error_message": error_message, "academic_year": academic_year})

def get_all_data():
    all_data = []
    academic_year = get_active_academic_year()
    simulation_list = Simulation.objects.filter(academic_year=academic_year).all()
    student_list = Student.objects.filter(academic_year=academic_year).all()
    score_list = StudentScore.objects.filter(market__simulation__academic_year=academic_year).all()
    team_list = Team.objects.filter(simulation__academic_year=academic_year).all()
    team_member_lsit = TeamMember.objects.filter(team__simulation__academic_year=academic_year).all()
    market_list = Market.objects.filter(simulation__academic_year=academic_year).all()
    sim2_all = Simulation2Survey.objects.filter(simulation__academic_year=academic_year).all()
    sim3_all = Simulation3Survey.objects.filter(simulation__academic_year=academic_year).all()
    simulation_ids = [sim.id for sim in simulation_list]
    student_sim_counts = []
    if len(simulation_ids) > 0:
       student_sim_counts=  get_all_student_simnulation_Count(simulation_ids)

    score_lookup = {(s.student_id, s.market.simulation_id): s for s in score_list }
    market_lookup = {(s.id): s for s in market_list }
    team_lookup = {(s.id): s for s in team_list }
    team_member_lookup = {(s.student_id, s.team_id): s for s in team_member_lsit }
    sim2_lookup = {(s.student_id, s.simulation_id): s for s in sim2_all }
    sim3_lookup = {(s.student_id, s.simulation_id): s for s in sim3_all }
    all_sim_lookup = {(s["student_id"]): s for s in student_sim_counts }

    for stu in student_list:
        for sim in simulation_list:
            temp_dto = AllData(
                studienr = stu.studienr,
                student_name = stu.name,
                email_address = stu.email_address,
                campus = stu.campus,
                subscription_key = stu.subscription_key,
                age_in_year = stu.age_in_year,
                gender = stu.gender,
                academic_year=stu.academic_year,
                simulation_name = sim.name,
                sim_number= sim.number,
            )
            temp_score = score_lookup.get((stu.id, sim.id))
            all_sim_data = all_sim_lookup.get((stu.id))
            temp_sim2 = sim2_lookup.get((stu.id, sim.id))
            temp_sim3 = sim3_lookup.get((stu.id, sim.id))

            temp_dto.cpl_data = False
            if all_sim_data is not None and all_sim_data["total_sim_count"] == len(simulation_ids):
                temp_dto.cpl_data = True
            if temp_score is not None:
                temp_market = market_lookup.get(temp_score.market_id)
                temp_team = None
                temp_team_member = None
                if temp_score.team is not None:
                    temp_team = team_lookup.get(temp_score.team_id)
                    temp_team_member = team_member_lookup.get((stu.id, temp_score.team_id))

                temp_dto.market_name = temp_market.name
                temp_dto.market_number = temp_market.market_number

                if temp_team is not None:
                    temp_dto.team_name = temp_team.name
                    temp_dto.teamID = temp_team.teamID
                    temp_dto.is_mmf = temp_team.is_mmf
                    temp_dto.is_3pt = temp_team.is_3pt
                    temp_dto.is_fix_alloc = temp_team.is_fix_alloc
                    temp_dto.role = temp_team_member.role
                    temp_dto.teammember_order = temp_team_member.teammember_order
                temp_dto.player_id = temp_score.player_id
                temp_dto.company = temp_score.company
                temp_dto.rubric_score_percentage = temp_score.rubric_score_percentage
                temp_dto.balanced_score_percentage = temp_score.balanced_score_percentage
                temp_dto.participation_percentage = temp_score.participation_percentage
                temp_dto.participation_total = temp_score.participation_total
                temp_dto.participation_in = temp_score.participation_in
                temp_dto.rank_score_percentage = temp_score.rank_score_percentage
                temp_dto.hr_score_percentage = temp_score.hr_score_percentage
                temp_dto.ethics_score_percentage = temp_score.ethics_score_percentage
                temp_dto.competency_quiz_percentage = temp_score.competency_quiz_percentage
                temp_dto.team_evaluation_percentage = temp_score.team_evaluation_percentage
                temp_dto.period_joined = temp_score.period_joined
                temp_dto.tutorial_quiz_percentage = temp_score.tutorial_quiz_percentage

            if temp_sim2 is not None:
                temp_dto.indiv_time_spent = temp_sim2.indiv_time_spent
                temp_dto.indiv_time_spent_t = temp_sim2.indiv_time_spent_t
                temp_dto.joint_time_spent = temp_sim2.joint_time_spent
                temp_dto.joint_time_spent_t = temp_sim2.joint_time_spent_t
                temp_dto.days_in_person = temp_sim2.days_in_person
                temp_dto.days_in_person_t = temp_sim2.days_in_person_t
                temp_dto.responsib_clear = temp_sim2.responsib_clear
                temp_dto.responsib_clear_t = temp_sim2.responsib_clear_t
                temp_dto.responsib_own = temp_sim2.responsib_own
                temp_dto.responsib_own_t = temp_sim2.responsib_own_t
                temp_dto.responsib_change = temp_sim2.responsib_change
                temp_dto.responsib_change_t = temp_sim2.responsib_change_t
                temp_dto.areas_change_1 = temp_sim2.areas_change_1
                temp_dto.areas_change_2 = temp_sim2.areas_change_2
                temp_dto.areas_change_3 = temp_sim2.areas_change_3
                temp_dto.areas_change_4 = temp_sim2.areas_change_4
                temp_dto.areas_change_indiv = temp_sim2.areas_change_indiv
                temp_dto.areas_change_team = temp_sim2.areas_change_team
                temp_dto.responsib_outside = temp_sim2.responsib_outside
                temp_dto.responsib_outside_t = temp_sim2.responsib_outside_t
                temp_dto.ta_a = temp_sim2.ta_a
                temp_dto.ta_b = temp_sim2.ta_b
                temp_dto.ta_c = temp_sim2.ta_c
                temp_dto.ta_indiv = temp_sim2.ta_indiv
                temp_dto.ta_team = temp_sim2.ta_team
                temp_dto.la_a = temp_sim2.la_a
                temp_dto.la_b = temp_sim2.la_b
                temp_dto.la_c = temp_sim2.la_c
                temp_dto.la_indiv = temp_sim2.la_indiv
                temp_dto.la_team = temp_sim2.la_team
                temp_dto.tms_s1 = temp_sim2.tms_s1
                temp_dto.tms_s2 = temp_sim2.tms_s2
                temp_dto.tms_s3 = temp_sim2.tms_s3
                temp_dto.tms_s4 = temp_sim2.tms_s4
                temp_dto.tms_s5 = temp_sim2.tms_s5
                temp_dto.tms_spec_indiv = temp_sim2.tms_spec_indiv
                temp_dto.tms_spec_team = temp_sim2.tms_spec_team
                temp_dto.tms_cred1 = temp_sim2.tms_cred1
                temp_dto.tms_cred2 = temp_sim2.tms_cred2
                temp_dto.tms_cred3 = temp_sim2.tms_cred3
                temp_dto.tms_cred4 = temp_sim2.tms_cred4
                temp_dto.tms_cred5 = temp_sim2.tms_cred5
                temp_dto.tms_cred_indiv = temp_sim2.tms_cred_indiv
                temp_dto.tms_cred_team = temp_sim2.tms_cred_team
                temp_dto.tms_co1 = temp_sim2.tms_co1
                temp_dto.tms_co2 = temp_sim2.tms_co2
                temp_dto.tms_co3 = temp_sim2.tms_co3
                temp_dto.tms_co4 = temp_sim2.tms_co4
                temp_dto.tms_co5 = temp_sim2.tms_co5
                temp_dto.tms_coord_indiv = temp_sim2.tms_coord_indiv
                temp_dto.tms_coord_team = temp_sim2.tms_coord_team
                temp_dto.att_market_sales = temp_sim2.att_market_sales
                temp_dto.att_production = temp_sim2.att_production
                temp_dto.att_randd = temp_sim2.att_randd
                temp_dto.focus_shift_1 = temp_sim2.focus_shift_1
                temp_dto.focus_shift_2 = temp_sim2.focus_shift_2
                temp_dto.focus_shift_3 = temp_sim2.focus_shift_3
                temp_dto.focus_shift_4 = temp_sim2.focus_shift_4
                temp_dto.focus_shift_indiv = temp_sim2.focus_shift_indiv
                temp_dto.focus_shift_team = temp_sim2.focus_shift_team
                temp_dto.compet_import1 = temp_sim2.compet_import1
                temp_dto.compet_import2 = temp_sim2.compet_import2
                temp_dto.compet_import3 = temp_sim2.compet_import3
                temp_dto.compet_import_indiv = temp_sim2.compet_import_indiv
                temp_dto.compet_import_team = temp_sim2.compet_import_team
                temp_dto.pcs_1 = temp_sim2.pcs_1
                temp_dto.pcs_2 = temp_sim2.pcs_2
                temp_dto.pcs_3 = temp_sim2.pcs_3
                temp_dto.pcs_indiv = temp_sim2.pcs_indiv
                temp_dto.pcs_team = temp_sim2.pcs_team
                temp_dto.statoverall_1 = temp_sim2.statoverall_1
                temp_dto.statoverall_2 = temp_sim2.statoverall_2
                temp_dto.statoverall_3 = temp_sim2.statoverall_3
                temp_dto.statoverall_4 = temp_sim2.statoverall_4
                temp_dto.statoverall_5 = temp_sim2.statoverall_5
                temp_dto.team_size = temp_sim2.team_size
                temp_dto.team_size_found = temp_sim2.team_size_found
                temp_dto.comments = temp_sim2.comments

            if temp_sim3 is not None:
                temp_dto.sim3_day1 = temp_sim3.sim3_day1
                temp_dto.sim3_day2 = temp_sim3.sim3_day2
                temp_dto.sim3_day3 = temp_sim3.sim3_day3
                temp_dto.sim3_day4 = temp_sim3.sim3_day4
                temp_dto.sim3_day5 = temp_sim3.sim3_day5
                temp_dto.sim3_statoverall_1 = temp_sim3.statoverall_1
                temp_dto.sim3_statoverall_2 = temp_sim3.statoverall_2
                temp_dto.sim3_statoverall_3 = temp_sim3.statoverall_3
                temp_dto.sim3_statoverall_4 = temp_sim3.statoverall_4
                temp_dto.sim3_statoverall_5 = temp_sim3.statoverall_5

            all_data.append(temp_dto)

    return all_data

@login_required(login_url='login')
def student_all_report_xlx(request):
    # Get your filtered data
    academic_year = get_active_academic_year()
    rows = get_all_data()

    # Create workbook
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = f"All_data"
    file_name = f"Students_All_data_report__{academic_year}__{timezone.now().strftime("%Y-%m-%d-%H-%M-%S")}"
    # Add header
    ws.append(["Studienr", "name", "email", "campus", "subscription_key", "age", "gender", "academic_year", "cpl_data", "sim", "sim_number", "market", "market_number"
               , "team_name", "teamID", "is_mmf", "is_3pt", "is_fix_alloc", "role", "teammember_order"
               
               , "player_id", "company", "rubric_score", "balanced_score", "participation", "participation_total", "participation_in", "rank_score", "hr_score"
               , "ethics_score", "competency_quiz", "team_evaluation", "period_joined", "tutorial_quiz"

               , "indiv_time_spent", "indiv_time_spent_t", "joint_time_spent", "joint_time_spent_t", "days_in_person", "days_in_person_t", "responsib_clear"
               , "responsib_clear_t", "responsib_own", "responsib_own_t", "responsib_change", "responsib_change_t", "areas_change_1", "areas_change_2"
               , "areas_change_3", "areas_change_4", "areas_change_indiv", "areas_change_team", "responsib_outside", "responsib_outside_t", "ta_a", "ta_b"
               , "ta_c", "ta_indiv", "ta_team", "la_a", "la_b", "la_c", "la_indiv", "la_team", "tms_s1", "tms_s2", "tms_s3", "tms_s4", "tms_s5", "tms_spec_indiv"
               , "tms_spec_team", "tms_cred1", "tms_cred2", "tms_cred3", "tms_cred4", "tms_cred5", "tms_cred_indiv", "tms_cred_team", "tms_co1", "tms_co2", "tms_co3"
               , "tms_co4", "tms_co5", "tms_coord_indiv", "tms_coord_team", "att_market_sales", "att_production", "att_randd", "focus_shift_1", "focus_shift_2"
               , "focus_shift_3", "focus_shift_4", "focus_shift_indiv", "focus_shift_team", "compet_import1", "compet_import2", "compet_import3", "compet_import_indiv"
               , "compet_import_team", "pcs_1", "pcs_2", "pcs_3", "pcs_indiv", "pcs_team", "statoverall_1", "statoverall_2", "statoverall_3", "statoverall_4"
               , "statoverall_5", "team_size", "team_size_found", "comments"

               , "sim3_day1", "sim3_day2", "sim3_day3", "sim3_day4", "sim3_day5", "sim3_statoverall_1", "sim3_statoverall_2", "sim3_statoverall_3", "sim3_statoverall_4"
               , "sim3_statoverall_5"
               ])

    # Add data
    for row in rows:
        #ws.append(row)
        ws.append([row.studienr, row.student_name, row.email_address, row.campus, row.subscription_key, row.age_in_year, row.gender, row.academic_year, get_true_false(row.cpl_data)
                  , row.simulation_name, row.sim_number, row.market_name, row.market_number
                  , row.team_name, row.teamID, get_true_false(row.is_mmf), get_true_false(row.is_3pt), get_true_false(row.is_fix_alloc), row.role, row.teammember_order
                  
                  , row.player_id, row.company, row.rubric_score_percentage, row.balanced_score_percentage, row.participation_percentage, row.participation_total
                  , row.participation_in, row.rank_score_percentage, row.hr_score_percentage, row.ethics_score_percentage, row.competency_quiz_percentage
                  , row.team_evaluation_percentage, row.period_joined, row.tutorial_quiz_percentage

                  , row.indiv_time_spent, row.indiv_time_spent_t, row.joint_time_spent, row.joint_time_spent_t, row.days_in_person, row.days_in_person_t
                  , row.responsib_clear, row.responsib_clear_t, row.responsib_own, row.responsib_own_t, row.responsib_change, row.responsib_change_t, row.areas_change_1
                  , row.areas_change_2, row.areas_change_3, row.areas_change_4, row.areas_change_indiv, row.areas_change_team, row.responsib_outside, row.responsib_outside_t
                  , row.ta_a, row.ta_b, row.ta_c, row.ta_indiv, row.ta_team, row.la_a, row.la_b, row.la_c, row.la_indiv, row.la_team, row.tms_s1, row.tms_s2, row.tms_s3
                  , row.tms_s4, row.tms_s5, row.tms_spec_indiv, row.tms_spec_team, row.tms_cred1, row.tms_cred2, row.tms_cred3, row.tms_cred4, row.tms_cred5, row.tms_cred_indiv
                  , row.tms_cred_team, row.tms_co1, row.tms_co2, row.tms_co3, row.tms_co4, row.tms_co5, row.tms_coord_indiv, row.tms_coord_team, row.att_market_sales
                  , row.att_production, row.att_randd, row.focus_shift_1, row.focus_shift_2, row.focus_shift_3, row.focus_shift_4, row.focus_shift_indiv, row.focus_shift_team
                  , row.compet_import1, row.compet_import2, row.compet_import3, row.compet_import_indiv, row.compet_import_team, row.pcs_1, row.pcs_2, row.pcs_3, row.pcs_indiv
                  , row.pcs_team, row.statoverall_1, row.statoverall_2, row.statoverall_3, row.statoverall_4, row.statoverall_5, row.team_size, row.team_size_found, row.comments

                  , row.sim3_day1, row.sim3_day2, row.sim3_day3, row.sim3_day4, row.sim3_day5, row.sim3_statoverall_1, row.sim3_statoverall_2, row.sim3_statoverall_3
                  , row.sim3_statoverall_4, row.sim3_statoverall_5
                  ])

    # Prepare response
    response = HttpResponse(
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
    response["Content-Disposition"] = f'attachment; filename="{file_name}.xlsx"'

    wb.save(response)
    return response

def get_true_false(value):
    if value is None: 
        return None
    return 1 if value == True else 0