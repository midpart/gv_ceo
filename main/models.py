from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone

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

    creation_date_time = models.DateTimeField(auto_now_add=True)
    modification_date_time = models.DateTimeField(default=timezone.now)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, blank=True, null=True,  related_name='students_created')
    modified_by = models.ForeignKey(User, on_delete=models.SET_NULL, blank=True, null=True, related_name='students_modified')

class Simulation(models.Model):
    name = models.CharField(max_length=1000, null=False, unique=True)

    creation_date_time = models.DateTimeField(auto_now_add=True)
    modification_date_time = models.DateTimeField(default=timezone.now)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, blank=True, null=True,  related_name='simulation_created')
    modified_by = models.ForeignKey(User, on_delete=models.SET_NULL, blank=True, null=True, related_name='simulation_modified')
    def __str__(self):
        return self.name 

class SimulationCompetition(models.Model):
    simulation = models.ForeignKey(Simulation, on_delete=models.RESTRICT, related_name='simulation', null=False)
    simulation_number = models.BigIntegerField(null= False, unique=True)
    name = models.CharField(max_length=1000, null=False, unique=True)

    creation_date_time = models.DateTimeField(auto_now_add=True)
    modification_date_time = models.DateTimeField(default=timezone.now)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, blank=True, null=True,  related_name='simulation_completition_created')
    modified_by = models.ForeignKey(User, on_delete=models.SET_NULL, blank=True, null=True, related_name='simulation_completition_modified')
    
class StudentScore(models.Model):
    student = models.ForeignKey(Student, on_delete=models.RESTRICT, related_name='scores', null=False)
    simulation_competition = models.ForeignKey(SimulationCompetition, on_delete=models.RESTRICT, related_name='scores', null=False)
    player_id = models.BigIntegerField(null= False)
    company = models.CharField(max_length=255)
    first_name = models.CharField(max_length=255)
    last_name = models.CharField(max_length=255)
    go_venture_subscription_key = models.CharField(max_length=255, null=False, unique=True)
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

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['student', 'simulation_competition'],
                name='unique_student_simulation_competition'
            )
        ]