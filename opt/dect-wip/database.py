
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


class UserExtension(db.Model):
    extension = db.Column(db.String(20), primary_key=True)
    password = db.Column(db.String(20))
    name = db.Column(db.String(20))
    info = db.Column(db.String(20))
    token = db.Column(db.String(20))

    # Add a foreign key to reference the User model's primary key (id)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

    # Create a relationship with the User model
    user = db.relationship('User', backref='extensions', lazy=True)

class TempExtension(db.Model):
    extension = db.Column(db.String(20), primary_key=True)
    password = db.Column(db.String(20))
    uid = db.Column(db.Integer)
    ppn = db.Column(db.Integer)


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(32), nullable=False)
    displayname = db.Column(db.String(32), nullable=False)
    password = db.Column(db.String(128), nullable=False)
    is_active = True
    is_authenticated = True

    def get_id(self): # used for flask-login
        return self.id