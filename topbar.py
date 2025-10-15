from flask import session

def topbar(pagename):
    editor = session['editor']
    username = session['username']

    html = '''<nav class="navbar navbar-expand-sm navbar-dark bg-success">
    <div class="container-fluid">
        <ul class="navbar-nav">
            '''
    if pagename == "view":
        if editor == 1:
            html += '''<li class="nav-item">
                <a class="nav-link active" href="admin">Admin Dashboard</a>
            </li>
        '''
    elif pagename == "edit":
        html += '''<li class="nav-item">
                <a class="nav-link active" href="view">Back to List of Scenarios</a>
            </li>
        '''

    html += f'''</ul>
    <ul class="navbar-nav navbar-right">
      <span class="navbar-text">User: {username}&nbsp;&nbsp;</span>
      <li class="nav-item">
        <a class="nav-link active" href="logout">Logout</a>
      </li>
    </ul>
  </div>
</nav>
    '''
    return html