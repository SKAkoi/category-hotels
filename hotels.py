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
from oauth2.client.client import FlowExchangeError
import httplib2
import json
from flask import make_response
import requests

CLIENT_ID =

# Connect to hotels database and create the database session
engine = create_engine('sqlite:///hotels.db')
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
        oauth_flow = flow_from_clientsecrets('client_secrets.json', scope='')
        oauth_flow.redirect_uri = 'postmessage'
        credentials = oauth_flow.step2_exchange(code)
    except FlowExchangeError:
        response = make_response(
                        json.dumps('Failed to upgrade the authorization code.'),
                        401))
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
    if result['user_id'] != google_id:
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
    data = answer.json
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


# Create a new user and retrieve their email for logging them in
def createUser(user_id):
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
        user = session.query(User).filter_by(login_session['email']).one()
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
    all_categories = session.query(Category).all().order_by(asc(Category.name))
    recent_hotels = session.query(Hotel).all().order_by(desc(Hotel.id)).limit(6)
    return render_template('home.html')

# Show the hotels for a given category
@app.route('/categories/<category_name>')
@app.route('/categories/<category_name>/hotels')
def showCategoryDetails(category_id):
    category = session.query(Category).filter_by(id = category_id).one()
    all_hotels = session.query(Hotel).filter_by(id = category_id).all()
    return render_template('categorydetail.html')

# Show the details of a given hotel
@app.route('/categories/<category_name>/<hotel_name>')
def showHotelDetails(hotel_id):
    hotel = session.query(Hotel).filter_by(id = hotel_id).one()
    category = session.query(Category).filter_by(id = category_id).one()
    return render_template('hotel.html')

# Create a new category
@app.route('/addcategory', methods=['POST'])
@app.route('/categories/addcategory', methods=['POST'])
def addNewCategory():
    if request.method == 'POST':
        new_category = Category(name = request.form['name'])
        session.add(new_category)
        session.commit()
        flash('Successfully added %s as a new category' % new_category.name)
        return redirect(url_for('showAllCategories'))
    else:
        return render_template('newcategory.html')

# Edit a category
@app.route('/categories/<category_name>/edit', methods=['GET', 'POST'])
def editCategory():
    category_to_edit = session.query(Category).filter_by(id = category_id).one()
    if request.method == 'POST':
        if request.form['name']:
            category_to_edit.name = request.form['name']
            session.add(category_to_edit)
            session.commit()
            flash('Category %s successfully edited' % category_to_edit.name)
            return redirect(url_for('showAllCategories'))
    else:
        return render_template('editcategory.html')

# Delete a category
@app.route('/categories/<category_name>/delete', methods=['GET', 'POST'])
def deleteCategory():
    category_to_delete = session.query(Category).filter_by(id = category_id).one()
    if request.method == 'POST':
        session.delete(category_to_delete)
        session.commit()
        flash('Successfully deleted %s' % category_to_delete)
        return redirect(url_for('showAllCategories'))
    else:
        return render_template('deletecategory.html')

# Create a new hotel
@app.route('/categories/<category_name>/hotels/addhotel', methods=['GET', 'POST'])
def addNewHotel(category_id):
    if request.method == 'POST':
        newHotel = Hotel(name = request.form['name'],
                        description = request.form['description'],
                        image = request.form['image_url'],
                        category = request.form['category'],
                        user = getUserInfo(login_session['email']))
        session.add(newHotel)
        session.commit()
        flash('You have added %s as a new hotel' % newHotel.name)
        return redirect(url_for('showHotelDetails'))
    else:
        return render_template('newhotel.html')



# Edit a hotel
@app.route('/categories/<category_name>/<hotel_name>/edit', methods=['GET', 'POST'])
def editHotel(category_id, hotel_id):
    category = session.query(Category).filter_by(id = category_id).one()
    hotel_to_edit = session.query(Hotel).filter_by(id = hotel_id).one()
    if request.method == 'POST':
        hotel_to_edit = request.form['name']
        session.add(hotel_to_edit)
        session.commit()
        flash('Successfully edited %s' % hotel_to_edit.name)
        return redirect(url_for('showHotelDetails'))
    else:
        return render_template('edithotel.html')


# Delete a hotel
@app.route('/categories/<int:category_id>/hotels/<int:hotel_id>/delete', methods=['GET', 'POST'])
def deleteHotel(category_id, hotel_id):
    category = session.query(Category).filter_by(id = category_id).one()
    hotel_to_delete = session.query(Hotel).filter_by(id = hotel_id).one()
    if request.method == 'POST':
        session.delete(hotel_to_delete)
        session.commit()
        flash('You have successfully deleted %s' % hotel_to_delete.name)
        return redirect(url_for('showCategoryDetails'))
    else:
        return render_template('deletehotel.html')

# JSON APIs to view Category and Hotel info
@app.route('/categories/JSON')
def categoriesJSON():

@app.route('/categories/<int:category_id>/hotel/JSON')
def hotelcategoryJSON(category_id):

@app.route('/categories/<int:category_id>/hotel/<int:hotel_id>/JSON')
def hoteldetailJSON(category_id, hotel_id):


if __name__ == '__main__':
    app.secret_key = 'something'
    app.debug = True
    app.run(host = '0.0.0.0', port = 5000)