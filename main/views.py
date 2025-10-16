from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from . forms import UploadFileForm, SimulationCompetitionForm
import pandas as pd
from django import forms
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from . models import Student, SimulationCompetition, Simulation
from django.utils import timezone
from django.core.paginator import Paginator
from django.conf import settings
import re

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
                name = row.get('Name')
                emailAdress = row.get('EmailAdress')
                campus = row.get('Campus')
                subscriptionKey = row.get('SubscriptionKey')
                marketMemberNum = row.get('MarketMemberNum')
                simulationNumber = row.get('SimulationNumber')
                
                temp_student = None
                temp_student = next((s for s in all_db_data if s.subscription_key == subscriptionKey), None)
                print(temp_student)
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
def manage_simulation_competition(request):
    template_name = 'main/manage_simulation_competition.html'
    simulations = SimulationCompetition.objects.all().order_by('modification_date_time')
    paginator = Paginator(simulations, settings.PER_PAGE)

    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, template_name, {'page_obj': page_obj})

@login_required(login_url='login')
def simulation_competition_form(request, pk=None):
    template_name = 'main/simulation_form.html'
    if pk:
        obj = get_object_or_404(SimulationCompetition, pk=pk)
    else:
        obj = None

    if request.method == "POST":
        form = SimulationCompetitionForm(request.POST, instance=obj)
        if form.is_valid():
            competition = form.save(commit=False)
            if not competition.pk:
                competition.created_by = request.user
            
            competition.modified_by = request.user
            competition.modification_date_time = timezone.now()
            competition.save()
            return redirect('manageSimulations')  # redirect to list page
    else:
        form = SimulationCompetitionForm(instance=obj)

    return render(request, template_name, {'form': form, 'obj': obj})

@login_required(login_url='login')
def delete_simulation_competition(request, pk):
    is_success = False
    message = ""
    if request.method == 'POST' and request.headers.get('x-requested-with') == 'XMLHttpRequest':
        try:
            obj = get_object_or_404(SimulationCompetition, pk=pk)
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
def get_simulation_competitions(request):
    if request.method == "POST" and request.FILES.get("file"):
        uploaded_file = request.FILES["file"]
        try:
            check_file(uploaded_file)
            file_name = uploaded_file.name
            simulation_id = request.POST.get('simulation_competition_id')
            simulation_obj = get_object_or_404(Simulation, pk=simulation_id)
            name_array = parse_file_name(file_name)
            simulation_number = None
            if name_array is not None and len(name_array) == 2:
                simulation_number = str_to_bigint(name_array[0])
                name = name_array[1]

                simulation_competition_obj = SimulationCompetition.objects.filter(simulation_number = simulation_number).first()
                if simulation_competition_obj is None: 
                    simulation_competition_obj = SimulationCompetition(
                        simulation = simulation_obj,
                        simulation_number = simulation_number,
                        name = name,
                        creation_date_time = timezone.now(),
                        modification_date_time = timezone.now(),
                        created_by = request.user,
                        modified_by = request.user
                    )
                    simulation_competition_obj.save()

            competitions = SimulationCompetition.objects.all().order_by("simulation_number").values("id", "name")
            selected_competition = competitions.filter(simulation_number = simulation_number).first()
            if selected_competition is None:
                selected_id = None
            else:
                selected_id = selected_competition["id"]

            return JsonResponse({"success": True, "competitions": list(competitions), "selected_id": selected_id})
        except Exception as e:
            return JsonResponse({"success": False, "error": str(e)})
    return JsonResponse({"success": False, "error": "No file uploaded."})

@csrf_exempt
def process_student_score_file(request):
    if request.method == "POST" and request.FILES.get("file"):
        uploaded_file = request.FILES["file"]
        simulation_competition_id = request.POST.get("simulation_competition_id")
        simulation_id = request.POST.get("simulation_id")
        try:
            check_file(uploaded_file)
            print(simulation_competition_id)
            print(simulation_id)

            if uploaded_file.name.endswith('.csv'):
                    df = pd.read_csv(uploaded_file)
            elif uploaded_file.name.endswith(('.xls', '.xlsx')):
                df = pd.read_excel(uploaded_file)

            row_count = len(df)
            add_count = 0
            modify_count = 0
            for index, row in df.iterrows():
                player_id = row.get('Player Id')
                company = row.get('Company')
                first_name = row.get('First Name')
                last_name = row.get('Last Name')
                subscription_key__simulation_number = row.get('GoVenture Subscription Key | Simulation Number')
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

                #print(player_id)

            # df = pd.read_excel(excel_file, sheet_name=sheet_name)
            
            # all_db_data = Student.objects.all()
            # add_data = []
            # update_data = []

            # for index, row in df.iterrows():
            #     studienr = row.get('Studienr')
            #     name = row.get('Name')
            #     emailAdress = row.get('EmailAdress')
            #     campus = row.get('Campus')
            #     subscriptionKey = row.get('SubscriptionKey')
            #     marketMemberNum = row.get('MarketMemberNum')
            #     simulationNumber = row.get('SimulationNumber')
                
            #     temp_student = None
            #     temp_student = next((s for s in all_db_data if s.subscription_key == subscriptionKey), None)
            #     print(temp_student)
            #     is_new = False
            #     if temp_student is None:
            #         is_new = True
            #         temp_student = Student(
            #             subscription_key = subscriptionKey,
            #             created_by = request.user,
            #             creation_date_time = timezone.now()
            #         )

            #     temp_student.studienr = str_to_bigint(studienr)
            #     temp_student.name = name
            #     temp_student.email_address = emailAdress
            #     temp_student.campus = campus
            #     temp_student.market_member_num = str_to_bigint(marketMemberNum)
            #     temp_student.simulation_number = str_to_bigint(simulationNumber)
            #     temp_student.modified_by = request.user
            #     temp_student.modification_date_time = timezone.now()
        
            #     if is_new:
            #         add_data.append(temp_student)
            #     else:
            #         update_data.append(temp_student)

            # row_count = len(df)
            # add_count = len(add_data)
            # modify_count = len(update_data)

            # if add_count > 0:
            #     Student.objects.bulk_create(add_data, batch_size=500)
            # if modify_count > 0:
            #     Student.objects.bulk_update(update_data, ["studienr"
            #                                               , "name"
            #                                               , "email_address"
            #                                               , "campus"
            #                                               , "market_member_num"
            #                                               , "simulation_number"
            #                                               , "modified_by"
            #                                               , "modification_date_time"
            #                                               ], batch_size=500)

            return JsonResponse({
                "success": True,
                "message": f"Successfully read {row_count}, add rows {add_count}, modify rows {modify_count} rows ."
            })
        except Exception as e:
            return JsonResponse({"success": False, "error": f"Error reading sheet: {e}"})
    return JsonResponse({"success": False, "error": "Missing file or sheet name."})    