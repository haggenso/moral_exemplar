import common
import topbar

import re
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

		return render_template('edit.html', form_data=form_data, topbar = topbar.topbar("edit"))

def save(mysql, scenario_id):

	form_data = dict(request.form)
	cursor = mysql.connection.cursor()

	if scenario_id.isdigit() :
		# First, delete old records
		query = "UPDATE scenarios SET deleted=1 WHERE scenario_id = %s"
		cursor.execute(query, (scenario_id,))
		query = "UPDATE actions SET deleted=1 WHERE scenario_id = %s"
		cursor.execute(query, (scenario_id,))

		# The following code actually works well, but
		# scenario_key is created from import data, should not be change
		"""
		source_key = get_source_key(cursor, form_data['source_id'])
		scenario_key = source_key + 'C' + str(form_data['start_chapter']) + 'V' + str(form_data['start_verse'])
		if not((form_data['start_chapter']==form_data['end_chapter']) and (form_data['start_verse']==form_data['end_verse'])) :
			scenario_key += '-C' + str(form_data['end_chapter']) + 'V' + str(form_data['end_verse'])
		form_data['scenario_key'] = scenario_key
		"""

		if form_data.get('validated', '') == '':
			form_data['validated']=0
		else:
			form_data['validated']=1

		# Second, Build a new record in TABLE scenarios
		query = "INSERT INTO scenarios (date_recorded, scenario_key, source_id, "
		query += " start_chapter, start_verse, end_chapter, end_verse, "
		query += " description, context, ethic_q, username, validated) "
		query += " VALUES (NOW(), %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"
		cursor.execute(query, (form_data['scenario_key'], form_data['source_id'], \
		form_data['start_chapter'], form_data['start_verse'], form_data['end_chapter'], form_data['end_verse'], \
		form_data['description'], form_data['context'], form_data['ethic_q'], session['username'], form_data['validated']))

		cursor.execute("SELECT LAST_INSERT_ID()")
		record = cursor.fetchone()
		form_data['scenario_id'] = record[0]

		# Third, insert all moral/immoral/amoral records into TABLE actions
		for ele_key in form_data.keys():
			matches = re.match(r"lst_(\D+)(\d+)_desc", ele_key)
			# Match lst_(moral_status)(count)_desc
			if matches :
				action_desc = form_data[ele_key].strip()
				action_confidence_name = 'lst_' + matches.group(1) + matches.group(2) + '_confidence'
				# action_id_name = 'lst_' + matches.group(1) + matches.group(2) + '_id'
				# print(action_id_name)

				# Some Content in Description
				if len(action_desc) > 0 :
					query = "INSERT INTO actions (timestamp, scenario_id, "
					query += " action_description, moral_status, confidence) "
					query += " VALUES (NOW(), %s, %s, %s, %s)"
					cursor.execute(query, (form_data['scenario_id'], action_desc, matches.group(1), form_data[action_confidence_name]))

		mysql.connection.commit()

		if form_data['next_unvalidated'] == "0":
			return redirect(url_for('edit') + "?id=" + str(form_data['scenario_id'])+"&from_edit=")
		else:
			query = "SELECT scenario_id FROM scenarios "
			query += " WHERE deleted = 0 AND validated = 0 "
			query += " AND source_id = %s AND start_chapter >= %s AND start_verse > %s "
			query += " ORDER BY source_id, start_chapter, start_verse limit 1 "
			cursor.execute(query, (form_data['source_id'], form_data['start_chapter'], form_data['start_verse']))
			q_res = cursor.fetchone()
			if q_res is None:
				return redirect(url_for('edit') + "?id=" + str(form_data['scenario_id'])+"&from_edit=")
			else:
				return redirect(url_for('edit') + "?id=" + str(q_res[0])+"&from_edit=")
	else:
		return "<p>Wrong scenario_id !</p>\n"
