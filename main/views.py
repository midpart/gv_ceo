from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from . forms import UploadFileForm, MarketForm
from . query import get_student_score_report, get_all_campus
import pandas as pd
from django import forms
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from . models import Student, Market, Simulation, StudentScore
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

@csrf_exempt
def get_sheet_names(request):
    if request.method == "POST" and request.FILES.get("file"):
        excel_file = request.FILES["file"]
        try:
            check_file(excel_file)
            xls = pd.ExcelFile(excel_file)
            return JsonResponse({"success": True, "sheet_names": xls.sheet_names})
        except Exception as e:
            return JsonResponse({"success": False, "error": str(e)})
    return JsonResponse({"success": False, "error": "No file uploaded."})

def check_file(file):
    allwoed_extention = ('.csv', '.xls', '.xlsx')
    if file is None:
        raise ValueError("There is no file to operate.")
    elif file.name.endswith(allwoed_extention) == False: 
        raise ValueError(f"Invalid file, it only support {(", ".join(allwoed_extention))}.")

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

@csrf_exempt
def process_sheet(request):
    if request.method == "POST" and request.FILES.get("file"):
        excel_file = request.FILES["file"]
        sheet_name = request.POST.get("sheet_name")
        try:
            check_file(excel_file)
            df = pd.read_excel(excel_file, sheet_name=sheet_name)
            
            all_db_data = Student.objects.all()
            add_data = []
            update_data = []

            for index, row in df.iterrows():
                studienr = row.get('Studienr')
                name = str_to_str(row.get('Name'))
                emailAdress = str_to_str(row.get('EmailAdress'))
                campus = str_to_str(row.get('Campus'))
                subscriptionKey = row.get('SubscriptionKey')
                marketMemberNum = row.get('MarketMemberNum')
                simulationNumber = row.get('SimulationNumber')
                age = row.get('Age')
                gender = str_to_str(row.get('Gender'))
                
                temp_student = None
                temp_student = next((s for s in all_db_data if s.subscription_key == subscriptionKey), None)
                is_new = False
                if temp_student is None:
                    is_new = True
                    temp_student = Student(
                        subscription_key = subscriptionKey,
                        created_by = request.user,
                        creation_date_time = timezone.now()
                    )

                temp_student.studienr = str_to_bigint(studienr)
                temp_student.name = name
                temp_student.email_address = emailAdress
                temp_student.campus = campus
                temp_student.market_member_num = str_to_bigint(marketMemberNum)
                temp_student.simulation_number = str_to_bigint(simulationNumber)
                temp_student.age_in_year = str_to_bigint(age)
                temp_student.gender = gender
                temp_student.modified_by = request.user
                temp_student.modification_date_time = timezone.now()
        
                if is_new:
                    add_data.append(temp_student)
                else:
                    update_data.append(temp_student)

            row_count = len(df)
            add_count = len(add_data)
            modify_count = len(update_data)

            if add_count > 0:
                Student.objects.bulk_create(add_data, batch_size=500)
            if modify_count > 0:
                Student.objects.bulk_update(update_data, ["studienr"
                                                          , "name"
                                                          , "email_address"
                                                          , "campus"
                                                          , "market_member_num"
                                                          , "simulation_number"
                                                          , "age_in_year"
                                                          , "gender"
                                                          , "modified_by"
                                                          , "modification_date_time"
                                                          ], batch_size=500)

            return JsonResponse({
                "success": True,
                "message": f"Successfully read {row_count}, add rows {add_count}, modify rows {modify_count} rows from sheet '{sheet_name}'."
            })
        except Exception as e:
            return JsonResponse({"success": False, "error": f"Error reading sheet: {e}"})
    return JsonResponse({"success": False, "error": "Missing file or sheet name."})    

@login_required(login_url='login')
def upload_student_file_ajax(request):
    template_name = 'main/upload_student_ajax.html' 
    form = UploadFileForm()

    return render(request, template_name, {'form': form})

@login_required(login_url='login')
def upload_student_file(request):
    template_name = 'main/upload-student.html'
    data = None
    if request.method == 'POST':
        form = UploadFileForm(request.POST, request.FILES)
        if form.is_valid():
            file = request.FILES['file']
            sheet_name = form.cleaned_data['sheet_name']
            try:
                # Check the file extension
                if file.name.endswith('.csv'):
                    df = pd.read_csv(file)
                elif file.name.endswith(('.xls', '.xlsx')):
                    all_df = pd.ExcelFile(file)
                    sheet_names = all_df.sheet_names
                    if sheet_name not in sheet_names:
                        raise ValueError(f"This sheet name not found in the file. We have {len(sheet_names)} sheet(s). They are {(", ".join(sheet_names))}")
                    df = pd.read_excel(file, sheet_name=sheet_name)
                else:
                    raise ValueError('Unsupported file type. Please upload CSV or Excel.')

                for index, row in df.iterrows():
                    name = row.get('Name')
            except Exception as e:
                return render(request, template_name, { 'form': form,'error': str(e)})

            return render(request, template_name, {
            'form': form,
            'success': 'File processed successfully!'
        })

    else:
        form = UploadFileForm()

    return render(request, template_name, {'form': form})

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

@login_required(login_url='login')
def upload_student_score_file_ajax(request):
    template_name = 'main/upload_student_score_ajax.html' 
    simulations = Simulation.objects.all()

    return render(request, template_name, {'simulations': simulations})

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

@csrf_exempt
def process_student_score_file(request):
    if request.method == "POST" and request.FILES.get("file"):
        uploaded_file = request.FILES["file"]
        market_id = request.POST.get("market_id")
        simulation_id = request.POST.get("simulation_id")
        filename = ""
        try:
            check_file(uploaded_file)
            market_obj = Market.objects.filter(simulation_id = simulation_id , id = market_id).first()
            if market_obj is None:
                raise (f"Unable to find Market with id : {market_id}")

            filename = uploaded_file.name
            if uploaded_file.name.endswith('.csv'):
                    df = pd.read_csv(uploaded_file)
            elif uploaded_file.name.endswith(('.xls', '.xlsx')):
                df = pd.read_excel(uploaded_file)

            row_count = len(df)
            all_students = Student.objects.all()
            no_student_found_list = []
            dublicate_student_found_list = []
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
                already_exists = False
                if len(score_obj_add_list) > 0:
                    already_exists = any(obj.go_venture_subscription_key == subscription_key_parsed for obj in score_obj_add_list)
                if already_exists == False and len(score_obj_update_list) > 0:
                    already_exists = any(obj.go_venture_subscription_key == subscription_key_parsed for obj in score_obj_update_list)

                if already_exists:
                    dublicate_student_found_list.append(player_id)
                    continue

                temp_score = StudentScore.objects.filter(student_id = temp_student.id).first()
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
            if len(dublicate_student_found_list) > 0:
                additional_info += f", duplicate student found {len(dublicate_student_found_list)} [{', '.join(map(str,dublicate_student_found_list))}]"
                failed_count += len(dublicate_student_found_list)
            if len(student_with_other_market_found_list) > 0:
                additional_info += f", duplicate student found {len(student_with_other_market_found_list)} [{', '.join(map(str,student_with_other_market_found_list))}]"
                failed_count += len(student_with_other_market_found_list)
            return JsonResponse({
                "success": True,
                "message": f"Successfully read {row_count}, add rows {len(score_obj_add_list)}, modify rows {len(score_obj_update_list)} rows{additional_info}. \nFrom file {filename}"
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
        per_page = request.GET.get("per_page", settings.PER_PAGE)
        simulation_id = request.GET.get("simulation_id", None)
        market_id = request.GET.get("market_id", None)
        filters = get_filter(request)
        simulation_list = Simulation.objects.all()
        campus_list = get_all_campus()
        if simulation_id:
            market_list = Market.objects.filter(simulation_id = simulation_id).all()
        elif market_id:
            market_list = Market.objects.all()

        rows = get_student_score_report(filters)
        paginator = Paginator(rows, per_page)
        page_number = request.GET.get('page')
        page_obj = paginator.get_page(page_number)
        total_rows = paginator.count
    except Exception as e:
        error_message = e
    return render(request, template_name, {"page_obj": page_obj, "filters": filters
                                           , "total_rows": total_rows, "simulation_list": simulation_list, "market_list": market_list
                                           , "error_message": error_message, "campus_list" : campus_list})

@csrf_exempt
def get_markets_list(request):
    is_success = False
    error_message = ""
    market_obj = []
    if request.method == "POST":
        try:
            simulation_id = request.POST.get('simulation_id')
            if simulation_id:
                market_obj = Market.objects.filter(simulation_id = simulation_id).all()
            else:
                market_obj = Market.objects.all()
            market_obj = list(market_obj.values("id", "name"))
            is_success = True
        except Exception as e:
            error_message = str(e)
    return JsonResponse({"success": is_success, "error": error_message, "markets": list(market_obj)})

def get_filter(request):
    filters = {
            "report_type": request.GET.get("report_type", 1),
            "student_name": request.GET.get("student_name", "").strip(),
            "gender": request.GET.get("gender", ""), 
            "campus": request.GET.get("campus", ""), 
            "simulation_id": request.GET.get("simulation_id", None),
            "market_id": request.GET.get("market_id", None),
            "age_from": request.GET.get("age_from", None),
            "age_to": request.GET.get("age_to", None),
            "per_page": request.GET.get("per_page", settings.PER_PAGE),
        }
    return filters

@login_required(login_url='login')
def student_score_report_xlx(request):
    # Get your filtered data
    rows = []
    filters = get_filter(request)
    rows = get_student_score_report(filters)

    # Create workbook
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Students"

    # Add header
    ws.append(["ID", "Name"])

    # Add data
    for row in rows:
        #ws.append(row)
        ws.append([row["id"], row["name"]])

    # Prepare response
    response = HttpResponse(
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
    response["Content-Disposition"] = 'attachment; filename="students.xlsx"'

    wb.save(response)
    return response