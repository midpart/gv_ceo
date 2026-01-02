from dataclasses import dataclass

@dataclass
class TeamSim2Survey:
    team_id: int
    team_size: int
    team_size_found: int

    indiv_time_spent: int = 0
    indiv_time_spent_t: float = 0

    joint_time_spent: int = 0
    joint_time_spent_t: float = 0

    days_in_person: int = 0
    days_in_person_t: float = 0

    responsib_clear: int = 0
    responsib_clear_t: float = 0

    responsib_own: int = 0
    responsib_own_t: float = 0

    responsib_change: int = 0
    responsib_change_t: float = 0

    areas_change_indiv: float = 0
    areas_change_team: float = 0

    responsib_outside: int = 0
    responsib_outside_t: float = 0

    ta_indiv: float = 0
    ta_team: float = 0

    la_indiv: float = 0
    la_team: float = 0

    tms_spec_indiv: float = 0
    tms_spec_team: float = 0

    tms_cred_indiv: float = 0
    tms_cred_team: float = 0

    tms_coord_indiv: float = 0
    tms_coord_team: float = 0

    focus_shift_indiv: float = 0
    focus_shift_team: float = 0

    compet_import_indiv: float = 0
    compet_import_team: float = 0

    pcs_indiv: float = 0
    pcs_team: float = 0

@dataclass
class AllData:
    studienr: int
    student_name: str
    email_address: str
    campus: str
    subscription_key: str
    age_in_year: int
    gender: str

    simulation_name: str = None
    market_name: str = None
    market_number: int = None

    team_name: str = None
    teamID: str  = None
    is_mmf: bool = None
    is_3pt: bool = None
    is_fix_alloc: bool = None
    role: str = None
    teammember_order: int = None

    player_id: int = None
    company: str = None
    rubric_score_percentage: int = None
    balanced_score_percentage: int = None
    participation_percentage: int = None
    participation_total: int = None
    participation_in: int = None
    rank_score_percentage: int = None
    hr_score_percentage: int = None
    ethics_score_percentage: int = None
    competency_quiz_percentage: int = None
    team_evaluation_percentage: int = None
    period_joined: int = None
    tutorial_quiz_percentage: int = None

    indiv_time_spent: int = None
    indiv_time_spent_t: float = None
    joint_time_spent: int = None
    joint_time_spent_t: float = None
    days_in_person: int = None
    days_in_person_t: float  = None
    responsib_clear: int  = None
    responsib_clear_t: float  = None
    responsib_own: int = None
    responsib_own_t: float  = None
    responsib_change: int  = None
    responsib_change_t: float  = None
    areas_change_1: int  = None
    areas_change_2: int  = None
    areas_change_3: int  = None
    areas_change_4: int  = None
    areas_change_indiv: float = None
    areas_change_team: float = None
    responsib_outside: int = None
    responsib_outside_t: float = None
    ta_a: int = None
    ta_b: int = None
    ta_c: int  = None
    ta_indiv: float  = None
    ta_team: float  = None
    la_a: int = None
    la_b: int  = None
    la_c: int  = None
    la_indiv: float  = None
    la_team: float  = None
    tms_s1: int  = None
    tms_s2: int  = None
    tms_s3: int = None
    tms_s4: int  = None
    tms_s5: int  = None
    tms_spec_indiv: float  = None
    tms_spec_team: float  = None
    tms_cred1: int  = None
    tms_cred2: int  = None
    tms_cred3: int  = None
    tms_cred4: int  = None
    tms_cred5: int  = None
    tms_cred_indiv: float  = None
    tms_cred_team: float  = None
    tms_co1: int = None
    tms_co2: int  = None
    tms_co3: int  = None
    tms_co4: int = None
    tms_co5: int = None
    tms_coord_indiv: float = None
    tms_coord_team: float = None
    att_market_sales: int  = None
    att_production: int = None
    att_randd: int  = None
    focus_shift_1: int  = None
    focus_shift_2: int  = None
    focus_shift_3: int  = None
    focus_shift_4: int = None
    focus_shift_indiv: float = None
    focus_shift_team: float = None
    compet_import1: int = None
    compet_import2: int = None
    compet_import3: int = None
    compet_import_indiv: float = None
    compet_import_team: float  = None
    pcs_1: int = None
    pcs_2: int  = None
    pcs_3: int  = None
    pcs_indiv: float  = None
    pcs_team: float  = None
    statoverall_1: int  = None
    statoverall_2: int  = None
    statoverall_3: int  = None
    statoverall_4: int  = None
    statoverall_5: int  = None
    team_size: int = None
    team_size_found: int = None 
    comments: str = None

    sim3_day1: str = None
    sim3_day2: str = None
    sim3_day3: str = None
    sim3_day4: str = None
    sim3_day5: str = None
    sim3_statoverall_1: int  = None
    sim3_statoverall_2: int  = None
    sim3_statoverall_3: int  = None
    sim3_statoverall_4: int = None
    sim3_statoverall_5: int = None