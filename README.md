# Category Hotels
--------------------------------------------

## Intro
This project uses the flask framework to build a simple web application
that showcases a list of hotels within a variety of categories, as well as
providing user registration and authentication via Google (oauth2)

### Setting up the VM
1. Install [Python](https://www.python.org)
2. Install [Virtual Box](https://www.virtualbox.org/wiki/Downloads)
3. Install and set up [Vagrant](https://www.vagrantup.com/downloads.html)
4. Start up the Virtual Machine after configuring Vagrant

### Running the project
1. Fork and clone this repository into your vagrant folder.
2. Run database_setup.py to initialize the database
3. Run loadinitialhotels.py to populate the database with initial entries.
4. Run hotels.py to start the application.
5. Point your browser to http://localhost:5000/ to view and interact with the project.

### Accessing data via the Category Hotels API
This project comes with JSON endpoints that allow you to query the database:
1. All categories - http://localhost:5000/categories/JSON
2. All hotels - http://localhost:5000/allhotels/JSON
3. Hotels belonging to a specific category - http://localhost:5000/categories/category_id/hotels/JSON
4. A specific hotel's info - http://localhost:5000/categories/int:category_id/hotel/int:hotel_id/JSON

Note that category_id and hotel_id refer to specific id values that correspond to the
category and hotel you are querying.
