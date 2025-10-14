from datetime import date, timedelta
from flask import jsonify, request

def api(mysql, api_type):
	if api_type == 'test':
		return test()
	elif api_type == 'daily_update':
		return daily_update(mysql)
	elif api_type == 'source_update':
		return 	source_update(mysql)
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
		tbl.append(rec)
	return jsonify(tbl), 201

"""
select count(scenario_id) from scenarios s
where s.date_recorded < CONVERT('2025-10-10', DATE)
and s.validated = 1
"""