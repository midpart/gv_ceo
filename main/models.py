from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.core.exceptions import ValidationError
from django.db.models import Q

User = get_user_model()
# Create your models here.

class Student(models.Model):
    studienr = models.BigIntegerField(null= True, blank=True)
    name = models.CharField(max_length=255)
    email_address = models.CharField(max_length=255)
    campus = models.CharField(max_length=255)
    subscription_key = models.CharField(max_length=255, null=False, unique=True)
    market_member_num = models.IntegerField(null=False, default=0)
    simulation_number = models.BigIntegerField(null=True, blank=True)
    age_in_year = models.IntegerField(null=True, blank=True)
    gender = models.CharField(max_length=10, null=True, blank=True)

    creation_date_time = models.DateTimeField(auto_now_add=True)
    modification_date_time = models.DateTimeField(default=timezone.now)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, blank=True, null=True,  related_name='students_created')
    modified_by = models.ForeignKey(User, on_delete=models.SET_NULL, blank=True, null=True, related_name='students_modified')

    def __str__(self):
        return self.name
    
class Simulation(models.Model):
    name = models.CharField(max_length=1000, null=False, unique=True)

    creation_date_time = models.DateTimeField(auto_now_add=True)
    modification_date_time = models.DateTimeField(default=timezone.now)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, blank=True, null=True,  related_name='simulation_created')
    modified_by = models.ForeignKey(User, on_delete=models.SET_NULL, blank=True, null=True, related_name='simulation_modified')
    
    def __str__(self):
        return self.name 

class Market(models.Model):
    simulation = models.ForeignKey(Simulation, on_delete=models.RESTRICT, related_name='simulation', null=False)
    market_number = models.BigIntegerField(null= False, unique=True)
    name = models.CharField(max_length=1000, null=False, unique=True)

    creation_date_time = models.DateTimeField(auto_now_add=True)
    modification_date_time = models.DateTimeField(default=timezone.now)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, blank=True, null=True,  related_name='market_created')
    modified_by = models.ForeignKey(User, on_delete=models.SET_NULL, blank=True, null=True, related_name='market_modified')
    
    def __str__(self):
        return f"Name: {self.name}, Number: {self.market_number}" 
    
    class Meta:
        ordering = ['name']

class Team(models.Model):
    simulation = models.ForeignKey(Simulation, on_delete=models.RESTRICT, related_name='team_simulation', null=True)
    name = models.CharField(max_length=255)
    teamID = models.IntegerField(null=False, default=0)
    sim_team_id = models.CharField(max_length=255, null=True)
    is_mmf = models.BooleanField(default=False)
    is_3pt = models.BooleanField(default=False)
    is_fix_alloc = models.BooleanField(default=False)

    creation_date_time = models.DateTimeField(auto_now_add=True)
    modification_date_time = models.DateTimeField(default=timezone.now)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, blank=True, null=True,  related_name='team_created')
    modified_by = models.ForeignKey(User, on_delete=models.SET_NULL, blank=True, null=True, related_name='team_modified')

    def __str__(self):
        return f"{self.teamID}"

class TeamMember(models.Model):
    team = models.ForeignKey(Team, on_delete=models.RESTRICT, related_name='team_team_member', null=False)
    student = models.ForeignKey(Student, on_delete=models.RESTRICT, related_name='student_team_member', null=False)
    role = models.CharField(max_length=255)
    teammember_order = models.IntegerField(null=False, default=0)

    creation_date_time = models.DateTimeField(auto_now_add=True)
    modification_date_time = models.DateTimeField(default=timezone.now)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, blank=True, null=True,  related_name='team_member_created')
    modified_by = models.ForeignKey(User, on_delete=models.SET_NULL, blank=True, null=True, related_name='team_member_modified')

    def __str__(self):
        return f"Student: {self.student.name}, Team: {self.team.name}"
    
class StudentScore(models.Model):
    student = models.ForeignKey(Student, on_delete=models.RESTRICT, related_name='student_scores', null=False)
    team = models.ForeignKey(Team, on_delete=models.RESTRICT, related_name='team_scores', null=True)
    team_member = models.ForeignKey(TeamMember, on_delete=models.RESTRICT, related_name='team_member_scores', null=True)
    market = models.ForeignKey(Market, on_delete=models.RESTRICT, related_name='market_scores', null=False)
    player_id = models.BigIntegerField(null= False)
    company = models.CharField(max_length=255)
    first_name = models.CharField(max_length=255)
    last_name = models.CharField(max_length=255)
    go_venture_subscription_key = models.CharField(max_length=255, null=False, unique=False)
    simulation_number = models.CharField(max_length=255)
    rubric_score_percentage = models.IntegerField(default=0)
    balanced_score_percentage = models.IntegerField(default=0)
    participation_percentage = models.IntegerField(default=0)
    participation_total = models.IntegerField(default=0)
    participation_in = models.IntegerField(default=0)
    rank_score_percentage = models.IntegerField(default=0)
    hr_score_percentage = models.IntegerField(default=0)
    ethics_score_percentage = models.IntegerField(default=0)
    competency_quiz_percentage = models.IntegerField(default=0)
    team_evaluation_percentage = models.IntegerField(default=0)
    period_joined = models.IntegerField(default=0)
    tutorial_quiz_percentage = models.IntegerField(null=True)

    creation_date_time = models.DateTimeField(auto_now_add=True)
    modification_date_time = models.DateTimeField(default=timezone.now)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, blank=True, null=True,  related_name='student_scores_created')
    modified_by = models.ForeignKey(User, on_delete=models.SET_NULL, blank=True, null=True, related_name='student_scores_modified')    

    def clean(self):
        # Prevent both being null
        if self.student is None and self.team is None:
            raise ValidationError("Either student or team must be provided.")

    def save(self, *args, **kwargs):
        # Run model validation before saving
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        if self.student:
            return f"Score for student: {self.student.name}"
        elif self.team:
            return f"Score for team: {self.team.name}"
        return "Invalid Score (no student or team)"
    
    class Meta:
        constraints = [
            # Ensure at least one of student/team is filled
            models.CheckConstraint(
                check= Q(student__isnull=False) | Q(team__isnull=False),
                name='student_or_team_required'
            ),
             models.UniqueConstraint(fields=['student', 'market'], name='unique_student_market')
        ]


class ImportFileLog(models.Model):
    name = models.CharField(max_length=1000, null=False, unique=False)
    remarks = models.CharField(max_length=5000, null=False, unique=False)
    total_row = models.IntegerField(default=0)
    total_insert = models.IntegerField(default=0)
    total_update = models.IntegerField(default=0)
    total_not_found = models.IntegerField(default=0)
    total_duplicate_found = models.IntegerField(default=0)

    creation_date_time = models.DateTimeField(auto_now_add=True)
    modification_date_time = models.DateTimeField(default=timezone.now)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, blank=True, null=True,  related_name='import_file_log_created')
    modified_by = models.ForeignKey(User, on_delete=models.SET_NULL, blank=True, null=True, related_name='import_file_log_modified')
    
    def __str__(self):
        return self.name 
    
class Simulation2Survey(models.Model):
    student = models.ForeignKey(Student, on_delete=models.RESTRICT, related_name='student_simulation2_survey', null=False)
    simulation = models.ForeignKey(Simulation, on_delete=models.RESTRICT, related_name='simulation_simulation2_survey', null=False)
    team = models.ForeignKey(Team, on_delete=models.RESTRICT, related_name='team_simulation2_survey', null=False)
    team_member = models.ForeignKey(TeamMember, on_delete=models.RESTRICT, related_name='team_member_simulation2_survey', null=False)

    indiv_time_spent = models.IntegerField(default=0)
    indiv_time_spent_t = models.DecimalField(default=0, decimal_places = 3, max_digits=4)

    joint_time_spent = models.IntegerField(default=0)
    joint_time_spent_t = models.DecimalField(default=0, decimal_places = 3, max_digits=4)

    days_in_person = models.IntegerField(default=0)
    days_in_person_t = models.DecimalField(default=0, decimal_places = 3, max_digits=4)

    responsib_clear = models.IntegerField(default=0)
    responsib_clear_t = models.DecimalField(default=0, decimal_places = 3, max_digits=4)

    responsib_own = models.IntegerField(default=0)
    responsib_own_t = models.DecimalField(default=0, decimal_places = 3, max_digits=4)

    responsib_change = models.IntegerField(default=0)
    responsib_change_t = models.DecimalField(default=0, decimal_places = 3, max_digits=4)

    areas_change_1 = models.IntegerField(default=0)
    areas_change_2 = models.IntegerField(default=0)
    areas_change_3 = models.IntegerField(default=0)
    areas_change_4 = models.IntegerField(default=0)
    areas_change_indiv = models.DecimalField(default=0, decimal_places = 3, max_digits=4)
    areas_change_team = models.DecimalField(default=0, decimal_places = 3, max_digits=4)

    responsib_outside = models.IntegerField(default=0)
    responsib_outside_t = models.DecimalField(default=0, decimal_places = 3, max_digits=4)

    ta_a = models.IntegerField(default=0)
    ta_b = models.IntegerField(default=0)
    ta_c = models.IntegerField(default=0)
    ta_indiv = models.DecimalField(default=0, decimal_places = 3, max_digits=4)
    ta_team = models.DecimalField(default=0, decimal_places = 3, max_digits=4)

    la_a = models.IntegerField(default=0)
    la_b = models.IntegerField(default=0)
    la_c = models.IntegerField(default=0)
    la_indiv = models.DecimalField(default=0, decimal_places = 3, max_digits=4)
    la_team = models.DecimalField(default=0, decimal_places = 3, max_digits=4)

    tms_s1 = models.IntegerField(default=0)
    tms_s2 = models.IntegerField(default=0)
    tms_s3 = models.IntegerField(default=0)
    tms_s4 = models.IntegerField(default=0)
    tms_s5 = models.IntegerField(default=0)
    tms_spec_indiv = models.DecimalField(default=0, decimal_places = 3, max_digits=4)
    tms_spec_team = models.DecimalField(default=0, decimal_places = 3, max_digits=4)

    tms_cred1 = models.IntegerField(default=0)
    tms_cred2 = models.IntegerField(default=0)
    tms_cred3 = models.IntegerField(default=0)
    tms_cred4 = models.IntegerField(default=0)
    tms_cred5 = models.IntegerField(default=0)
    tms_cred_indiv = models.DecimalField(default=0, decimal_places = 3, max_digits=4)
    tms_cred_team = models.DecimalField(default=0, decimal_places = 3, max_digits=4)

    tms_co1 = models.IntegerField(default=0)
    tms_co2 = models.IntegerField(default=0)
    tms_co3 = models.IntegerField(default=0)
    tms_co4 = models.IntegerField(default=0)
    tms_co5 = models.IntegerField(default=0)
    tms_coord_indiv = models.DecimalField(default=0, decimal_places = 3, max_digits=4)
    tms_coord_team = models.DecimalField(default=0, decimal_places = 3, max_digits=4)

    att_market_sales = models.IntegerField(default=0)
    att_production = models.IntegerField(default=0)
    att_randd = models.IntegerField(default=0)

    focus_shift_1 = models.IntegerField(default=0)
    focus_shift_2 = models.IntegerField(default=0)
    focus_shift_3 = models.IntegerField(default=0)
    focus_shift_4 = models.IntegerField(default=0)
    focus_shift_indiv = models.DecimalField(default=0, decimal_places = 3, max_digits=4)
    focus_shift_team = models.DecimalField(default=0, decimal_places = 3, max_digits=4)

    compet_import1 = models.IntegerField(default=0)
    compet_import2 = models.IntegerField(default=0)
    compet_import3 = models.IntegerField(default=0)
    compet_import_indiv = models.DecimalField(default=0, decimal_places = 3, max_digits=4)
    compet_import_team = models.DecimalField(default=0, decimal_places = 3, max_digits=4)

    pcs_1 = models.IntegerField(default=0)
    pcs_2 = models.IntegerField(default=0)
    pcs_3 = models.IntegerField(default=0)
    pcs_indiv = models.DecimalField(default=0, decimal_places = 3, max_digits=4)
    pcs_team = models.DecimalField(default=0, decimal_places = 3, max_digits=4)
    
    statoverall_1 = models.IntegerField(default=0)
    statoverall_2 = models.IntegerField(default=0)
    statoverall_3 = models.IntegerField(default=0)
    statoverall_4 = models.IntegerField(default=0)
    statoverall_5 = models.IntegerField(default=0)

    team_size = models.IntegerField(default=0)
    team_size_found = models.IntegerField(default=0)

    comments = models.CharField(max_length=1000)
    subscrip_key = models.CharField(max_length=255)
    mail_confirm = models.CharField(max_length=255)
    email = models.CharField(max_length=255)
    match_value = models.CharField(max_length=255)
    match_by_field = models.CharField(max_length=255)
    row_number = models.IntegerField(default=0)

    creation_date_time = models.DateTimeField(auto_now_add=True)
    modification_date_time = models.DateTimeField(default=timezone.now)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, blank=True, null=True,  related_name='Simulation2Survey_created')
    modified_by = models.ForeignKey(User, on_delete=models.SET_NULL, blank=True, null=True, related_name='Simulation2Survey_modified')
    
    def __str__(self):
        return f"{self.student.name}, sim: {self.simulation.name}"


class Simulation3Survey(models.Model):
    student = models.ForeignKey(Student, on_delete=models.RESTRICT, related_name='student_simulation3_survey', null=False)
    simulation = models.ForeignKey(Simulation, on_delete=models.RESTRICT, related_name='simulation_simulation3_survey', null=False)

    sim3_day1 = models.CharField(max_length=1000)
    sim3_day2 = models.CharField(max_length=1000)
    sim3_day3 = models.CharField(max_length=1000)
    sim3_day4 = models.CharField(max_length=1000)
    sim3_day5 = models.CharField(max_length=1000)
    sim3_subkey = models.CharField(max_length=255)
    sim3_confirm_email = models.CharField(max_length=255)
    email = models.CharField(max_length=255)
    
    statoverall_1 = models.IntegerField(default=0)
    statoverall_2 = models.IntegerField(default=0)
    statoverall_3 = models.IntegerField(default=0)
    statoverall_4 = models.IntegerField(default=0)
    statoverall_5 = models.IntegerField(default=0)

    match_value = models.CharField(max_length=255)
    match_by_field = models.CharField(max_length=255)
    row_number = models.IntegerField(default=0)

    creation_date_time = models.DateTimeField(auto_now_add=True)
    modification_date_time = models.DateTimeField(default=timezone.now)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, blank=True, null=True,  related_name='Simulation3Survey_created')
    modified_by = models.ForeignKey(User, on_delete=models.SET_NULL, blank=True, null=True, related_name='Simulation3Survey_modified')
    
    def __str__(self):
        return f"{self.student.name}, sim: {self.simulation.name}"
