from flask import session

def topbar(pagename):
    editor = session['editor']
    username = session['username']

    html = '''<nav class="navbar navbar-expand-sm navbar-dark bg-success">
    <div class="container-fluid">
        <ul class="navbar-nav">
            '''
    if pagename in {"view", "profile"}:
        if editor == 1:
            html += '''<li class="nav-item">
                <a class="nav-link active" href="admin">Admin Dashboard</a>
            </li>
        '''

    if pagename == "edit":
        html += '''<li class="nav-item">
                <a class="nav-link active" href="view">Back to List of Scenarios</a>
            </li>
        '''
    elif pagename == "profile":
        html += '''<li class="nav-item">
                <a class="nav-link active" href="view">List of Scenarios</a>
            </li>
        '''

    html += f'''</ul>
    <ul class="navbar-nav navbar-right">
      <span class="navbar-text">User: <A HREF="/profile">{username}</A>&nbsp;&nbsp;</span>
      <li class="nav-item">
        <a class="nav-link active" href="logout">Logout</a>
      </li>
    </ul>
  </div>
</nav>
    '''
    return html