from django.contrib import admin

from .models import *
from django.conf import settings
from django.utils import timezone
# Register your models here.
# admin.site.register(Student)
@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = ('id', 'studienr', 'name', 'age_in_year', 'gender', 'email_address'
                    , 'campus', 'subscription_key', 'market_member_num'
                    , 'simulation_number', 'creation_date_time', 'created_by')  
    search_fields = ('name', 'studienr', 'subscription_key', 'age_in_year')
    list_filter = ('campus', 'gender',)
    list_per_page = settings.PER_PAGE

    def has_add_permission(self, request):
        return False

@admin.register(Simulation)
class SimulationAdmin(admin.ModelAdmin):
    def save_model(self, request, obj, form, change):
        if not obj.pk:
            obj.created_by = request.user
        obj.modified_by = request.user
        obj.modification_date_time = timezone.now()
        return super().save_model(request, obj, form, change)
    
    list_display = ('id', 'name', 'creation_date_time', 'modification_date_time', 'created_by',  'modified_by')  
    list_per_page = settings.PER_PAGE

@admin.register(Market)
class MarketAdmin(admin.ModelAdmin):
    def save_model(self, request, obj, form, change):
        if not obj.pk:
            obj.created_by = request.user
        obj.modified_by = request.user
        obj.modification_date_time = timezone.now()
        return super().save_model(request, obj, form, change)
    
    list_display = ('id', 'simulation', 'market_number', 'name', 'creation_date_time', 'modification_date_time', 'created_by',  'modified_by')  
    list_per_page = settings.PER_PAGE
    list_filter = ('simulation',)

@admin.register(StudentScore)
class StudentScoreAdmin(admin.ModelAdmin):
    def save_model(self, request, obj, form, change):
        if not obj.pk:
            obj.created_by = request.user
        obj.modified_by = request.user
        obj.modification_date_time = timezone.now()
        return super().save_model(request, obj, form, change)
    
    list_display = ('id', 'student', 'team', 'market', 'player_id', 'company', 'first_name', 'rubric_score_percentage',  'creation_date_time', 'modification_date_time', 'created_by',  'modified_by')  
    list_per_page = settings.PER_PAGE
    list_filter = ('market',)
    
@admin.register(ImportFileLog)
class ImportFileLogAdmin(admin.ModelAdmin):
    def save_model(self, request, obj, form, change):
        if not obj.pk:
            obj.created_by = request.user
        obj.modified_by = request.user
        obj.modification_date_time = timezone.now()
        return super().save_model(request, obj, form, change)
    
    list_display = ('id', 'name', 'total_row', 'total_insert', 'total_update', 'total_not_found', 'total_duplicate_found', 'remarks'
                    , 'creation_date_time', 'modification_date_time', 'created_by',  'modified_by')  
    list_per_page = settings.PER_PAGE
    list_filter = ('name',)

    def has_add_permission(self, request):
        return False
    
@admin.register(Team)
class TeamAdmin(admin.ModelAdmin):
    def save_model(self, request, obj, form, change):
        if not obj.pk:
            obj.created_by = request.user
        obj.modified_by = request.user
        obj.modification_date_time = timezone.now()
        return super().save_model(request, obj, form, change)
    
    list_display = ('id', 'name', 'simulation', 'teamID', 'sim_team_id', 'is_mmf', 'is_3pt', 'is_fix_alloc'
                    , 'creation_date_time', 'modification_date_time', 'created_by',  'modified_by')  
    list_per_page = settings.PER_PAGE
    list_filter = ('simulation', 'is_mmf', 'is_3pt', 'is_fix_alloc',)

    def has_add_permission(self, request):
        return False        
    
@admin.register(TeamMember)
class TeamMemberAdmin(admin.ModelAdmin):
    def save_model(self, request, obj, form, change):
        if not obj.pk:
            obj.created_by = request.user
        obj.modified_by = request.user
        obj.modification_date_time = timezone.now()
        return super().save_model(request, obj, form, change)
    
    list_display = ('id', 'team', 'student', 'role', 'teammember_order'
                    , 'creation_date_time', 'modification_date_time', 'created_by',  'modified_by')  
    list_per_page = settings.PER_PAGE
    list_filter = ('team', 'role',)

    def has_add_permission(self, request):
        return False    
    
@admin.register(Simulation2Survey)
class Simulation2SurveyAdmin(admin.ModelAdmin):
    def save_model(self, request, obj, form, change):
        if not obj.pk:
            obj.created_by = request.user
        obj.modified_by = request.user
        obj.modification_date_time = timezone.now()
        return super().save_model(request, obj, form, change)
    
    list_display = ('id', 'student', 'simulation', 'indiv_time_spent', 'joint_time_spent'
                    , 'creation_date_time', 'modification_date_time', 'created_by',  'modified_by')  
    list_per_page = settings.PER_PAGE
    list_filter = ('simulation',)

    def has_add_permission(self, request):
        return False   