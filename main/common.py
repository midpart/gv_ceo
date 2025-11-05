from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from . forms import UploadFileForm, MarketForm
from . query import get_student_score_report, get_all_campus
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

def str_to_bigint(value):
    try:
        return int(value)
    except (ValueError, TypeError):
        return None

def str_to_subscription_key_simulation_number(value):
    try:
       if value is not None:
           parts = value.split("|")
           if len(parts) == 2:
               part1 = parts[0].strip()
               part2 = parts[1].replace("#", "").strip()
               return (part1, part2)
        
       return (None, None)
    except (ValueError, TypeError):
        return (None, None)
    
def str_to_str(value):
    try:
        if value is not None:
            return value.strip()
        return value
    except (ValueError, TypeError):
        return None

def str_remove_percentage(value):
    try:
        if value is not None:
            return value.replace("%", "").strip()
        return None
    except Exception as e:
        return None

def check_file(file):
    allwoed_extention = ('.csv', '.xls', '.xlsx')
    if file is None:
        raise ValueError("There is no file to operate.")
    elif file.name.endswith(allwoed_extention) == False: 
        raise ValueError(f"Invalid file, it only support {(", ".join(allwoed_extention))}.")

def parse_file_name(filename):
    name_array = []
    if filename is not None and len(filename)> 0:
        name_without_ext = filename.rsplit('.', 1)[0]
        match = re.search(r"Rubric_(\d+)\s+(.*)", name_without_ext)
        if match:
            rubric_id = match.group(1) 
            simulation_name = match.group(2)
            name_array.append(rubric_id)
            name_array.append(simulation_name)
        else:
            print("Pattern not found")
    return name_array

def save_file_export_log(filename, remarks, total_row, total_insert, total_update, 
                         total_not_found, total_duplicate_found, user):
   temp_ob = ImportFileLog(
       name = filename,
       remarks = remarks,
       total_row = total_row,
       total_insert = total_insert,
       total_update = total_update,
       total_not_found = total_not_found,
       total_duplicate_found = total_duplicate_found,
       creation_date_time = timezone.now(),
       modification_date_time = timezone.now(),
       created_by = user,
       modified_by = user,
   )
   temp_ob.save()