import re
import html

action_count = 5

like6lvl = ['Strongly Disagree',
	'Disagree',
	'Somewhat Disagree',
	'Somewhat Agree',
	'Agree',
	'Strongly Agree']

def list_remove_none(in_list):
	return_list = []
	for item in in_list:
		if item is None:
			return_list.append("")
		else:
			return_list.append(item)
	return return_list

def list_html_esc(in_list):
	return_list = []
	for item in in_list:
		return_list.append(html.escape(str(item)))
	return return_list

def list_in_TD(in_list):
	return_html = ""
	for item in in_list:
		return_html += '<TD>' + item + '</TD>'
	return return_html

def get_choices(cursor, tbl_name, pri_key, field, select_value):

	query = "SELECT %s, %s FROM %s order by %s"	% (pri_key, field, tbl_name, pri_key)
	choices = cursor.execute(query)
	choices = cursor.fetchall()

	choice_list = []
	for item in choices :
		if str(item[0]) == str(select_value) :
			selected = " SELECTED"
		else:
			selected = ""
		choice = "<OPTION VALUE={}{}>{}</OPTION>".format(item[0], selected, item[1])
		choice_list.append(choice)

	return choice_list

def get_source_key(cursor, source_id):
	query = "SELECT source_key FROM sources "
	query += " where source_id = %s"
	cursor.execute(query, (source_id,))
	record = cursor.fetchone()
	return record[0]

def get_action_list(cursor, scenario_id, moral_status):
	action_html ='\n'

	query = "SELECT action_id, action_description, confidence FROM actions "
	query += " WHERE scenario_id = %s and moral_status = %s"
	cursor.execute(query, (scenario_id, moral_status))
	# Fetch rows
	q_res = cursor.fetchall()

	for i in range(action_count):

		if cursor.rowcount > i:
			item = list_remove_none(q_res[i])
			item = list_html_esc(item)
			# dict(zip(['action_id', 'action_description','action_confidence'] item))
			action_description = item[1]
			action_confidence = item[2]
		else:
			action_description = ""
			action_confidence = "0"

		action_num = '{:02d}'.format(i+1)
		if i > 0 :
			action_html += '<HR class="bg-primary border-primary border-2">\n'
		action_html += 'Action' + action_num + ':<BR>\n'
		action_html += '<TEXTAREA NAME="lst_' + moral_status + action_num + '_desc" ROWS="8"'
		action_html += ' COLS="30" STYLE="overflow:auto">\n'
		action_html += action_description + '</TEXTAREA><BR>\n'
		for idx in range(len(like6lvl)):
			confidence_value = round(idx*0.1,1)
			action_html += '<INPUT TYPE="RADIO" class="form-check-input" NAME="lst_' + moral_status + action_num + '_confidence"'
			action_html += ' VALUE=' + str(confidence_value)
			if abs(float(action_confidence) - confidence_value) < 0.01:
				action_html += ' CHECKED'
			action_html += '>'
			action_html += like6lvl[idx] +'<BR>\n'

	return action_html
