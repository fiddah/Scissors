from . import db
from flask_login import UserMixin

class User(UserMixin, db.Model):
    __tablename__ = 'user'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20),  nullable=False, unique=True)
    email = db.Column(db.String,  nullable=False, unique=True)
    password = db.Column(db.Text,  nullable=False,)
    confirmed = db.Column(db.Boolean, default=False)
    urls = db.relationship('Url', backref='user', lazy=True)

    def __repr__(self):
        return f'User: <{self.username}>'


class Url(db.Model):
    __tablename__ = 'url'
    id = db.Column(db.Integer, primary_key=True)
    long_url = db.Column(db.String())
    short_url = db.Column(db.String(10), unique=True)
    custom_url = db.Column(db.String(50), unique=True, default=None)
    clicks = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, server_default=db.func.now())
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)

    def __repr__(self):
        return f'Link: <{self.short_url}>'