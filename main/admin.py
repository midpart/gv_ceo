from django.contrib import admin

from .models import *
from django.conf import settings
from django.utils import timezone
# Register your models here.
# admin.site.register(Student)
@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = ('id', 'studienr', 'name', 'email_address'
                    , 'campus', 'subscription_key', 'market_member_num'
                    , 'simulation_number', 'creation_date_time', 'created_by')  
    search_fields = ('name', 'studienr', 'subscription_key')
    list_filter = ('campus',)
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

@admin.register(SimulationCompetition)
class SimulationCompetitionAdmin(admin.ModelAdmin):
    def save_model(self, request, obj, form, change):
        if not obj.pk:
            obj.created_by = request.user
        obj.modified_by = request.user
        obj.modification_date_time = timezone.now()
        return super().save_model(request, obj, form, change)
    
    list_display = ('id', 'simulation', 'simulation_number', 'name', 'creation_date_time', 'modification_date_time', 'created_by',  'modified_by')  
    list_per_page = settings.PER_PAGE
    list_filter = ('simulation',)