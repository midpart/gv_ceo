from django.db import connection

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
	, stu.name 
	, stu.age_in_year AS age
	, stu.gender 
	, stu.campus 
	, sc.go_venture_subscription_key 
	, sc.simulation_number AS go_venture_simulation_number
	, stu.subscription_key 
	, stu.simulation_number 
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