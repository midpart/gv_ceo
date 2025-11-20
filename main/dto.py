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

    statoverall_indiv: float = 0
    statoverall_team: float = 0