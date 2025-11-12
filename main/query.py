from django.db import connection

def str_to_bigint(value):
    try:
        return int(value)
    except (ValueError, TypeError):
        return None

def get_param_value(params_filter, key):
    if key in params_filter:
        value = params_filter[key]
        return value
    return None

def dictfetchall(cursor):
    """Return all rows from a cursor as a dict"""
    columns = [col[0] for col in cursor.description]
    return [
        dict(zip(columns, row))
        for row in cursor.fetchall()
    ]

def get_student_score_report(params_filter):

    sql = """
SELECT 
	sc.id 
	, sc.market_id 
	, m.simulation_id 
	, sc.student_id 
	, sc.team_id 
	, m.name AS market_name
    , stu.studienr 
	, stu.name 
	, stu.age_in_year AS age
	, stu.gender
    , stu.email_address 
	, stu.campus 
	, sc.go_venture_subscription_key 
	, sc.simulation_number AS go_venture_simulation_number
	, stu.subscription_key 
	, stu.simulation_number 
    , sc.player_id 
    , sc.company
	, sc.rubric_score_percentage 
	, sc.balanced_score_percentage 
	, sc.participation_percentage 
	, sc.participation_in 
	, sc.participation_total 
	, sc.rank_score_percentage 
	, sc.hr_score_percentage 
	, sc.ethics_score_percentage 
	, sc.competency_quiz_percentage 
	, sc.team_evaluation_percentage 
	, sc.period_joined 
	, sc.tutorial_quiz_percentage 
FROM main_studentscore sc 
INNER JOIN main_market m ON m.id = sc.market_id 
LEFT JOIN main_student stu ON stu.id = sc.student_id 
"""
    params = []
    filter_query = []

    market_id = get_param_value(params_filter, "market_id")
    simulation_id = get_param_value(params_filter, "simulation_id")
    student_id = get_param_value(params_filter, "student_id")
    team_id = get_param_value(params_filter, "team_id")
    report_type = get_param_value(params_filter, "report_type")
    student_name = get_param_value(params_filter, "student_name")
    age_from = get_param_value(params_filter, "age_from")
    age_to = get_param_value(params_filter, "age_to")
    gender = get_param_value(params_filter, "gender")
    campus = get_param_value(params_filter, "campus")

    if market_id is not None and market_id.isdigit():
        filter_query.append("AND sc.market_id = %s")
        params.append(market_id)

    if simulation_id is not None and simulation_id.isdigit():
        filter_query.append("AND m.simulation_id = %s")
        params.append(simulation_id)

    if student_id is not None and student_id.isdigit():
        filter_query.append("AND sc.student_id = %s")
        params.append(student_id)

    if team_id is not None and team_id.isdigit():
        filter_query.append("AND sc.team_id = %s")
        params.append(team_id)

    apply_student_filter = True
    if report_type is not None:
        if report_type  == 1: # only student
            filter_query.append("AND sc.student_id IS NOT NULL")
        elif report_type  == 2: # only Team
            apply_student_filter = False
            filter_query.append("AND sc.team_id IS NOT NULL")

    if student_name is not None and apply_student_filter and student_name:
        filter_query.append("AND stu.name LIKE %s")
        params.append(f"%{student_name}%")

    if age_from is not None and apply_student_filter and age_from.isdigit():
        filter_query.append("AND stu.age_in_year >= %s")
        params.append(age_from)

    if age_to is not None and apply_student_filter and age_to.isdigit():
        filter_query.append("AND stu.age_in_year <= %s")
        params.append(age_to)

    if gender is not None and apply_student_filter and gender:
        if gender.lower() == 'female':
            filter_query.append("AND stu.gender = 'Female'")
        elif gender.lower() == 'male':
            filter_query.append("AND stu.gender = 'Male'")

    if campus is not None and apply_student_filter and campus:
        filter_query.append("AND stu.campus = %s")
        params.append(f"{campus}")
    
    where_sql = "WHERE 1 = 1 "
    if len(filter_query) > 0:
        where_sql += " \n ".join(filter_query)
    sql += where_sql
    sql += " \n ORDER BY rubric_score_percentage DESC"
    # execute safely
    with connection.cursor() as cursor:
        #print(cursor.mogrify(sql, params))
        print(get_sql_debug(sql, params))  # for debugging only
        cursor.execute(sql, params)
        #rows = cursor.fetchall()
        rows = dictfetchall(cursor)

    return rows

def get_team_member_report(params_filter):

    sql = """
SELECT 
	tm.id as team_id
	, tm.student_id 
	, t.simulation_id 
	, t.teamID 
	, t.sim_team_id 
	, tm.role
	, tm.teammember_order 
	, t.name as team_name
	, t.is_3pt 
	, t.is_fix_alloc 
	, t.is_mmf 
	, stu.name as student_name
	, stu.gender 
	, stu.age_in_year as age
    , stu.campus
	, s.name as simulation_name
FROM main_teammember tm 
INNER JOIN main_team t ON t.id = tm.team_id 
INNER JOIN main_student stu ON stu.id = tm.student_id 
INNER JOIN main_simulation s ON s.id = t.simulation_id 
"""
    params = []
    filter_query = []

    simulation_ids = get_param_value(params_filter, "simulation_ids")
    student_name = get_param_value(params_filter, "student_name")
    teamID = get_param_value(params_filter, "teamID")
    is_3pt = get_param_value(params_filter, "is_3pt")
    is_fix_alloc = get_param_value(params_filter, "is_fix_alloc")
    is_mmf = get_param_value(params_filter, "is_mmf")
    campus = get_param_value(params_filter, "campus")

    if simulation_ids is not None and len(simulation_ids) > 0:
        selected_simulation_ids = [int(c) for c in simulation_ids if c.isdigit()]
        id_list = ', '.join(str(c) for c in selected_simulation_ids)
        filter_query.append(f"AND t.simulation_id IN ({id_list})")

    if student_name is not None and student_name:
        filter_query.append("AND stu.name LIKE %s")
        params.append(f"%{student_name}%")

    if teamID is not None and teamID and str_to_bigint(teamID) > 0:
        filter_query.append("AND t.teamID = %s")
        params.append(f"{str_to_bigint(teamID)}")

    if is_3pt is not None and is_3pt and str_to_bigint(is_3pt) > -1:
        filter_query.append("AND t.is_3pt = %s")
        params.append(f"{is_3pt}")

    if is_fix_alloc is not None and is_fix_alloc and str_to_bigint(is_fix_alloc) > -1:
        filter_query.append("AND t.is_fix_alloc = %s")
        params.append(f"{is_fix_alloc}")

    if is_mmf is not None and is_mmf and str_to_bigint(is_mmf) > -1:
        filter_query.append("AND t.is_mmf = %s")
        params.append(f"{is_mmf}")
    
    if campus is not None and campus:
        filter_query.append("AND stu.campus = %s")
        params.append(f"{campus}")

    where_sql = "WHERE 1 = 1 "
    if len(filter_query) > 0:
        where_sql += " \n ".join(filter_query)
    sql += where_sql
    sql += " \n ORDER BY t.teamID ASC, tm.teammember_order ASC"
    # execute safely
    with connection.cursor() as cursor:
        #print(cursor.mogrify(sql, params))
        print(get_sql_debug(sql, params))  # for debugging only
        cursor.execute(sql, params)
        #rows = cursor.fetchall()
        rows = dictfetchall(cursor)

    return rows

def get_sql_debug(sql, params):
    """
    Returns SQL with parameters substituted for debugging (SQLite safe)
    """
    # Make a copy so we don't modify original
    sql_debug = sql[:]
    
    for p in params:
        if isinstance(p, str):
            p = f"'{p}'"  # wrap strings in quotes
        elif p is None:
            p = 'NULL'
        sql_debug = sql_debug.replace("%s", str(p), 1)
    return sql_debug

def get_all_campus():
    sql = "SELECT ms.campus FROM main_student ms GROUP BY ms.campus ORDER BY campus;"
    with connection.cursor() as cursor:
        #print(cursor.mogrify(sql, params))
        #print(get_sql_debug(sql, params))  # for debugging only
        #rows = cursor.fetchall()
        cursor.execute(sql)
        rows = dictfetchall(cursor)

    return rows