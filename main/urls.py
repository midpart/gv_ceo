from django.urls import path
from django.contrib.auth import views as auth_views
from . import views, student_views, student_score_views, market_views, team_views

urlpatterns = [
    path('', views.index, name='index'),
    path('login/', auth_views.LoginView.as_view(template_name='main/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),

    path('get_sheet_names/', student_views.get_sheet_names, name='getSheetNames'),
    path('process_sheet/', student_views.process_sheet, name='processSheet'),
    path('upload_student_file/', student_views.upload_student_file, name='uploadStudentFile'),
    
    path('manage_market/', market_views.manage_market, name='manageMarkets'),
    path('market/add/', market_views.market_form, name='marketAdd'),
    path('market/edit/<int:pk>/', market_views.market_form, name='marketEdit'),
    path('market/delete/<int:pk>/', market_views.delete_market, name='marketDelete'),

    path('upload_student_score_file/', student_score_views.upload_student_score_file, name='uploadStudentScore'),
    path('get_markets/', student_score_views.get_markets, name='getMarkets'),
    path('process_student_score_file/', student_score_views.process_student_score_file, name='processStudentScoreFile'),
    path('student_score_report/', student_score_views.student_score_report, name='studentScoreReport'),

    path('get_markets_list/', student_score_views.get_markets_list, name='getMarketsList'),
    path('student_score_report_xlx/', student_score_views.student_score_report_xlx, name='studentScoreReportXlx'),

    path('upload_team_file/', team_views.upload_team_file, name='uploadTeamFile'),
    path('process_team_file_sheet/', team_views.process_team_file_sheet, name='processTeamFileSheet'),
    path('team_member_report/', team_views.team_member_report, name='teamMemberReport'),
]
