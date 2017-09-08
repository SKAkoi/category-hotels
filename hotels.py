from flask import Flask, render_template, request, redirect, jsonify, url_for, flash
app = Flask(__name__)

from sqlalchemy import create_engine, asc
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm.exc import NoResultFound
from database_setup import Base, Hotel, Category, User

# imports to create anti-forgery token
from flask import session as login_session
import random, string

# imports for logging in via oauth(Google)
from oauth2client.client import flow_from_clientsecrets
from oauth2client.client import FlowExchangeError
import httplib2
import json
from flask import make_response
import requests

CLIENT_ID = json.loads(open('client_secret.json', 'r').read())['web']['client_id']
APPLICATION_NAME = "Hotels App"

# Connect to hotels database and create the database session
engine = create_engine('sqlite:///hotels1.db')
Base.metadata.bind = engine
DBSession = sessionmaker(bind=engine)
session = DBSession()


# Create state token to guard againt request forgery
# And then store it in the session for later validation
@app.route('/login')
def showLogin():
    state = ''.join(random.choice(string.ascii_uppercase + string.digits)
                for x in xrange(32))
    login_session['state'] = state
    return render_template('login.html', STATE=state)


# Authenticate via the user's Google account
@app.route('/glogin', methods=['POST'])
def glogin():
    # Validate state token
    if request.args.get('state') != login_session['state']:
        response = make_response(json.dumps('Invalid state parameter'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    # Obtain authorization code
    code = request.data

    try:
        # Upgrade the authorization code into a credentials object
        oauth_flow = flow_from_clientsecrets('client_secret.json', scope='')
        oauth_flow.redirect_uri = 'postmessage'
        credentials = oauth_flow.step2_exchange(code)
    except FlowExchangeError:
        response = make_response(
                        json.dumps('Failed to upgrade the authorization code.'),
                        401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Check that the access token is valid
    access_token = credentials.access_token
    url = ('https://www.googleapis.com/oauth2/v1/tokeninfo?access_token=%s' %
            access_token)
    h = httplib2.Http()
    result = json.loads(h.request(url, 'GET')[1])
    # If there was an error in the access token info, abort.
    if result.get('error') is not None:
        response = make_response(json.dumps(result.get('error')), 500)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Verify that the access token matches the intended user.
    gplus_id = credentials.id_token['sub']
    if result['user_id'] != gplus_id:
        response = make_response(
                    json.dumps("Token's user ID doesn't match given user ID"),
                    401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Verify that the access token is valid for this app
    if result['issued_to'] != CLIENT_ID:
        response = make_response(
                    json.dumps("Token's client ID does not match app's"), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Check to see if user is already logged in
    stored_access_token = login_session.get('access_token')
    stored_gplus_id = login_session.get('gplus_id')
    if stored_access_token is not None and gplus_id == stored_gplus_id:
        response = make_response(
                    json.dumps("Current user is already connected."), 200)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Store the access toekn in the session for later use.
    login_session['access_token'] = credentials.access_token
    login_session['gplus_id'] = gplus_id

    # Get the user's info
    userinfo_url = "https://www.googleapis.com/oauth2/v1/userinfo"
    params = {'access_token': credentials.access_token, 'alt': 'json'}
    answer = requests.get(userinfo_url, params=params)
    data = answer.json()
    login_session['username'] = data['name']
    login_session['picture'] = data['picture']
    login_session['email'] = data['email']

    # Check to see if the user exists. If not, then create a new user

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
    output += ' "style = "width:300px; height:300px;">'
    flash("you are now logged in as %s" % login_session['username'])
    print("done!")
    return output

# Logout the user by revoking their token and resetting the login session
@app.route('/logout')
def glogout():
    # Only disconnect a connected user
    access_token = login_session.get('access_token')
    if access_token is None:
        print('Access Token is None')
        response = make_response(json.dumps('Current user not connected'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    print('In glogout access toekn is %s', access_token)
    print('User name is: ')
    print(login_session['username'])

    #Execute HTTP GET request to revoke current token
    #access_toekn = credentials.access_token
    url = 'https://accounts.google.com/o/oauth2/revoke?token=%s' % login_session['access_token']
    h = httplib2.Http()
    result = h.request(url, 'GET')[0]
    print('result is')
    print(result)

    if result['status'] == '200':
        # Reset the user's session
        del login_session['access_token']
        del login_session['gplus_id']
        del login_session['username']
        del login_session['email']
        del login_session['picture']

        #response = make_response(json.dumps('Successfully disconnected.'), 200)
        #response.headers['Content-Type'] = 'application/json'
        #return response
        flash("You are now logged out. Sign in to your account.")
        return redirect(url_for('showAllCategories'))

    else:
        #For whatever reason, the given token was Invalid
        response = make_response(json.dumps('Failed to revoke token for given user.'), 400)
        response.headers['Content-Type'] = 'application/json'
        return response

# Create a new user and retrieve their email for logging them in
def createUser(login_session):
    newUser = User(name = login_session['username'],
                    email = login_session['email'],
                    picture = login_session['picture'])
    session.add(newUser)
    session.commit()
    user = session.query(User).filter_by(email = login_session['email']).one()
    return user.id

# Retrieve a user's email from the DB for use in permission handling
def getUserID(email):
    try:
        user = session.query(User).filter_by(email=email).one()
        return user.id
    except:
        return None


# Retrieve user's info from DB from the DB for use in permission handling later on
def getUserInfo(user_id):
    user = session.query(User).filter_by(id = user_id).one()
    return user





# Show all hotel categories
@app.route('/')
@app.route('/categories')
def showAllCategories():
    all_categories = session.query(Category).all()
    recent_hotels = session.query(Hotel).all()
    return render_template('home.html', all_categories=all_categories, recent_hotels=recent_hotels)

# Create a new category
@app.route('/addcategory', methods=['POST', 'GET'])
@app.route('/categories/addcategory', methods=['POST', 'GET'])
def addNewCategory():
    if 'username' not in login_session:
        return redirect('/login')
    if request.method == 'POST':
        new_category = Category(name=request.form['name'], user_id=login_session['user_id'])
        session.add(new_category)
        session.commit()
        flash('Successfully added %s as a new category' % new_category.name)
        return redirect(url_for('showAllCategories'))
    elif request.method == 'GET':
        return render_template('newcategory.html')

# Edit a category
@app.route('/categories/<category_id>/edit', methods=['GET', 'POST'])
def editCategory(category_id):
    category_to_edit = session.query(Category).filter_by(id = category_id).one()
    if 'username' not in login_session:
        return redirect('/login')
    if category_to_edit.user_id != login_session['user_id']:
        return "<script>function myFunction() {alert('You are not authorised to edit this category. Please create your own category in order to edit it. ');setTimeout(function() {window.location.href='/';}, 200);}</script><body onload='myFunction()''>"
    if request.method == 'POST':
        if request.form['name']:
            category_to_edit.name = request.form['name']
            session.add(category_to_edit)
            session.commit()
            flash('Category %s successfully edited' % category_to_edit.name)
            return redirect(url_for('showAllCategories'))
    else:
        return render_template('editcategory.html', category_to_edit=category_to_edit)

# Delete a category
@app.route('/categories/<category_id>/delete', methods=['GET', 'POST'])
def deleteCategory(category_id):
    category_to_delete = session.query(Category).filter_by(id = category_id).one()
    if 'username' not in login_session:
        return redirect('/login')
    if category_to_delete.user_id != login_session['user_id']:
        return "<script>function myFunction() {alert('You are not authorised to delete this category.');setTimeout(function() {window.location.href='/';}, 500);}</script><body onload='myFunction()''>"
    if request.method == 'POST':
        session.delete(category_to_delete)
        session.commit()
        flash('Successfully deleted %s' % category_to_delete)
        return redirect(url_for('showAllCategories'))
    else:
        return render_template('deletecategory.html', category_to_delete=category_to_delete)


# Show all the hotels for a given category
@app.route('/categories/<category_id>')
@app.route('/categories/<category_id>/hotels')
def showCategoryDetails(category_id):
    category = session.query(Category).filter_by(id=category_id).one()
    all_hotels = session.query(Hotel).filter_by(category_id=category_id).all()
    return render_template('categorydetail.html', category=category, all_hotels=all_hotels)

# Show the details of a given hotel
@app.route('/categories/<category_id>/<hotel_id>')
def showHotelDetails(category_id, hotel_id):
    hotel = session.query(Hotel).filter_by(id = hotel_id).one()
    category = session.query(Category).filter_by(id = category_id).one()
    return render_template('hotel.html', hotel=hotel, category=category)

# Create a new hotel
@app.route('/categories/<category_id>/hotels/addhotel', methods=['GET', 'POST'])
def addNewHotel(category_id):
    if 'username' not in login_session:
        return redirect('/login')
    #all_categories = session.query(Category).all()
    category = session.query(Category).filter_by(id=category_id).one()
    if login_session['user_id'] != category.user_id:
        return "<script>function myFunction() {alert('You are not authorised to add hotels to this category. Please create a category to add hotels to it');setTimeout(function() {window.location.href='/';}, 500);}</script><body onload='myFunction()''>"
    if request.method == 'POST':
        newHotel = Hotel(name = request.form['name'],
                        description = request.form['description'],
                        image = request.form['image_url'],
                        category_id = category_id,
                        location = request.form['location'],
                        user_id=category.user_id)
        session.add(newHotel)
        session.commit()
        flash('You have added %s as a new hotel' % newHotel.name)
        return redirect(url_for('showHotelDetails', category_id=category_id, hotel_id=newHotel.id))
    else:
        return render_template('newhotel.html')

# Edit a hotel
@app.route('/hotels/<hotel_id>/edit', methods=['GET', 'POST'])
def editHotel(hotel_id):
    if 'username' not in login_session:
        return redirect('/login')
    hotel_to_edit = session.query(Hotel).filter_by(id = hotel_id).one()
    all_categories = session.query(Category).all()
    category = session.query(Category).filter_by(id=hotel_to_edit.category.id).one()
    if login_session['user_id'] != category.user_id:
        return "<script>function myFunction() {alert('You are not authorised to edit this hotel. Please add your own hotel before you can edit it.');setTimeout(function() {window.location.href='/';}, 500);}</script><body onload='myFunction()''>"

    if request.method == 'POST':
        if request.form['name']:
            hotel_to_edit.name = request.form['name']
        if request.form['description']:
            hotel_to_edit.description = request.form['description']
        if request.form['image_url']:
            hotel_to_edit.image = request.form['image_url']
        if request.form['location']:
            hotel_to_edit.location = request.form['location']
        session.add(hotel_to_edit)
        session.commit()
        flash('Successfully edited %s' % hotel_to_edit.name)
        return redirect(url_for('showHotelDetails', category_id=hotel_to_edit.category.id, hotel_id=hotel_to_edit.id))
    else:
        return render_template('edithotel.html', hotel_to_edit=hotel_to_edit, all_categories=all_categories)


# Delete a hotel
@app.route('/categories/<int:category_id>/hotels/<int:hotel_id>/delete', methods=['GET', 'POST'])
def deleteHotel(category_id, hotel_id):
    if 'username' not in login_session:
        return redirect('/login')
    category = session.query(Category).filter_by(id = category_id).one()
    hotel_to_delete = session.query(Hotel).filter_by(id = hotel_id).one()
    if login_session['user_id'] != category.user_id:
        return "<script>function myFunction() {alert('You are not authorised to delete this hotel.');setTimeout(function() {window.location.href='/';}, 500);}</script><body onload='myFunction()''>"
    if request.method == 'POST':
        session.delete(hotel_to_delete)
        session.commit()
        flash('You have successfully deleted %s' % hotel_to_delete.name)
        return redirect(url_for('showCategoryDetails', category_id=category_id))
    else:
        return render_template('deletehotel.html', hotel_to_delete=hotel_to_delete)

# JSON API Endpoints to view Category and Hotel info
@app.route('/categories/JSON')
def categoriesJSON():
    categories = session.query(Category).all()
    return jsonify(categories = [c.serialize for c in categories])

@app.route('/allhotels/JSON')
def allhotelsJSON():
    all_hotels = session.query(Hotel).all()
    return jsonify(all_hotels = [a.serialize for a in all_hotels])

@app.route('/categories/<category_id>/hotels/JSON')
def categorydetailJSON(category_id):
    category = session.query(Category).filter_by(id = category_id).one()
    hotels = session.query(Hotel).filter_by(category_id = category_id).all()
    return jsonify(hotels = [h.serialize for h in hotels])

@app.route('/categories/<int:category_id>/hotel/<int:hotel_id>/JSON')
def hoteldetailJSON(category_id, hotel_id):
    hotel = session.query(Hotel).filter_by(id = hotel_id).one()
    return jsonify(hotel = hotel.serialize)


if __name__ == '__main__':
    app.secret_key = 'something'
    app.debug = True
    app.run(host = '0.0.0.0', port = 5000)
