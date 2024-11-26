# models.py
from sqlalchemy import create_engine, Column, Integer, String, Text, Table, ForeignKey
from sqlalchemy.orm import declarative_base, relationship, sessionmaker
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin

Base = declarative_base()

location_activities = Table('location_activities', Base.metadata,
    Column('location_id', Integer, ForeignKey('locations.id'), primary_key=True),
    Column('activity_id', Integer, ForeignKey('activities.id'), primary_key=True)
)

class Location(Base):
    __tablename__ = 'locations'
    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False)
    description = Column(Text)
    address = Column(String(255))
    activities = relationship('Activity', secondary=location_activities, back_populates='locations')

class Activity(Base):
    __tablename__ = 'activities'
    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False, unique=True)
    locations = relationship('Location', secondary=location_activities, back_populates='activities')

user_locations = Table('user_locations', Base.metadata,
    Column('user_id', Integer, ForeignKey('users.id')),
    Column('location_id', Integer, ForeignKey('locations.id'))
)
class User(Base, UserMixin):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True)
    username = Column(String(150), unique=True, nullable=False)
    password_hash = Column(String(128), nullable=False)
    # Relationship to track visited locations
    visited_locations = relationship('Location', secondary=user_locations, backref='visitors')

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

# Database connection
engine = create_engine('mysql+mysqlconnector://root:@localhost/database')
Session = sessionmaker(bind=engine)
