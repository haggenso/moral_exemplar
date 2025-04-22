import re
import html
import hashlib
from decouple import config
from flask import Flask, render_template, url_for, request, session, redirect, jsonify
from flask_mysqldb import MySQL

action_count = 5

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
			action_id = item[0]
			action_description = item[1]
			action_confidence = item[2]
		else:
			action_id = ""
			action_description = ""
			action_confidence = "1.00"

		action_num = '{:02d}'.format(i+1)

		action_html += 'Action' + action_num + ':<BR>\n'
		action_html += '<INPUT TYPE="hidden" NAME="lst_' + moral_status + action_num + '_id"'
		action_html += ' VALUE="' + action_id + '"/>\n'
		action_html += '<TEXTAREA NAME="lst_' + moral_status + action_num + '_desc" ROWS="4"'
		action_html += ' COLS="30" STYLE="overflow:auto">\n'
		action_html += action_description + '</TEXTAREA><BR>\n'
		action_html += '<LABEL FOR="lst_' + moral_status + action_num + '_confidence">Confidence Level: </LABEL>\n'
		action_html += '<INPUT TYPE="NUMBER" NAME="lst_' + moral_status + action_num + '_confidence"'
		action_html += ' STEP="0.01" MIN="0" MAX="1" VALUE="' + action_confidence + '"/><BR>\n'

	return action_html

# Use the cursor variable globally so that the db session commit action can be done after this function returns
def save_action(form_data):
	global cursor

	action_insert=[]
	action_update=[]
	action_delete=[]
	for ele_key in form_data.keys():
		matches = re.match(r"lst_(\D+)(\d+)_desc", ele_key)
		# Match lst_(moral_status)(count)_desc
		if matches :
			action_desc = form_data[ele_key].strip()
			action_id_name = 'lst_' + matches.group(1) + matches.group(2) + '_id'
			action_confidence_name = 'lst_' + matches.group(1) + matches.group(2) + '_confidence'
			# print(action_id_name)

			# Some Content in Description
			if len(action_desc) > 0 :
				# action_id exists -> Update
				if len(form_data[action_id_name].strip()) > 0 :
					action_update.append((action_desc, matches.group(1), form_data[action_confidence_name], form_data[action_id_name]))
				# action_id missing -> New Record -> Insert
				else:
					action_insert.append((action_desc, matches.group(1), form_data[action_confidence_name]))
			# Empty Description with an action_id -> Delete
			elif len(form_data[action_id_name].strip()) > 0 :
				action_delete.append(form_data[action_id_name])

	for item in action_insert:
		query = "INSERT INTO actions (timestamp, scenario_id, "
		query += " action_description, moral_status, confidence) "
		query += " VALUES (curdate(), %s, %s, %s, %s)"
		cursor.execute(query, (form_data['scenario_id'], item[0], item[1], item[2]))
	for item in action_update:
		query = "UPDATE actions SET timestamp = curdate(), "
		query += " scenario_id = %s, action_description = %s, "
		query += " moral_status = %s, confidence = %s "
		query += " WHERE action_id = %s"
		cursor.execute(query, (form_data['scenario_id'], item[0], item[1], item[2], item[3]))
	for item in action_delete:
		query = "DELETE FROM actions WHERE action_id = %s"
		cursor.execute(query, (item,))

@app.route("/")
def index():
	if 'username' in session:
		return redirect(url_for('view'))
	else:
	    return redirect(url_for('login'))

@app.route('/login', methods=['GET','POST'])
def login():
    msg_bar = ""
    if request.method == 'POST' :
        cursor = mysql.connection.cursor()
        query = "select hashpass, groupfilter from usergroups, users "
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
	try:
		# out_str += app.config['MYSQL_DB']
		cursor = mysql.connection.cursor()

		id_key = 'scenario_id'
		fld_list = ['scenario_key','description','context']
		query = "SELECT " + id_key + "," + ",".join(fld_list) + " FROM scenarios "
		query += " WHERE " + session['groupfilter']
		query += " ORDER BY " + id_key
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
			scenario_id = item[0]
			item = item[1:]
			item = list_remove_none(item)
			item = list_html_esc(item)
			item.insert(0, "<A HREF='" + url_for('edit') + "?id=" + str(scenario_id) + "'>Edit</A>")
			list_of_html.append(list_in_TD(item))

		return render_template('view.html', list_of_html=list_of_html, username=session['username'])
		# return out_str + "<p>" + repr(scenarios) + "</p>\n"
		# return out_str + "<p>" + repr(list_of_html) + "</p>\n"

	except Exception as e:
		return (jsonify({'status': 'error', 'message': str(e)}))

@app.route("/edit", methods=['GET','POST'])
def edit():
	global cursor

	out_str = "<p>Hello</p>\n"
	try:
		scenario_id = str(request.args['id'])
		form_fld = ['scenario_id','scenario_key','source_id','start_chapter','start_verse',
				'end_chapter','end_verse','description','context','ethic_q']

		if request.method == 'POST' :
			form_data = dict(request.form)
			if scenario_id == "new" :

				cursor = mysql.connection.cursor()

				source_key = get_source_key(cursor, form_data['source_id'])
				scenario_key = source_key + 'C' + str(form_data['start_chapter']) + 'V' + str(form_data['start_verse'])
				if not((form_data['start_chapter']==form_data['end_chapter']) and (form_data['start_verse']==form_data['end_verse'])) :
					scenario_key += '-C' + str(form_data['end_chapter']) + 'V' + str(form_data['end_verse'])
				form_data['scenario_key'] = scenario_key

				query = "INSERT INTO scenarios (date_recorded, scenario_key, source_id, "
				query += " start_chapter, start_verse, end_chapter, end_verse, "
				query += " description, context, ethic_q) "
				query += " VALUES (curdate(), %s, %s, %s, %s, %s, %s, %s, %s, %s)"
				cursor.execute(query, (form_data['scenario_key'], form_data['source_id'], \
				form_data['start_chapter'], form_data['start_verse'], form_data['end_chapter'], form_data['end_verse'], \
				form_data['description'], form_data['context'], form_data['ethic_q']))

				cursor.execute("SELECT LAST_INSERT_ID()")
				record = cursor.fetchone()
				form_data['scenario_id'] = record[0]

				save_action(form_data)

				mysql.connection.commit()

				return redirect(url_for('edit') + "?id=" + str(form_data['scenario_id'])+"&from_new=")

				#source_choices = get_choices(cursor, "sources", "source_id", "title", -1)

				# form_data['msg_bar'] = "New Record Added!"
				# return render_template('edit.html', form_data=form_data, source_choices=source_choices)

				# return "Save to be impelemented! form_data:" + repr(form_data)
			elif scenario_id.isdigit() :

				cursor = mysql.connection.cursor()

				source_key = get_source_key(cursor, form_data['source_id'])
				scenario_key = source_key + 'C' + str(form_data['start_chapter']) + 'V' + str(form_data['start_verse'])
				if not((form_data['start_chapter']==form_data['end_chapter']) and (form_data['start_verse']==form_data['end_verse'])) :
					scenario_key += '-C' + str(form_data['end_chapter']) + 'V' + str(form_data['end_verse'])
				form_data['scenario_key'] = scenario_key
				# scenario_key = form_data['scenario_key']

				query = "UPDATE scenarios set date_recorded = curdate(), "
				query += " scenario_key = %s, source_id = %s, "
				query += " start_chapter = %s, start_verse = %s, "
				query += " end_chapter = %s, end_verse = %s, "
				query += " description = %s, context = %s, ethic_q = %s "
				query += " where scenario_id = %s "
				# print (query % (form_data['scenario_key'], form_data['source_id'], \
				# form_data['start_chapter'], form_data['start_verse'], form_data['end_chapter'], form_data['end_verse'], \
				# form_data['description'], form_data['context'], form_data['ethic_q'], form_data['scenario_id']))

				cursor.execute(query, (form_data['scenario_key'], form_data['source_id'], \
				form_data['start_chapter'], form_data['start_verse'], form_data['end_chapter'], form_data['end_verse'], \
				form_data['description'], form_data['context'], form_data['ethic_q'], form_data['scenario_id']))

				save_action(form_data)

				mysql.connection.commit()

				return redirect(url_for('edit') + "?id=" + str(form_data['scenario_id'])+"&from_edit=")

				# source_choices = get_choices(cursor, "sources", "source_id", "title", -1)

				# form_data['msg_bar'] = "Edited Record Saved!"
				# return render_template('edit.html', form_data=form_data, source_choices=source_choices)

				#return "Update to be impelemented! scenario_id: " + form_data['scenario_id'] + " form_data:" +  repr(form_data)

		elif scenario_id == "new" :
			form_data = {}
			form_data['scenario_id'] = scenario_id

			cursor = mysql.connection.cursor()
			source_choices = get_choices(cursor, "sources", "source_id", "title", -1)

			form_data['moral_actions'] = get_action_list(cursor, scenario_id, 'moral')
			form_data['immoral_actions'] = get_action_list(cursor, scenario_id, 'immoral')
			form_data['amoral_actions'] = get_action_list(cursor, scenario_id, 'amoral')

			form_data['msg_bar'] = "Adding a New Record"
			return render_template('edit.html', form_data=form_data, source_choices=source_choices)

			# return "New record to be impelemented!"

		elif scenario_id.isdigit() :
			# out_str += app.config['MYSQL_DB']
			cursor = mysql.connection.cursor()

			query = "SELECT " + ",".join(form_fld) + " FROM scenarios WHERE scenario_id = %s"
			# Test possibility of stack queries SQL injection
			# query = "select 1;select 2; select 3"
			cursor.execute(query, (scenario_id,))

			# Fetch one row
			q_res = cursor.fetchone()
			q_res = list_remove_none(q_res)
			form_data = dict(zip(form_fld, q_res))

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

			return render_template('edit.html', form_data=form_data, source_choices=source_choices)

			# return "Edit function to be implemented! id: " + repr(form_data)
			# return "Edit function to be implemented! id: " + repr(request.args['id'])
		else:
			return out_str

	except Exception as e:
		return (jsonify({'status': 'error', 'message': str(e)}))

if __name__ == '__main__':
	app.run()
