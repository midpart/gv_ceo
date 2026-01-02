from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from .forms import UploadFileForm, MarketForm
from .query import get_student_score_report, get_all_campus
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
    try:
        per_page = request.GET.get("per_page", settings.PER_PAGE)
        
        rows = get_all_data()
        paginator = Paginator(rows, per_page)
        page_number = request.GET.get('page')
        page_obj = paginator.get_page(page_number)
        total_rows = paginator.count
    except Exception as e:
        error_message = e
    return render(request, template_name, {"page_obj": page_obj, "total_rows": total_rows, "error_message": error_message})

def get_all_data():
    all_data = []
    simulation_list = Simulation.objects.all()
    student_list = Student.objects.all()
    score_list = StudentScore.objects.all()
    team_list = Team.objects.all()
    team_member_lsit = TeamMember.objects.all()
    market_list = Market.objects.all()
    sim2_all = Simulation2Survey.objects.all()
    sim3_all = Simulation3Survey.objects.all()

    score_lookup = {(s.student_id, s.market.simulation_id): s for s in score_list }
    market_lookup = {(s.id): s for s in market_list }
    team_lookup = {(s.id): s for s in team_list }
    team_member_lookup = {(s.student_id, s.team_id): s for s in team_member_lsit }
    sim2_lookup = {(s.student_id, s.simulation_id): s for s in sim2_all }
    sim3_lookup = {(s.student_id, s.simulation_id): s for s in sim3_all }

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
            )
            temp_score = score_lookup.get((stu.id, sim.id))
            if temp_score is not None:
                temp_market = market_lookup.get(temp_score.market_id)
                temp_team = None
                temp_team_member = None
                temp_sim2 = sim2_lookup.get((stu.id, sim.id))
                temp_sim3 = sim3_lookup.get((stu.id, sim.id))
                if temp_score.team is not None:
                    temp_team = team_lookup.get(temp_score.team_id)
                    temp_team_member = team_member_lookup.get((stu.id, temp_score.team_id))

                temp_dto.simulation_name = sim.name
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
    rows = get_all_data()

    # Create workbook
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = f"All_data"
    file_name = f"Students_All_data_report{timezone.now().strftime("%Y-%m-%d-%H-%M-%S")}"
    # Add header
    ws.append(["Studienr", "name", "email", "campus", "subscription_key", "age", "gender", "sim", "market", "market_number"])

    # Add data
    for row in rows:
        #ws.append(row)
        ws.append([row.studienr, row.student_name, row.email_address, row.campus, row.subscription_key, row.age_in_year, row.gender
                  , row.simulation_name, row.market_name, row.market_number])

    # Prepare response
    response = HttpResponse(
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
    response["Content-Disposition"] = f'attachment; filename="{file_name}.xlsx"'

    wb.save(response)
    return response