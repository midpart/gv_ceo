from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('login/', auth_views.LoginView.as_view(template_name='main/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('upload_student_file/', views.upload_student_file, name='uploadStudentFile'),
    path('get_sheet_names/', views.get_sheet_names, name='getSheetNames'),
    path('process_sheet/', views.process_sheet, name='processSheet'),
    path('upload_student_file_ajax/', views.upload_student_file_ajax, name='uploadStudentFileAjax'),
    path('manage_simulation_competition/', views.manage_simulation_competition, name='manageSimulations'),
    path('simulation_competition/add/', views.simulation_competition_form, name='simulationCompetitionAdd'),
    path('simulation_competition/edit/<int:pk>/', views.simulation_competition_form, name='simulationCompetitionEdit'),
    path('simulation_competition/delete/<int:pk>/', views.delete_simulation_competition, name='simulationCompetitionDelete'),
    path('upload_student_score_file_ajax/', views.upload_student_score_file_ajax, name='uploadStudentScoreAjax'),
    path('get_simulation_competitions/', views.get_simulation_competitions, name='getSimulationCompetitions'),
    path('process_student_score_file/', views.process_student_score_file, name='processStudentScoreFile'),
]
