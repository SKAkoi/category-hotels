from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from database_setup import Base, Category, Hotel

engine = create_engine('sqlite:///hotels1.db')

# Bind the engine to the metadata of the Base class so that the declaratives
# Can be accessed through a DBSession instance
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
session = DBSession()

# Create intial categories
beach = Category(name="Beach")
session.add(beach)
session.commit()

wine_country = Category(name="Wine Country")
session.add(wine_country)
session.commit()

spa = Category(name="Spa")
session.add(spa)
session.commit()

city_style = Category(name="City Style")
session.add(city_style)
session.commit()

family_fun = Category(name="Family Fun")
session.add(city_style)
session.commit()

pet_friendly = Category(name="Pet Friendly")
session.add(pet_friendly)
session.commit()

# Create initial hotels
hotel1 = Hotel(name="San Nicolas Resort",
                description="A boutique hotel in a cosmopolitan style",
                image="https://cdn1.tablethotels.com/media/ecs/global/magazine/story-images/050617/SanNicolas.jpg",
                location="Lefkada, Greece", category=beach)
session.add(hotel1)
session.commit()

hotel2 = Hotel(name="Hotel Healdsburg",
                description="Contemporary hotel deep in California Wine Country",
                image="https://d2v76fz8ke2yrd.cloudfront.net/media/ecs/global/magazine/story-images/051416/Healdsburg.jpg",
                location="Healdsburg, California", category=wine_country)
session.add(hotel2)
session.commit()

hotel3 = Hotel(name="Gaia Retreat & Spa",
                description="A stylish health retreat with fantastic countryside views and fabulous food",
                image="https://www.i-escape.com/gallery/149001_150000/149201_149300/149240.jpg",
                location="Byron Bay, Australia", category=spa)
session.add(hotel3)
session.commit()

hotel4 = Hotel(name="Hotel Americano",
                description="An ultra modern New York getaway",
                image="https://d2v76fz8ke2yrd.cloudfront.net/media/ecs/global/magazine/story-images/052116/Americano.jpg",
                location="Chelsea, New York", category=city_style)
session.add(hotel4)
session.commit()

hotel5 = Hotel(name="The Gascony Farmhouse",
                description="Set in glorious Gascony countryside, this hippy-deluxe 4-bedroom offers a pool and bucolic gardens",
                image="https://www.i-escape.com/gallery/162001_163000/162601_162700/162686.jpg",
                location="Tarbes, France", category=family_fun)
session.add(hotel5)
session.commit()

hotel6 = Hotel(name="XV Beacon",
                description="Chic city escape for your furry companion",
                image="https://cdn1.tablethotels.com/media/ecs/global/magazine/story-images/052017/XVBeacon.jpg",
                location="Boston, Massachusetts", category=pet_friendly)
session.add(hotel6)
session.commit()

print("hotels have been added")
