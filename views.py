import os
import datetime
from flask import Flask, render_template, request
from flask import redirect, jsonify, url_for, flash
from flask import send_from_directory
from werkzeug.utils import secure_filename
from flask import session as login_session
import random
import string

from sqlalchemy import create_engine, asc
from sqlalchemy.orm import sessionmaker
from models import Base, Category, Item, User

from oauth2client.client import flow_from_clientsecrets
from oauth2client.client import FlowExchangeError
import httplib2
import json
from flask import make_response
import requests

UPLOAD_FOLDER = 'uploads/'
ALLOWED_EXTENSIONS = set(['png', 'jpg', 'jpeg'])

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

CLIENT_ID = json.loads(
    open('client_secrets.json', 'r').read())['web']['client_id']

# Connect to Database and create database session
engine = create_engine('sqlite:///catalog.db')
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
session = DBSession()


# Check if the file extension is valid
def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


# Upload file
def upload_file(file):
    if file and allowed_file(file.filename):
        now = datetime.datetime.now()
        filename = ''.join([now.strftime("%Y%m%d%H%M_"),
                            secure_filename(file.filename)])
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
    elif not allowed_file(file.filename):
        flash('File type not allowed')
        return False
    return filename


@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'],
                               filename)


# HTML Endpoints
@app.route('/')
@app.route('/catalog')
def showCatalog():
    categories = session.query(Category).all()
    items = session.query(Item).order_by(Item.id.desc()).limit(6)
    return render_template('catalog.html',
                           categories=categories,
                           items=items)


@app.route('/catalog/<string:name>')
def showCategory(name):
    categories = session.query(Category).all()
    category = session.query(Category).filter_by(name=name).one()
    items = session.query(Item).filter_by(category_id=category.id).all()
    return render_template('category.html',
                           categories=categories,
                           category=category,
                           items=items)


@app.route('/catalog/new', methods=['GET', 'POST'])
def newCategory():
    if 'username' not in login_session:
        return redirect(url_for('showLogin'))

    categories = session.query(Category).all()
    if request.method == 'POST':
        file = request.files['file']
        name = request.form['name']
        description = request.form['description']

        # Check if the name is already used
        try:
            newCategory = session.query(Category).filter_by(
                name=name).one()
            if newCategory:
                flash('Category name already used')
                return redirect(request.url)
        except:
            pass

        if name == '' or description == '' or file.filename == '':
            flash('All fields are required')
            return redirect(request.url)

        filename = upload_file(file)

        if not filename:
            return redirect(request.url)

        category = Category(
            name=name,
            description=description,
            image=filename,
            user_id=login_session['user_id']
        )
        session.add(category)
        session.commit()
        flash('New category %s successfully created' % category.name)
        return redirect(url_for('showCategory', name=name))
    else:
        return render_template('newCategory.html', categories=categories)


@app.route('/catalog/<string:name>/edit', methods=['GET', 'POST'])
def editCategory(name):
    categories = session.query(Category).all()
    category = session.query(Category).filter_by(name=name).one()

    if 'username' not in login_session:
        return redirect(url_for('showLogin'))
    elif category.user_id != login_session['user_id']:
        return '''<script>
                  alert("You are not authorized!");
                  window.history.back();
                  </script>'''

    if request.method == 'POST':
        file = request.files['file']
        name = request.form['name']
        description = request.form['description']

        # Check if the name is already used
        try:
            newCategory = session.query(Category).filter_by(
                name=name).one()
            if newCategory.name != category.name:
                flash('Category name already used')
                return redirect(request.url)
        except:
            pass

        if file.filename != '':
            filename = upload_file(file)
            if filename:
                os.remove(os.path.join(app.config['UPLOAD_FOLDER'],
                                       category.image))
            else:
                return redirect(request.url)

        if name:
            category.name = name
        if description:
            category.description = description
        if file.filename != '':
            category.image = filename

        session.add(category)
        session.commit()
        flash('Category successfully edited ')
        return redirect(url_for('showCategory', name=name))
    else:
        return render_template('editCategory.html',
                               categories=categories, category=category)


@app.route('/catalog/<int:id>/delete', methods=['POST'])
def deleteCategory(id):
    category = session.query(Category).filter_by(id=id).one()
    if request.method == 'POST':
        os.remove(os.path.join(app.config['UPLOAD_FOLDER'], category.image))
        session.delete(category)
        flash('Category %s deleted successfully' % category.name)
        session.commit()
        return 'OK'


@app.route('/catalog/<string:name>/new', methods=['GET', 'POST'])
def newItem(name):
    if 'username' not in login_session:
        return redirect(url_for('showLogin'))

    categories = session.query(Category).all()
    category = session.query(Category).filter_by(name=name).one()
    if request.method == 'POST':
        file = request.files['file']
        name = request.form['name']
        description = request.form['description']

        # Check if the name is already used
        try:
            newItem = session.query(Item).filter_by(
                name=name, category_id=category.id).one()
            if newItem:
                flash('Item name already used')
                return redirect(request.url)
        except:
            pass

        if name == '' or description == '' or file.filename == '':
            flash('All fields are required')
            return redirect(request.url)

        filename = upload_file(file)

        if not filename:
            return redirect(request.url)

        item = Item(
            name=name,
            image=filename,
            description=description,
            category_id=category.id,
            user_id=login_session['user_id']
        )
        session.add(item)
        session.commit()
        flash('New item %s successfully created' % category.name)
        return redirect(url_for('showCategory', name=category.name))
    else:
        return render_template('newItem.html',
                               categories=categories, category=category)


@app.route('/catalog/<string:name>/<string:item>/edit',
           methods=['GET', 'POST'])
def editItem(name, item):
    categories = session.query(Category).all()
    category = session.query(Category).filter_by(name=name).one()
    item = session.query(Item).filter_by(name=item,
                                         category_id=category.id).one()
    if 'username' not in login_session:
        return redirect(url_for('showLogin'))
    elif item.user_id != login_session['user_id']:
        return '''<script>
                  alert("You are not authorized!");
                  window.history.back();
                  </script>'''

    if request.method == 'POST':
        file = request.files['file']
        name = request.form['name']
        description = request.form['description']

        # Check if the name is already used
        try:
            newItem = session.query(Item).filter_by(
                name=name, category_id=category.id).one()
            if newItem.name != item.name:
                flash('Item name already used')
                return redirect(request.url)
        except:
            pass

        if file.filename != '':
            filename = upload_file(file)
            if filename:
                os.remove(os.path.join(app.config['UPLOAD_FOLDER'],
                                       item.image))
            else:
                return redirect(request.url)

        if name:
            item.name = name
        if description:
            item.description = description
        if file.filename != '':
            item.image = filename

        session.add(item)
        session.commit()
        flash('Item successfully edited ')
        return redirect(url_for('showCategory', name=category.name))
    else:
        return render_template('editItem.html',
                               categories=categories,
                               category=category,
                               item=item)


@app.route('/catalog/<string:name>/<int:id>/delete', methods=['POST'])
def deleteItem(name, id):
    item = session.query(Item).filter_by(id=id).one()
    if request.method == 'POST':
        os.remove(os.path.join(app.config['UPLOAD_FOLDER'], item.image))
        session.delete(item)
        flash('Item %s deleted successfully' % item.name)
        session.commit()
        return 'OK'


# Login functions
@app.route('/login')
def showLogin():
    categories = session.query(Category).all()
    state = ''.join(random.choice(string.ascii_uppercase + string.digits)
                    for x in range(32))
    login_session['state'] = state
    return render_template('login.html', STATE=state, categories=categories)


@app.route('/disconnect')
def disconnect():
    if 'provider' in login_session:
        if login_session['provider'] == 'google':
            gdisconnect()
        del login_session['user_id']
        del login_session['provider']
        flash("You have successfully been logged out")
        return redirect(url_for('showCatalog'))
    else:
        flash("You were not logged in")
        return redirect(url_for('showCatalog'))


@app.route('/gconnect', methods=['POST'])
def gconnect():
    # Validate state token
    if request.args.get('state') != login_session['state']:
        response = make_response(json.dumps('Invalid state parameter.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    # Obtain authorization code
    code = request.data

    try:
        # Upgrade the authorization code into a credentials object
        oauth_flow = flow_from_clientsecrets('client_secrets.json', scope='')
        oauth_flow.redirect_uri = 'postmessage'
        credentials = oauth_flow.step2_exchange(code)
    except FlowExchangeError:
        response = make_response(
            json.dumps('Failed to upgrade the authorization code.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Check that the access token is valid.
    access_token = credentials.access_token
    url = ('https://www.googleapis.com/oauth2/v1/tokeninfo?access_token=%s'
           % access_token)
    h = httplib2.Http()
    result = json.loads(h.request(url, 'GET')[1])
    # If there was an error in the access token info, abort.
    if result.get('error') is not None:
        response = make_response(json.dumps(result.get('error')), 500)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Verify that the access token is used for the intended user.
    gplus_id = credentials.id_token['sub']
    if result['user_id'] != gplus_id:
        response = make_response(
            json.dumps("Token's user ID doesn't match given user ID."), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Verify that the access token is valid for this app.
    if result['issued_to'] != CLIENT_ID:
        response = make_response(
            json.dumps("Token's client ID does not match app's."), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    stored_access_token = login_session.get('access_token')
    stored_gplus_id = login_session.get('gplus_id')
    if stored_access_token is not None and gplus_id == stored_gplus_id:
        response = make_response(json.dumps('User is already connected.'),
                                 200)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Store the access token in the session for later use.
    login_session['access_token'] = credentials.access_token
    login_session['gplus_id'] = gplus_id

    # Get user info
    userinfo_url = "https://www.googleapis.com/oauth2/v1/userinfo"
    params = {'access_token': credentials.access_token, 'alt': 'json'}
    answer = requests.get(userinfo_url, params=params)

    data = answer.json()

    login_session['username'] = data['name']
    login_session['picture'] = data['picture']
    login_session['email'] = data['email']
    login_session['provider'] = 'google'

    # Add user to database
    user_id = getUserID(login_session['email'])
    if not user_id:
        user_id = createUser(login_session)

    login_session['user_id'] = user_id

    output = ''
    output += '<h1>Welcome, '
    output += login_session['username']
    output += '!</h1>'
    output += '<img src="'
    output += login_session['picture']
    output += '">'
    # flash("you are now logged in as %s" % login_session['username'])
    return output


@app.route('/gdisconnect/')
def gdisconnect():
    access_token = login_session.get('access_token')
    if access_token is None:
        response = make_response(json.dumps('User not connected.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    url = '''https://accounts.google.com/
             o/oauth2/revoke?token=%s''' % login_session['access_token']
    h = httplib2.Http()
    result = h.request(url, 'GET')[0]
    if result['status'] == '200':
        del login_session['access_token']
        del login_session['gplus_id']
        del login_session['username']
        del login_session['email']
        del login_session['picture']
        response = make_response(json.dumps('Successfully disconnected.'), 200)
        response.headers['Content-Type'] = 'application/json'
        return response
    else:
        response = make_response(json.dumps(
                'Failed to revoke token for given user.',
                400))
        response.headers['Content-Type'] = 'application/json'
        return response


# User Helper Functions
def createUser(login_session):
    newUser = User(name=login_session['username'], email=login_session[
                   'email'], picture=login_session['picture'])
    session.add(newUser)
    session.commit()
    user = session.query(User).filter_by(email=login_session['email']).one()
    return user.id


def getUserInfo(user_id):
    user = session.query(User).filter_by(id=user_id).one()
    return user


def getUserID(email):
    try:
        user = session.query(User).filter_by(email=email).one()
        return user.id
    except:
        return None


if __name__ == '__main__':
    app.debug = True
    app.secret_key = ''.join(
                    random.choice(string.ascii_uppercase + string.digits)
                    for x in range(32))
    app.run(host='0.0.0.0', port=5000)
