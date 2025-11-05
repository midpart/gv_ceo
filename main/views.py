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

@login_required(login_url='login')
def index(request):
    return render(request, 'main/index.html')
