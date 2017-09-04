from sqlalchemy import Column, ForeignKey, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy import create_engine

Base = declarative_base()

class User(Base):
    __tablename__ = 'user'

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(250), nullable=False, server_default="Admin")
    email = Column(String(250), nullable=False, server_default="admin@mail.com")
    picture = Column(String(250))

class Category(Base):
    __tablename__ = 'category'

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(250), nullable=False)
    user_id = Column(Integer, ForeignKey('user.id'))
    user = relationship(User)

    @property
    def serialize(self):
        """Return hotel category data in seriablizable form"""
        return {
            'name' : self.name,
            'id' : self.id,
        }

class Hotel(Base):
    __tablename__ = 'hotel'

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(250), nullable=False)
    description = Column(String(500), nullable=False)
    image = Column(String(250))
    location = Column(String(250))
    category_id = Column(Integer, ForeignKey('category.id'))
    category = relationship(Category)
    user_id = Column(Integer, ForeignKey('user.id'))
    user = relationship(User)

    @property
    def serialize(self):
        """ Return the hotel data in a serializeable format """
        return {
            'name' : self.name,
            'id' : self.id,
            'description' : self.description,
            'image' : self.image,
            'category' : self.category,
            'location' : self.location,
        }

engine = create_engine('sqlite:///hotelswithusers.db')

Base.metadata.create_all(engine)
