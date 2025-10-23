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
    path('manage_market/', views.manage_market, name='manageMarkets'),
    path('market/add/', views.market_form, name='marketAdd'),
    path('market/edit/<int:pk>/', views.market_form, name='marketEdit'),
    path('market/delete/<int:pk>/', views.delete_market, name='marketDelete'),
    path('upload_student_score_file_ajax/', views.upload_student_score_file_ajax, name='uploadStudentScoreAjax'),
    path('get_markets/', views.get_markets, name='getMarkets'),
    path('process_student_score_file/', views.process_student_score_file, name='processStudentScoreFile'),
]
