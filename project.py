from flask import Flask, render_template, request, redirect
from flask import jsonify, url_for, flash
from sqlalchemy import create_engine, asc, desc
from sqlalchemy.orm import sessionmaker
from database_setup import Categories, Base, Items, User
from flask import session as login_session
import random
import string
from oauth2client.client import flow_from_clientsecrets
from oauth2client.client import FlowExchangeError
import httplib2
import json
from flask import make_response
import requests

app = Flask(__name__)

# get client id from client_secrets.json file.
CLIENT_ID = json.loads(
    open('client_secrets.json', 'r').read())['web']['client_id']
APPLICATION_NAME = "Catalog App Application"


# Connect to Database and create database session
engine = create_engine('sqlite:///catalogapp.db')
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
session = DBSession()


# Name        : showLogin
# Description : Create a uniqe token for every user to prevent forgery.
# Parameters  : none
# Return      : current state. (login_session['state'])
@app.route('/login')
def showLogin():
    state = ''.join(random.choice(string.ascii_uppercase + string.digits)
                    for x in xrange(32))
    login_session['state'] = state
    return render_template('login.html', STATE=state)


# Name        : gconnect
# Description : provide secure login to user using their google+ account.
# Parameters  : none
# Return      : user info from google+ account(name, email, pitcure)
@app.route('/gconnect', methods=['POST'])
def gconnect():
    # check if the state token is valid
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
        print "Token's client ID does not match app's."
        response.headers['Content-Type'] = 'application/json'
        return response

    stored_credentials = login_session.get('credentials')
    stored_gplus_id = login_session.get('gplus_id')
    if stored_credentials is not None and gplus_id == stored_gplus_id:
        response = make_response(
                            json.dumps('Current user is already connected.'),
                            200)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Store the access token in the session for later use.
    login_session['credentials'] = credentials
    login_session['gplus_id'] = gplus_id

    # Get user info
    userinfo_url = "https://www.googleapis.com/oauth2/v1/userinfo"
    params = {'access_token': credentials.access_token, 'alt': 'json'}
    answer = requests.get(userinfo_url, params=params)

    data = answer.json()

    login_session['username'] = data['name']
    login_session['picture'] = data['picture']
    login_session['email'] = data['email']

    # See if a user exists, if it doesn't make a new one

    output = ''
    output += '<h1>Welcome, '
    output += login_session['username']
    output += '!</h1>'
    output += '<img src="'
    output += login_session['picture']
    output += ' " style = "width: 300px; height: 300px;border-radius: "
                "150px;-webkit-border-radius: 150px;-moz-border-radius: "
                "150px;"> '
    flash("you are now logged in as %s" % login_session['username'])
    print "done!"
    return output


# Name        : gdisconnect
# Description : provide secure logout from the app, and reset user's session.
# Parameters  : none
# Return      : none
@app.route('/gdisconnect')
def gdisconnect():
        # Only disconnect a connected user.
    credentials = login_session.get('credentials')
    if credentials is None:
        response = make_response(
            json.dumps('Current user not connected.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    access_token = credentials.access_token
    url = 'https://accounts.google.com/o/oauth2/revoke?token=%s' % access_token
    h = httplib2.Http()
    result = h.request(url, 'GET')[0]

    if result['status'] == '200':
        # Reset the user's sesson.
        del login_session['credentials']
        del login_session['gplus_id']
        del login_session['username']
        del login_session['email']
        del login_session['picture']
        
        response = make_response(json.dumps('Successfully disconnected.'), 200)
        response.headers['Content-Type'] = 'application/json'
        return response
        
    else:
        # For whatever reason, the given token was invalid.
        response = make_response(
            json.dumps('Failed to revoke token for given user.', 400))
        response.headers['Content-Type'] = 'application/json'
        return response


# Name        : appjson
# Description : provide json page to the app.
# Parameters  : none
# Return      : list of items with their id, name, description, and category.
@app.route('/json')
def appjson():
    list = []
    items = session.query(Items).all()
    for item in items:
        list.append({"name": item.name,
                     "id": item.id,
                     "description": item.description,
                     "category": item.categories.name,
        })
    return jsonify({"items": list})


# Name        : showCatalog
# Description : Show all the categories and new items.
# Parameters  : none
# Return      : categories, items.
@app.route('/')
@app.route('/catalog/')
def showCatalog():
    categories = session.query(Categories).order_by(asc(Categories.name))
    items = session.query(Items).order_by(desc(Items.id))
    return render_template('catalog.html', categories=categories, items=items)


# Name        : showCategories
# Description : Show all the items in selected category.
# Parameters  : categories_id
# Return      : categories, items, category.
@app.route('/catalog/<string:categories_id>/')
def showCategory(categories_id):
    categories = session.query(Categories).order_by(asc(Categories.name))
    category = session.query(Categories).filter_by(id=categories_id).one()
    items = session.query(Items).filter_by(categories=category).all()
    return render_template('catalog.html', categories=categories,
                            items=items, category=category)


# Name        : showItems
# Description : Show all the details about selected item.
# Parameters  : items_id.
# Return      : item.
@app.route('/item/<int:items_id>/')
def showItem(items_id):
    item = session.query(Items).filter_by(id=items_id).one()
    return render_template('item.html', item=item)


# Name        : addItem
# Description : addItem to the category.
# Parameters  : categories_id.
# Return      : category.
@app.route('/catalog/<int:categories_id>/add/', methods=['GET', 'POST'])
def addItem(categories_id):
    if 'username' not in login_session:
        return redirect('/login')
    category = session.query(Categories).filter_by(id=categories_id).one()
    if request.method == 'POST':
        newItem = Items(name=request.form['name'], 
                        description=request.form['description'], 
                        categories_id=categories_id)
        session.add(newItem)
        session.commit()
        flash('New Menu %s Item Successfully Created' % (newItem.name))
        return redirect(url_for('showCategory', categories_id=categories_id))
    else:
        return render_template('addItem.html', category=category)


# Name        : editItem
# Description : edit information to the item.
# Parameters  : items_id.
# Return      : item.
@app.route('/item/<int:items_id>/edit/', methods=['GET', 'POST'])
def editItem(items_id):
    if 'username' not in login_session:
        return redirect('/login')
    editedItem = session.query(Items).filter_by(id=items_id).one()
    if request.method == 'POST':
        if request.form['name']:
            editedItem.name = request.form['name']
        if request.form['description']:
            editedItem.description = request.form['description']
        session.add(editedItem)
        session.commit()
        flash('Menu Item Successfully Edited')
        return redirect(url_for('showItem', items_id=items_id))
    else:
        return render_template('edititem.html', item=editedItem)


# Name        : deleteItem
# Description : delete item from the category.
# Parameters  : items_id.
# Return      : item.
@app.route('/item/<int:items_id>/delete/', methods=['GET', 'POST'])
def deleteItem(items_id):
    if 'username' not in login_session:
        return redirect('/login')
    itemToDelete = session.query(Items).filter_by(id=items_id).one()
    categories_id = itemToDelete.categories.id
    if request.method == 'POST':
        session.delete(itemToDelete)
        session.commit()
        flash('Menu Item Successfully Deleted')
        return redirect(url_for('showCategory', categories_id=categories_id))
    else:
        return render_template('deleteitem.html', item=itemToDelete)


if __name__ == '__main__':
    app.secret_key = 'super_secret_key'
    app.debug = True
    app.run(host='0.0.0.0', port=8000)
