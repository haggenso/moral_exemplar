import common

from flask import request, render_template, url_for, session

def view(mysql):
	cursor = mysql.connection.cursor()

	# form_data = dict(request.args)

	if 'source_id' in request.args:
		if request.args['source_id'].isdigit():
			source_id = request.args['source_id']
		else:
			source_id = "1"
	else:
		source_id = "1"
	source_choices = common.get_choices(cursor, "sources", "source_id", "title", source_id)

	id_key = 'scenario_id'
	fld_list = ['scenario_key','description','context','validated']
	query = "SELECT " + id_key + "," + ",".join(fld_list) + " FROM scenarios "
	query += " WHERE deleted=0 AND " + session['groupfilter']
	query += " AND source_id = %s "
	query += " ORDER BY source_id, start_chapter, start_verse"
	cursor.execute(query, (source_id, ))

	# Fetch all rows
	scenarios = cursor.fetchall()

	list_of_html = []
	header = ['Edit', 'Scenario Key','Desc.','Text','Validated']
	header = common.list_html_esc(header)
	for i in range(len(header)) :
		header[i] = "<B>" + header[i] +"</B>"
	list_of_html.append(common.list_in_TD(header))
	for item in scenarios:
		item = list(item)
		scenario_id = item[0]
		item = item[1:]
		item[-1] = 'Validated' if item[-1] else 'Not Validated'
		item = common.list_remove_none(item)
		item = common.list_html_esc(item)
		item.insert(0, "<A HREF='" + url_for('edit') + "?id=" + str(scenario_id) + "'>Edit</A>")
		list_of_html.append(common.list_in_TD(item))

	return render_template('view.html', source_choices=source_choices, list_of_html=list_of_html, username=session['username'], editor=session['editor'])
