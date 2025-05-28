import re
import html
import hashlib
from decouple import config
from flask import Flask, render_template, url_for, request, session, redirect, jsonify
from flask_mysqldb import MySQL

action_count = 5

like6lvl = ['Strongly Disagree',
	'Disagree',
	'Somewhat Disagree',
	'Somewhat Agree',
	'Agree',
	'Strongly Agree']

app = Flask(__name__)
# Set the secret key to some random bytes. Keep this really secret!
app.secret_key = config('session_key')

app.config['DEBUG'] = True
app.config['TESTING'] = True
app.config['PROPAGATE_EXCEPTIONS'] = True

app.config['MYSQL_HOST'] = config('mariadb_host')
app.config['MYSQL_USER'] = config('mariadb_user')
app.config['MYSQL_PASSWORD'] = config('mariadb_pass')
app.config['MYSQL_DB'] = config('mariadb_db')

mysql = MySQL(app)

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
		if item[0] == select_value :
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

# Use the cursor variable globally so that the db session commit action can be done after this function returns
def save_action(form_data):
	global cursor

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

@app.route("/")
def index():
	return render_template('index.html')

@app.route('/login', methods=['GET','POST'])
def login():
    msg_bar = ""
    if request.method == 'POST' :
        cursor = mysql.connection.cursor()
        query = "select hashpass, groupfilter, editor from usergroups, users "
        query += " where usergroups.group_id = users.group_id "
        query += " and username = %s"
        cursor.execute(query, (request.form['username'],))
        q_res = cursor.fetchone()
        if q_res is None:
            msg_bar = "Wrong Username!"
            return render_template('login.html', msg_bar=msg_bar)
        else:
            passwd = request.form['passwd']
            passwd = hashlib.sha256(passwd.encode()).hexdigest()

            if passwd == q_res[0]:
                session['username'] = request.form['username']
                session['groupfilter'] = q_res[1]
                session['editor'] = q_res[2]
                return redirect(url_for('view'))
            else:
                msg_bar = "Wrong Password!"
                return render_template('login.html', msg_bar=msg_bar)
    else:
        return render_template('login.html')

@app.route('/logout')
def logout():
	# remove the username from the session if it's there
	session.clear()
	return redirect(url_for('index'))

@app.route("/view")
def view():

	out_str = "<p>Hello</p>\n"
	if 'username' in session:
		try:
			# out_str += app.config['MYSQL_DB']
			cursor = mysql.connection.cursor()

			id_key = 'scenario_id'
			fld_list = ['scenario_key','description','context','validated']
			query = "SELECT " + id_key + "," + ",".join(fld_list) + " FROM scenarios "
			query += " WHERE deleted=0 and " + session['groupfilter']
			query += " ORDER BY source_id, start_chapter, start_verse"
			cursor.execute(query)

			# Fetch all rows
			scenarios = cursor.fetchall()

			list_of_html = []
			header = fld_list
			header.insert(0, "Edit")
			header = list_html_esc(header)
			for i in range(len(header)) :
				header[i] = "<B>" + header[i] +"</B>"
			list_of_html.append(list_in_TD(header))
			for item in scenarios:
				item = list(item)
				scenario_id = item[0]
				item = item[1:]
				item[-1] = 'Validated' if item[-1] else 'Not Validated'
				item = list_remove_none(item)
				item = list_html_esc(item)
				item.insert(0, "<A HREF='" + url_for('edit') + "?id=" + str(scenario_id) + "'>Edit</A>")
				list_of_html.append(list_in_TD(item))

			return render_template('view.html', list_of_html=list_of_html, username=session['username'], editor=session['editor'])
			# return out_str + "<p>" + repr(scenarios) + "</p>\n"
			# return out_str + "<p>" + repr(list_of_html) + "</p>\n"

		except Exception as e:
			return (jsonify({'status': 'error', 'message': str(e)}))
	else:
		return redirect(url_for('login'))

@app.route("/edit", methods=['GET','POST'])
def edit():
	global cursor

	out_str = "<p>Hello</p>\n"
	if 'username' in session:
		try:
			scenario_id = str(request.args['id'])
			form_fld = ['scenario_id','scenario_key','source_id','start_chapter','start_verse',
					'end_chapter','end_verse','description','context','ethic_q','validated']

			if request.method == 'POST' :
				form_data = dict(request.form)
				cursor = mysql.connection.cursor()

				if scenario_id.isdigit() :
					query = "UPDATE scenarios SET deleted=1 WHERE scenario_id = %s"
					cursor.execute(query, (scenario_id,))
					query = "UPDATE actions SET deleted=1 WHERE scenario_id = %s"
					cursor.execute(query, (scenario_id,))

				source_key = get_source_key(cursor, form_data['source_id'])
				scenario_key = source_key + 'C' + str(form_data['start_chapter']) + 'V' + str(form_data['start_verse'])
				if not((form_data['start_chapter']==form_data['end_chapter']) and (form_data['start_verse']==form_data['end_verse'])) :
					scenario_key += '-C' + str(form_data['end_chapter']) + 'V' + str(form_data['end_verse'])
				form_data['scenario_key'] = scenario_key

				if form_data.get('validated', '') == '':
					form_data['validated']=0
				else:
					form_data['validated']=1

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

				save_action(form_data)

				mysql.connection.commit()

				if scenario_id.isdigit() :
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
					return redirect(url_for('edit') + "?id=" + str(form_data['scenario_id'])+"&from_new=")

				# source_choices = get_choices(cursor, "sources", "source_id", "title", -1)

				# return render_template('edit.html', form_data=form_data, source_choices=source_choices, username=session['username'])

				# return "Update to be impelemented! scenario_id: " + form_data['scenario_id'] + " form_data:" +  repr(form_data)

			elif scenario_id == "new" :
				form_data = {}
				form_data['scenario_id'] = scenario_id
				form_data['username'] = session['username']

				cursor = mysql.connection.cursor()
				source_choices = get_choices(cursor, "sources", "source_id", "title", -1)

				form_data['moral_actions'] = get_action_list(cursor, scenario_id, 'moral')
				form_data['immoral_actions'] = get_action_list(cursor, scenario_id, 'immoral')
				form_data['amoral_actions'] = get_action_list(cursor, scenario_id, 'amoral')

				form_data['msg_bar'] = "Adding a New Record"
				return render_template('edit.html', form_data=form_data, source_choices=source_choices, username=session['username'])

				# return "New record to be impelemented!"

			elif scenario_id.isdigit() :
				# out_str += app.config['MYSQL_DB']
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
					q_res = list_remove_none(q_res)
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

					source_choices = get_choices(cursor, "sources", "source_id", "title", form_data['source_id'])

					form_data['moral_actions'] = get_action_list(cursor, scenario_id, 'moral')
					form_data['immoral_actions'] = get_action_list(cursor, scenario_id, 'immoral')
					form_data['amoral_actions'] = get_action_list(cursor, scenario_id, 'amoral')

					if 'from_new' in request.args:
						form_data['msg_bar'] = "New Record Added!"
					elif 'from_edit' in request.args:
						form_data['msg_bar'] = "Edited Record Saved!"
					else:
						form_data['msg_bar'] = "Editing a Previous Record"

					return render_template('edit.html', form_data=form_data, source_choices=source_choices, username=session['username'])

				# return "Edit function to be implemented! id: " + repr(form_data)
				# return "Edit function to be implemented! id: " + repr(request.args['id'])
			else:
				return out_str

		except Exception as e:
			return (jsonify({'status': 'error', 'message': str(e)}))
	else:
		return redirect(url_for('login'))

if __name__ == '__main__':
	app.run()
