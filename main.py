import mod_login
import mod_view
import mod_edit
import mod_api
import topbar

from decouple import config
from flask import Flask, render_template, url_for, request, session, redirect, jsonify
from flask_cors import CORS
from flask_mysqldb import MySQL

app = Flask(__name__)
CORS(app)
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

@app.route("/")
def index():
	return render_template('index.html')

@app.route('/login', methods=['GET','POST'])
def login():
	return mod_login.login(mysql)

@app.route('/logout')
def logout():
	# remove the username from the session if it's there
	session.clear()
	return redirect(url_for('index'))

@app.route("/view")
def view():
	if 'username' in session:
		try:
			return mod_view.view(mysql)
			# return out_str + "<p>" + repr(list_of_html) + "</p>\n"
		except Exception as e:
			return (jsonify({'status': 'error', 'message': str(e)}))
	else:
		return redirect(url_for('login'))

@app.route("/edit", methods=['GET','POST'])
def edit():
	if 'username' in session:
		try:
			scenario_id = str(request.args['id'])

			if request.method == 'POST' :
				return mod_edit.save(mysql, scenario_id)
				# return "Update to be impelemented! scenario_id: " + form_data['scenario_id'] + " form_data:" +  repr(form_data)
			elif scenario_id.isdigit() :
				return mod_edit.load(mysql, scenario_id)
			else:
				return "<p>Error!</p>\n"

		except Exception as e:
			return (jsonify({'status': 'error', 'message': str(e)}))
	else:
		return redirect(url_for('login'))

@app.route('/api/<path:api_type>', methods=['POST'])
def api(api_type):
	if 'username' in session:
		try:
			return mod_api.api(mysql, api_type)
			# return out_str + "<p>" + repr(list_of_html) + "</p>\n"
		except Exception as e:
			return (jsonify({'status': 'error', 'message': str(e)}))
	else:
		return jsonify({"error": "error"}), 404

@app.route("/admin")
def admin():
	if session['editor'] == 1:
		return render_template('admin.html', topbar = topbar.topbar("edit"))
	else:
		# Redirect back to the referring page
		referrer_url = request.referrer
		if referrer_url:
			return redirect(referrer_url)
		else:
			# Fallback if referrer is not available (e.g., direct access)
			return redirect(url_for('index'))

if __name__ == '__main__':
	app.run()
