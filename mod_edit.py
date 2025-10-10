import common

from flask import render_template, url_for, request, session, redirect
# from flask import Flask, render_template, url_for, request, session, redirect, jsonify

def load(mysql, scenario_id):

	form_fld = ['scenario_id','scenario_key','source_id','start_chapter','start_verse',
			'end_chapter','end_verse','description','context','ethic_q','validated']

	cursor = mysql.connection.cursor()

	query = "SELECT " + ",".join(form_fld) + " FROM scenarios "
	query += " WHERE " + session['groupfilter'] + " and scenario_id = %s"
	# Test possibility of stack queries SQL injection
	# query = "select 1;select 2; select 3"
	cursor.execute(query, (scenario_id,))

	# Fetch one row
	q_res = cursor.fetchone()
	if q_res is None:
		return redirect(url_for('view'))
	else:
		q_res = common.list_remove_none(q_res)
		form_data = dict(zip(form_fld, q_res))
		form_data['username'] = session['username']
		form_data['version'] = ""
		if session['editor'] == 1:
			version_html = 'Version(s):'
			query = "SELECT scenario_id, date_recorded, username FROM scenarios WHERE scenario_key = %s";
			cursor.execute(query, (form_data['scenario_key'],))
			q_res2 = cursor.fetchall()
			if q_res2 is not None:
				version_html += '<FORM ID="versionForm" METHOD="GET">\n'
				version_html += '<TABLE class="table table-bordered border-primary">\n'
				version_html += '<TR><TD>Select</TD>\n'
				version_html += '<TD>DateTime</TD>\n'
				version_html += '<TD>Username</TD></TR>\n'
				for item in q_res2:
					version_html += '<TR><TD>'
					if str(item[0]) == scenario_id:
						version_html += 'Current'
					else:
						version_html += '<INPUT TYPE="RADIO" NAME="id" VALUE=' + str(item[0]) +'></TD>\n'
					version_html += '<TD>' + str(item[1]) + '</TD>\n'
					version_html += '<TD>' + item[2] + '</TD></TR>\n'
				version_html += '</TABLE>\n'
				version_html += '<INPUT TYPE=SUBMIT VALUE="Go">\n'
				version_html += '</FORM>\n'
			form_data['version'] = version_html

		# source_choices = get_choices(cursor, "sources", "source_id", "title", form_data['source_id'])
		query = "SELECT title FROM sources WHERE source_id = %s"
		cursor.execute(query, (form_data['source_id'],))
		q_res = cursor.fetchone()
		form_data['source_name'] = q_res[0]

		form_data['moral_actions'] = common.get_action_list(cursor, scenario_id, 'moral')
		form_data['immoral_actions'] = common.get_action_list(cursor, scenario_id, 'immoral')
		form_data['amoral_actions'] = common.get_action_list(cursor, scenario_id, 'amoral')

		if 'from_edit' in request.args:
			form_data['msg_bar'] = "Edited Record Saved!"
		else:
			form_data['msg_bar'] = "Editing a Previous Record"

		return render_template('edit.html', form_data=form_data, username=session['username'])

