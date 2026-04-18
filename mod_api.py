from datetime import date, timedelta
from flask import jsonify, request, session

def get_left_n_chars_until_space(text, n):
	"""
	Code originally generated from Google search, debugging needed :(

	Extracts the left 'n' characters of a string, stopping at the first space encountered.

	Args:
		text (str): The input string.
		n (int): The maximum number of characters to extract from the left.

	Returns:
		str: The extracted substring.
	"""
	# Slice the string to get the first 'n' characters
	segment = text[:n]

	# Find the index of the first space in the segment
	space_index = segment.rfind(' ')

	# If a space is found, return the substring up to that space
	if space_index != -1:
		return segment[:space_index]
	# If no space is found within the first 'n' characters, return the entire segment
	else:
		return segment

def api(mysql, api_type):
	if api_type == 'test':
		return test()
	elif api_type == 'daily_update':
		return daily_update(mysql)
	elif api_type == 'source_update':
		return source_update(mysql)
	elif api_type == 'user_summary':
	    return user_summary(mysql)
	elif api_type == 'user_activity':
	    return user_activity(mysql)
	elif api_type == 'user_last_upd':
	    return user_last_upd(mysql)
	else:
		return jsonify({"error": "api_type error"}), 404

def test():
	data = request.get_json()
	return jsonify(data), 201

def daily_update(mysql):
	param = request.get_json()
	cursor = mysql.connection.cursor()

	xy = {}

	# Calculate the date some days ago
	date_count = date.today() - timedelta(days=param['days'])

	for _ in range(param['days']):
		xy[date_count.strftime('%Y-%m-%d')] = 0
		date_count += timedelta(days=1)

	query = "SELECT date(date_recorded), count(scenario_id) FROM scenarios "
	query += "WHERE date_recorded > DATE_SUB(NOW(), INTERVAL %s DAY) "
	query += "AND username <> 'initial'	"
	query += "GROUP BY date(date_recorded)"
	cursor.execute(query, (param['days'],))

	q_res = cursor.fetchall()
	for item in q_res:
		tmp = item[0].strftime('%Y-%m-%d')
		xy[tmp] = item[1]
	data = {"x": list(xy.keys()), "y": list(xy.values())}
	return jsonify(data), 201

def source_update(mysql):
	cursor = mysql.connection.cursor()

	tbl = []

	query = "SELECT tot_table.sid, tot_table.so_title, valid_table.validated, tot_table.total FROM "
	query += "(SELECT so.source_id as sid, so.title as so_title, count(scenario_id) as total "
	query += "FROM scenarios sc, sources so WHERE sc.source_id = so.source_id "
	query += "AND deleted = 0 "
	query += "GROUP BY sc.source_id) AS tot_table LEFT JOIN "
	query += "(SELECT so.source_id as sid, count(scenario_id) as validated "
	query += "FROM scenarios sc, sources so WHERE sc.source_id = so.source_id "
	query += "AND deleted = 0 AND sc.validated=1 "
	query += "GROUP BY sc.source_id) AS valid_table ON "
	query += "tot_table.sid = valid_table.sid ORDER BY tot_table.sid"
	cursor.execute(query)
	q_res = cursor.fetchall()

	# Not to make the above query too long, I will manually join the third table
	query = "select so_base.sid, act_tot as action_tot from"
	query += "(select source_id as sid from sources) as so_base "
	query += "left join (select so.source_id as sid, count(action_id) as act_tot "
	query += "from sources so left join scenarios sc "
	query += "ON so.source_id = sc.source_id "
	query += "inner join actions a on sc.scenario_id = a.scenario_id "
	query += "where sc.deleted = 0 and a.deleted = 0 and sc.validated = 1  "
	query += "group by so.source_id) as grp_tbl "
	query += "on so_base.sid = grp_tbl.sid "
	query += "order by so_base.sid"
	cursor.execute(query)
	q_actions = cursor.fetchall()

	idx = 0
	for item in q_res:
		rec = {}
		rec['sid'] = item[0]
		rec['title'] = item[1]
		if item[2]:
			rec['validate'] = item[2]
		else:
			rec['validate'] = 0
		rec['total'] = item[3]
		rec['complete'] = round(float(rec['validate']) / float(item[3]) * 100, 2)
		if q_actions[idx][1]:
			rec['action_tot'] = q_actions[idx][1]
		else:
			rec['action_tot'] = 0
		tbl.append(rec)
		idx += 1

	return jsonify(tbl), 201

def user_summary(mysql):
    cursor = mysql.connection.cursor()

    tbl = []

    query = "SELECT base_user.username, last_update.last_update_datetime, validate.validated_count FROM "
    query += "(SELECT user_id, username from users) AS  base_user LEFT JOIN "
    query += "(SELECT username, max(date_recorded) AS last_update_datetime FROM scenarios "
    query += "WHERE username <> 'initial' GROUP BY username) AS last_update "
    query += "ON base_user.username = last_update.username LEFT JOIN "
    query += "(SELECT username, count(scenario_id) AS validated_count FROM scenarios "
    query += "WHERE username <> 'initial' AND validated =1 "
    query += "GROUP BY username) AS validate "
    query += "ON base_user.username = validate.username "
    query += "ORDER BY base_user.user_id "
    cursor.execute(query)
    q_res = cursor.fetchall()

    for item in q_res:
    	rec = {}
    	rec['username'] = item[0]
    	if item[1]:
    		rec['last_update'] = item[1].strftime("%Y-%m-%d %H:%M:%S")
    	else:
    		rec['last_update'] = "1900-01-01 00:00:00"
    	if item[2]:
    		rec['validate'] = item[2]
    	else:
    		rec['validate'] = 0
    	tbl.append(rec)
    return jsonify(tbl), 201

def user_activity(mysql):
	param = request.get_json()
	cursor = mysql.connection.cursor()

	xy = {}

	# Calculate the date some days ago
	date_count = date.today() - timedelta(days=param['days'])

	for _ in range(param['days']):
		xy[date_count.strftime('%Y-%m-%d')] = 0
		date_count += timedelta(days=1)

	query = "SELECT date(date_recorded), count(scenario_id) FROM scenarios "
	query += "WHERE date_recorded > DATE_SUB(NOW(), INTERVAL %s DAY) "
	query += "AND username = %s "
	query += "GROUP BY date(date_recorded)"
	cursor.execute(query, (param['days'], session['username']))

	q_res = cursor.fetchall()
	for item in q_res:
		tmp = item[0].strftime('%Y-%m-%d')
		xy[tmp] = item[1]
	data = {"x": list(xy.keys()), "y": list(xy.values())}
	return jsonify(data), 201

def user_last_upd(mysql):
    context_maxlen = 50
    cursor = mysql.connection.cursor()

    tbl = []

    query = "SELECT scenario_key, context, date_recorded FROM scenarios "
    query += "WHERE username = %s "
    query += "AND deleted = 0 ORDER BY date_recorded desc limit 10 "
    cursor.execute(query, (session['username'],))

    q_res = cursor.fetchall()
    for item in q_res:
    	rec = {}
    	rec['scenario_key'] = item[0]
    	if len(item[1]) > context_maxlen :
    		rec['context'] = get_left_n_chars_until_space(item[1], context_maxlen) + '...'
    	else:
    		rec['context'] = item[1]
    	rec['last_update'] = item[2].strftime("%Y-%m-%d %H:%M:%S")
    	tbl.append(rec)
    return jsonify(tbl), 201
