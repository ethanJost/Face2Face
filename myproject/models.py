# models.py
from sqlalchemy import create_engine, Column, Integer, String, Text, Table, ForeignKey
from sqlalchemy.orm import declarative_base, relationship, sessionmaker
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from stored_procedures import get_db_connection

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
class User(UserMixin):
    def __init__(self, id, username, password_hash):
        self.id = id
        self.username = username
        self.password_hash = password_hash
    
    def load_user(user_id):
        conn = get_db_connection()
        cur = conn.cursor(dictionary=True)
        cur.execute('SELECT * FROM users WHERE id = %s', (user_id,))
        user = cur.fetchone()
        conn.close()
        if user:
            return User(user['id'], user['username'], user['password_hash'])
        return None

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

# Database connection
engine = create_engine('mysql+mysqlconnector://root:@localhost/database')
Session = sessionmaker(bind=engine)
