from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from flask import current_app
import datetime

db = SQLAlchemy()

ff = db.Table('ff',
    db.Column('uid',db.Integer, db.ForeignKey('User.id'), primary_key=True),
    db.Column('follower',db.Integer, db.ForeignKey('User.id'), primary_key=True)
)
like = db.Table(
    'like',
    db.Column('uid',db.Integer, db.ForeignKey('User.id'), primary_key=True),
    db.Column('pid',db.Integer, db.ForeignKey('Post.pid'), primary_key=True)
)

class User(UserMixin, db.Model):
    __tablename__ = 'User'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    username = db.Column(db.String, nullable=False, unique=True)
    password = db.Column(db.String, nullable=False)
    following = db.relationship('User', secondary=ff, backref='followers',
        primaryjoin=(id == ff.c.follower), secondaryjoin=(id == ff.c.uid))
    posts = db.relationship('Post', backref='user', cascade="all, delete-orphan")
    liked = db.relationship('Post',secondary=like, backref='likes')
    comments = db.relationship('Comment', backref='user', cascade="all, delete-orphan")

    def follow(self, user):
        self.following.append(user)
    def unfollow(self, user):
        self.following.remove(user)

class Post(db.Model):
    __tablename__ = 'Post'
    pid = db.Column(db.Integer, primary_key=True, autoincrement=True)
    title = db.Column(db.String, nullable=False)
    caption = db.Column(db.String)
    time = db.Column(db.DateTime(), default=datetime.datetime.now())
    image_url = db.Column(db.String)
    user_id = db.Column(db.Integer, db.ForeignKey('User.id', ondelete="CASCADE"))
    comments = db.relationship('Comment', backref='post', cascade="all, delete-orphan")

class Comment(db.Model):
    __tablename__ = "Comment"
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    pid = db.Column(db.Integer, db.ForeignKey('Post.pid', ondelete="CASCADE"))
    uid = db.Column(db.Integer, db.ForeignKey('User.id', ondelete="CASCADE"))
    comment = db.Column(db.String(200),nullable=False)
    time = db.Column(db.DateTime(), default=datetime.datetime.now())
