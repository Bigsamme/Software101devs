from flask import Flask, render_template,url_for,request,redirect, flash
from flask_bootstrap import Bootstrap
from flask_ckeditor import CKEditor
from flask_login import LoginManager, login_required, login_user,logout_user, UserMixin,current_user,AnonymousUserMixin
from flask_sqlalchemy import SQLAlchemy
import gunicorn
import os
import datetime as dt
from functools import wraps
from werkzeug.security import gen_salt, generate_password_hash,check_password_hash
from datetime import datetime
from sqlalchemy.orm import relationship
from forms import RegisterForm, BlogPostForm, LoginForm, SearchForm, FileSubmit
import random
import string

def proper_user_required(func):
    @wraps(func)
    def decorated_function(*args, **kwargs):
        if current_user.username != kwargs.get("username"):
            return redirect(url_for('add_post'))
        return func(*args, **kwargs)
    return decorated_function

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get("FLASK_KEY")
app.config['UPLOAD_FOLDER'] = "static/images/profile_pics"
ALLOWED_EXTENSIONS = {'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif'}
ckeditor = CKEditor(app)
Bootstrap(app)



app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv("DB_URL", "sqlite:///blog_posts.db")
db = SQLAlchemy(app)

login_manager = LoginManager()
login_manager.init_app(app)

@login_manager.user_loader
def load_user(user_id):
    return User.query.filter_by(id = user_id).first()
    

class User(UserMixin, db.Model):
    __tablename__ = "users"
    id = db.Column( db.Integer, primary_key = True)
    username = db.Column( db.String(250), )
    email = db.Column( db.String(250),nullable=True)
    password = db.Column( db.String(250))
    registration_date = db.Column(db.String(100))
    profile_pic = db.Column(db.String(250))
    posts = relationship("BlogPosts", back_populates="author")
    post_history = relationship("UserPostHistory", back_populates="read_user")
    
class UserPostHistory(db.Model):
    __tablename__ = "user_post_history"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    post_id = db.Column(db.Integer, db.ForeignKey("blog_posts.id"))
    date_read = db.Column(db.DateTime, default=datetime.utcnow)

    read_user = relationship("User", back_populates="post_history")
    post = relationship("BlogPosts", back_populates="read_by_users")
class BlogPosts(db.Model):
    __tablename__ = "blog_posts"
    id = db.Column( db.Integer, primary_key = True)
    title = db.Column( db.String(250))
    description = db.Column( db. String(250))
    body = db.Column( db.Text)
    language = db.Column( db.String(250))
    type = db.Column( db.String(250))
    thumbnail = db.Column(db.String)
    views = db.Column(db.Integer)
    author_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    author = relationship("User", back_populates="posts")
    read_by_users = relationship("UserPostHistory", back_populates="post")


with app.app_context():
    db.create_all()



@app.route("/")
def home():
    posts = BlogPosts.query.all()
    posts = posts[:10]
    user = current_user
    random.shuffle(posts)
    if user.is_authenticated:
        history = UserPostHistory.query.filter_by(user_id = current_user.id).all()
    else:
        history = []
    return render_template("index.html", posts = posts,user= user, history = history)



@app.context_processor
def base():
    form = SearchForm()
    return dict(search_form = form)

@app.route("/support/about-us")
def about_us():
    return render_template('about-us.html')
@app.route('/login', methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("home"))
    form = LoginForm()
    if request.method == "GET":
        return render_template('login.html',form = form)
    else:
        email = request.form['email']
        user = User.query.filter_by( email = email).first()
        if user:
            password = form.password.data
            if check_password_hash(user.password, password):
                login_user(user)
                return redirect(url_for('home'))
            else:
                flash("Password is incorrect", "error")
                return render_template("login.html", form = form)
        else:
            flash("A User with this email not found", "error")
            return render_template('login.html', form = form)
            

@app.route('/users/<username>/dashboard')
@proper_user_required
def dashboard(username):
    if not current_user.is_authenticated:
        return redirect(url_for("login"))
    user = User.query.filter_by(username = username).first()
    user_posts = BlogPosts.query.filter_by(author_id = user.id).all()
    return render_template("dashboard.html", user = user,user_posts = user_posts)


@app.route("/add_post", methods=["GET", "POST"])
def add_post():
    if not current_user.is_authenticated:
        return redirect(url_for('login'))
    form = BlogPostForm()
    if request.method == "GET":
        return render_template('add-post.html', form = form)
    
    lower_letters = string.ascii_lowercase
    upper_letters = string.ascii_uppercase
    file_path = ""
    for letter in range(50):
        file_path += random.choice(upper_letters)
        file_path += random.choice(lower_letters)
    file = request.files['thumbnail']
    type_ = file.filename.split(".")[1]
    file_name = '.'.join([file_path,type_])
    file.save(os.path.join(app.config['UPLOAD_FOLDER'], file_name))
    new_post = BlogPosts(
        title=form.title.data,
        description=form.description.data,
        body=form.body.data,
        language=form.language.data,
        thumbnail = file_name,
        type=form.type.data,
        views = 0,
        author=current_user  # Set the author to the current logged-in user
    )


    # Then, add the new post to the database
    db.session.add(new_post)
    db.session.commit()
    return redirect(url_for('home'))
    
    
@app.route('/show_post/<post_title>/<int:post_id>')
def show_post(post_id,post_title):
    post = BlogPosts.query.filter_by(id = post_id).first()
    post.views = post.views + 1
    user = current_user
    read_history_entry = UserPostHistory(read_user=user, post=post)
    db.session.add(read_history_entry)
    db.session.add(post)
    db.session.commit()
    return render_template("post.html", post = post)

@app.route('/register', methods = ["GET","POST"])
def register():
    form = RegisterForm()
    if request.method == "GET":
        return render_template('register.html', form = form)
    elif request.method == "POST":
        user = User.query.filter_by(username = request.form["username"]).first()
        if user:
            flash("this username already exist")
            return render_template("register.html", form = form)
        user = User.query.filter_by(email = request.form["email"]).first()
        if user:
            flash("A user with this email already exits")
            return render_template("register.html", form = form)
        length = random.randint(0,25)
        encoded = request.form["password"]
        user = User( username = request.form["username"],
                    email = request.form["email"],
                    password = generate_password_hash(encoded, method='pbkdf2:sha256',salt_length=length),
                    registration_date = dt.datetime.now().strftime("%b/%m/%Y"))
        db.session.add(user)
        db.session.commit()
        login_user(user)
        return redirect(url_for('home'))
    
@app.route('/search', methods=["POST"])
def search():
    form = SearchForm()
    posts = BlogPosts.query
    if form.validate_on_submit():
        searched = form.searched.data
        posts = posts.filter(BlogPosts.body.like('%' + searched + "%"))
        posts = posts.order_by(BlogPosts.title).all()
        if posts == []:
            posts = BlogPosts.query.all()
        return render_template("index.html",posts = posts)
    return "Hello"
    
@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('home'))

    
if __name__ == "__main__":
    app.run(debug=True, port=5000)