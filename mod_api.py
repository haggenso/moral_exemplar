from datetime import datetime, date, timedelta
from flask import jsonify, request

def api(mysql, api_type):
	if api_type == 'test':
		return test()
	elif api_type == 'daily_update':
		return daily_update(mysql)
	else:
		return jsonify({"error": "api_type error"}), 404

def test():
	data = request.get_json()
	return jsonify(data), 201

def daily_update(mysql):
	param = request.get_json()

	date_list = []
	x = []
	y = []

	# Calculate the date some days ago
	date_count = date.today() - timedelta(days=param['days'])

	for _ in range(param['days']):
		date_list.append(date_count.strftime('%Y-%m-%d'))
		date_count += timedelta(days=1)

	cursor = mysql.connection.cursor()

	query = "SELECT date(date_recorded), count(scenario_id) FROM scenarios "
	query += "WHERE date_recorded > DATE_SUB(NOW(), INTERVAL %s DAY) "
	query += "GROUP BY date(date_recorded)"
	cursor.execute(query, (param['days'],))

	q_res = cursor.fetchall()
	for item in q_res:
		# tmp = datetime.strptime(item[0], '%a, %d %b %Y %H:%M:%S %Z')
		x.append(item[0].strftime('%Y-%m-%d'))
		y.append(item[1])
	data = {"x": x, "y": y}
	return jsonify(data), 201

"""
select date(s.date_recorded), count(scenario_id) from scenarios s
where s.date_recorded > DATE_SUB(NOW(), INTERVAL 30 DAY)
group by date(s.date_recorded);

select count(scenario_id) from scenarios s
where s.date_recorded < CONVERT('2025-10-10', DATE)
and s.validated = 1
"""