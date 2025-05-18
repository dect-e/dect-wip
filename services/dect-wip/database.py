
from dataclasses import dataclass
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

@dataclass
class UserExtension(db.Model):
    extension: str = db.Column(db.String(20), primary_key=True)
    password: str = db.Column(db.String(20))
    name: str = db.Column(db.String(20))
    info: str = db.Column(db.String(20))
    token: str = db.Column(db.String(20))
    public: bool = db.Column(db.Boolean, default=False, nullable=False)

    # Add a foreign key to reference the User model's primary key (id)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

    # Create a relationship with the User model
    user = db.relationship('User', backref='extensions', lazy=True)

@dataclass
class TempExtension(db.Model):
    extension: str = db.Column(db.String(20), primary_key=True)
    password: str = db.Column(db.String(20))
    uid: int = db.Column(db.Integer)
    ppn: int = db.Column(db.Integer)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(32), nullable=False)
    displayname = db.Column(db.String(32), nullable=False)
    password = db.Column(db.String(128), nullable=False)
    is_admin = db.Column(db.Boolean, default=False, nullable=False)
    is_active = True
    is_authenticated = True

    def get_id(self): # used for flask-login
        return self.id
