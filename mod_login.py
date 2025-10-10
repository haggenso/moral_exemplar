import hashlib
from flask import render_template, url_for, request, session, redirect

def login(mysql):
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