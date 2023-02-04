from flask import Flask, url_for, redirect, render_template, request, flash, send_from_directory, get_flashed_messages
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import func
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash
from models import db, User, Post, Comment
import os, datetime
from nocache import nocache

app = Flask(__name__)
upload_folder = os.path.join(os.getcwd(), 'images')
app.config['SECRET_KEY'] = 'hello'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///db.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = upload_folder
db.init_app(app)
login_manager = LoginManager(app)
app.app_context().push()

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))
@app.route('/', methods=['GET', 'POST'])
def index():
    if current_user.is_authenticated:
        flash('user logged in!!')
        return redirect(url_for('home'))
    else:
        return redirect(url_for('login'))


@app.route('/login',methods=['GET','POST'])
def login():
    active = ['active','']
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    error = ''
    if request.method =='POST':
        try:
            user = User.query.filter_by(username = request.form['username']).first()
            if check_password_hash(user.password, request.form['password']):
                login_user(user)
                flash('user logged in!')
                return redirect(url_for('home'))
            else:
                error = 'password not correct'
        except:
            error = 'user not found'
        if error != "":
            flash(error)
        return render_template('login.html',active=active)
    else:
        return render_template('login.html', active=active)

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    error = ''
    active = ['','active']
    if request.method == 'POST':
        if request.form['password'] == request.form['confirm']:
            user = User(
                username = request.form['username'],
                password = generate_password_hash(request.form['password'])
            )
            try:
                db.session.add(user)
                db.session.commit()
                login_user(user)
                flash('user created!!')
                return redirect(url_for('home'))
            except:
                db.session.rollback()
                error = 'username already exist'
        else:
            error='passwords do not match'
    if error != "":
        flash(error)
    return render_template('signup.html',active=active)

@app.route('/home', methods=['GET', 'POST'])
@login_required
def home():
    active = ['active','','','']
    user = current_user
    result = Post.query.order_by(Post.time).all()
    return render_template('home.html',user=user, feed = result, active=active)

@app.route('/profile/<int:id>',methods=['GET','POST'])
@login_required
def profile(id):
    active = ['','','active','']
    user = User.query.filter_by(id=id).first()
    return render_template('profile.html', user=user,active=active)

@app.route('/followers/<int:id>')
@login_required
def followers(id):
    active = ['','','','']
    user = User.query.filter_by(id=id).first()
    return render_template('followers.html', user = user, active=active)

@app.route('/following/<int:id>')
@login_required
def following(id):
    active = ['','','','']
    user = User.query.filter_by(id=id).first()
    return render_template('following.html', user = user, active=active)

@app.route('/search', methods=['GET', 'POST'])
@login_required
def search(): 
    active = ['','active','','']
    results=[] 
    if request.method == 'POST':
        if request.form['search'] != "":
            results = User.query.filter(User.username.like('%'+request.form['search']+'%'))
    return render_template('search.html',results=results, user=current_user, active=active)

@app.route('/follow', methods=['POST'])
@login_required
def follow():
    user = User.query.filter_by(id=int(request.form['follow_id'])).first()
    current_user.follow(user)
    db.session.commit()
    flash('following '+user.username)
    return "following "+request.form['follow_id']
@app.route('/unfollow', methods=['POST'])
@login_required
def unfollow():
    user = User.query.filter_by(id=int(request.form['unfollow_id'])).first()
    current_user.unfollow(user)
    db.session.commit()
    flash('unfollowing '+user.username)
    return "unfollowing "+request.form['unfollow_id']

@app.route('/create_post', methods=['GET','POST'])
@login_required
def post():
    active = ['','','','active']
    error=""
    if request.method == 'POST':
        if 'image' not in request.files:
            error = 'No File Part'
        file = request.files['image']
        if file.filename == '':
            error = 'No File Selected'
        file_name = secure_filename(file.filename)
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], 'post', file_name))
        try:
            post = Post(
                title=request.form['title'],
                caption = request.form['caption'],
                user_id = current_user.id,
                image_url = file_name
            )
            db.session.add(post)
            db.session.commit()
            flash("Post Added!!")
            return redirect(url_for('home'))
        except:
            error = "error uploading post"
    if error != "":
        flash(error)
    return render_template('post.html', user=current_user, active=active)
@app.route('/editpost/<int:id>', methods=['GET','POST'])
@login_required
def editpost(id):
    active = ['','','','']
    post = Post.query.filter_by(pid=id).first()
    if request.method == 'POST':
        post.title = request.form['title']
        post.caption = request.form['caption']
        db.session.commit()
        flash('post updated!!')
        return redirect(url_for('profile',id=current_user.id))
    return render_template('edit_post.html',post=post, active=active)
@app.route('/deletepost/<int:id>')
@login_required
def deletepost(id):
    post = Post.query.filter_by(pid=id).first()
    db.session.delete(post)
    db.session.commit()
    flash('post with title '+post.title+' deleted!!')
    return redirect(url_for('profile', id=current_user.id))

@app.route('/edituser/<int:change_password>', methods=['GET','POST'])
@login_required
def edituser(change_password):
    active = ['','','','']
    user = current_user
    error = ''
    if request.method == 'POST':
        if change_password and user.username == request.form['username']:
            if check_password_hash(user.password, request.form['previous']):
                user.password = generate_password_hash(request.form['new'])
                db.session.commit()
                flash('password changed')
                return redirect(url_for('home'))
            else:
                error="previous password do not match"
        elif change_password and user.username != request.form['username']:
            error='problem with username'
        elif check_password_hash(user.password, request.form['previous'] ) :
            user.username = request.form['username']
            db.session.commit()
            flash('username changed')
            return redirect(url_for('home'))
        else:
            error="password do not match"
    if error != "":
        flash(error)
    return render_template('edit_user.html',user=user,error=error,change_password=change_password, active=active)
@app.route('/deleteuser', methods=['POST'])
def deleteuser():
    user = User.query.filter_by(id = current_user.id).first()
    if check_password_hash(user.password, request.form['password']):
        db.session.delete(user)
        db.session.commit()
        logout_user()
        flash('Account: '+user.username+' deleted!!')
        return redirect(url_for('login')) 
    else:
        flash('password not correct')
        return redirect(request.referrer)    

@app.route('/addcomment/<int:id>', methods=['POST'])
def addcomment(id):
    post = Post.query.filter_by(pid = id).first()
    comment = Comment(
        comment=request.form['comment'],
        pid = id,
        uid = current_user.id)    
    db.session.add(comment)
    db.session.commit()
    flash('you commented on post: '+post.title)
    return redirect(request.referrer)
@app.route('/deletecomment/<int:id>/<int:pid>')
def deletecomment(id,pid):
    comment = Comment.query.filter_by(id = id).first()
    db.session.delete(comment)
    db.session.commit()
    return redirect(request.referrer)

@app.route('/addlike/<int:id>')
def addlike(id):
    post = Post.query.filter_by(pid = id).first()
    user = current_user.liked.append(post)
    db.session.commit()
    return redirect(request.referrer)  
@app.route('/removelike/<int:id>')
def removelike(id):
    post = Post.query.filter_by(pid=id).first()
    user = current_user.liked.remove(post)
    db.session.commit()
    return redirect(request.referrer)

@app.route('/getfile/<filename>')
@nocache
@login_required
def getfile(filename):
    return send_from_directory(os.path.join(app.config['UPLOAD_FOLDER'], 'post'), filename)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

if __name__ == "__main__":
    app.run(debug=True)