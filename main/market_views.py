from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from .forms import UploadFileForm, MarketForm
from .query import get_student_score_report, get_all_campus
from .common import *
import pandas as pd
from django import forms
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from .models import Student, Market, Simulation, StudentScore, ImportFileLog
from django.utils import timezone
from django.core.paginator import Paginator
from django.conf import settings
import re
import openpyxl
from django.http import HttpResponse

# Create your views here.
@login_required(login_url='login')
def manage_market(request):
    template_name = 'main/manage_market.html'
    simulations = Market.objects.all().order_by('modification_date_time')
    paginator = Paginator(simulations, settings.PER_PAGE)

    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, template_name, {'page_obj': page_obj})

@login_required(login_url='login')
def market_form(request, pk=None):
    template_name = 'main/market_form.html'
    if pk:
        obj = get_object_or_404(Market, pk=pk)
    else:
        obj = None

    if request.method == "POST":
        form = MarketForm(request.POST, instance=obj)
        if form.is_valid():
            market = form.save(commit=False)
            if not market.pk:
                market.created_by = request.user
            
            market.modified_by = request.user
            market.modification_date_time = timezone.now()
            market.save()
            return redirect('manageMarkets')  # redirect to list page
    else:
        form = MarketForm(instance=obj)

    return render(request, template_name, {'form': form, 'obj': obj})

@login_required(login_url='login')
def delete_market(request, pk):
    is_success = False
    message = ""
    if request.method == 'POST' and request.headers.get('x-requested-with') == 'XMLHttpRequest':
        try:
            obj = get_object_or_404(Market, pk=pk)
            obj.delete()
            is_success = True
            message = "Delete operation is successful."
        except Exception as e:
            message = str(e)
    else:
        message = "Invalid request"
    return JsonResponse({'success': is_success, 'message': message})

@csrf_exempt
def get_markets(request):
    if request.method == "POST" and request.FILES.get("file"):
        uploaded_file = request.FILES["file"]
        try:
            check_file(uploaded_file)
            file_name = uploaded_file.name
            simulation_id = request.POST.get('simulation_id')
            simulation_obj = get_object_or_404(Simulation, pk=simulation_id)
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
