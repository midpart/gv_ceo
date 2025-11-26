from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from . forms import UploadFileForm, MarketForm
from . query import get_student_score_report, get_all_campus
from .common import *
import pandas as pd
from django import forms
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from . models import Student, Market, Simulation, Team, StudentScore, ImportFileLog
from django.utils import timezone
from django.core.paginator import Paginator
from django.conf import settings
import re
import openpyxl
from django.http import HttpResponse

# Create your views here.

@login_required(login_url='login')
def index(request):
    total_student = 0
    total_simulation = 0
    total_market = 0
    total_team = 0
    error_message = ''
    try:
        total_student = Student.objects.count()
        total_simulation = Simulation.objects.count()
        total_market = Market.objects.count()
        total_team = Team.objects.count()
    except Exception as e:
        error_message = str(e)
    return render(request, 'main/index.html', {"total_student": total_student,"total_simulation": total_simulation,"total_market": total_market
                                               ,"total_team": total_team, "error_message": error_message})
