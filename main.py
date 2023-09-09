from flask import Flask, render_template,url_for,request,redirect, flash
from flask_bootstrap import Bootstrap
from flask_ckeditor import CKEditor
from flask_login import LoginManager, login_required, login_user,logout_user, UserMixin,current_user
from flask_sqlalchemy import SQLAlchemy
import gunicorn
import os
import datetime as dt
from sqlalchemy.orm import relationship
from forms import RegisterForm, BlogPostForm, LoginForm, SearchForm, FileSubmit
from werkzeug.utils import secure_filename
import random
import string



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
    
    

class BlogPosts(db.Model):
    __tablename__ = "blog_posts"
    id = db.Column( db.Integer, primary_key = True)
    title = db.Column( db.String(250))
    description = db.Column( db. String(250))
    body = db.Column( db.Text)
    language = db.Column( db.String(250))
    type = db.Column( db.String(250))
    views = db.Column(db.Integer)
    author_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    author = relationship("User", back_populates="posts")


with app.app_context():
    db.create_all()


def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS
           
@app.route('/image', methods = ["GET","POST"])  
def image():
    lower_letters = string.ascii_lowercase
    upper_letters = string.ascii_uppercase
    file_path = ""
    for letter in range(50):
        file_path += random.choice(upper_letters)
        file_path += random.choice(lower_letters)
    form =  FileSubmit()
    if request.method =="GET":
        return render_template('login.html', form = form)
    if request.method == 'POST':
        # check if the post request has the file part
        if 'file' not in request.files:
            flash('No file part')
            return redirect(request.url)
        file = request.files['file']
        # If the user does not select a file, the browser submits an
        # empty file without a filename.
        if file.filename == '':
            flash('No selected file')
            return redirect(request.url)
        if file and allowed_file(file.filename):
            type_ = file.filename.split(".")[1]
            file_name = '.'.join([file_path,type_])
            user = User.query.filter_by(email = current_user.email).first()
            user.profile_pic = file_name
            db.session.add(user)
            db.session.commit()
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], file_name))
            return redirect(url_for('home'))
    return '''
    <!doctype html>
    <title>Upload new File</title>
    <h1>Upload new File</h1>
    <form method=post enctype=multipart/form-data>
      <input type=file name=file>
      <input type=submit value=Upload>
    </form>
    '''

@app.route("/")
def home():
    posts = BlogPosts.query.all()
    posts = posts[:10]
    user = current_user
    
    return render_template("index.html", posts = posts,user= user)

@app.route("/<int:number>")
def home_10(number):
    if number == 1:
        posts = BlogPosts.query.all()
        posts = posts[number * 1:number*10]
    else:
        posts = BlogPosts.query.all()
        posts = posts[number * 10:10+number*10]
    user = current_user
    
    return render_template("index.html", posts = posts,user= user)

@app.context_processor
def base():
    form = SearchForm()
    return dict(form = form)

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
            if user.password == request.form['password']:
                login_user(user)
                return redirect(url_for('home'))
            else:
                flash("Password is incorrect", "error")
                return render_template("login.html", form = form)
        else:
            flash("A User with this email not found", "error")
            return render_template('login.html', form = form)
            

@app.route('/<username>/dashboard')
def dashboard(username):
    user = User.query.filter_by(username = username).first()
    user_posts = BlogPosts.query.filter_by(author_id = user.id).all()
    return render_template("dashboard.html", user = user,user_posts = user_posts)


@app.route("/add-post", methods=["GET", "POST"])
def add_post():
    if not current_user.is_authenticated:
        return redirect(url_for('login'))
    form = BlogPostForm()
    if request.method == "GET":
        return render_template('add-post.html', form = form)
    elif request.method == "POST":
        new_post = BlogPosts(
            title=form.title.data,
            description=form.description.data,
            body=form.body.data,
            language=form.language.data,
            type=form.type.data,
            views = 0,
            author=current_user  # Set the author to the current logged-in user
        )

        # Then, add the new post to the database
        db.session.add(new_post)
        db.session.commit()
        return redirect(url_for('home'))
    
    
@app.route('/show-post/<post_title>/<int:post_id>')
def show_post(post_id,post_title):
    post = BlogPosts.query.filter_by(id = post_id).first()
    post.views = post.views + 1
    db.session.add(post)
    db.session.commit()
    return render_template("post.html", post = post)

@app.route('/register', methods = ["GET","POST"])
def register():
    if request.method == "GET":
        form = RegisterForm()
        return render_template('register.html', form = form)
    elif request.method == "POST":
        user = User( username = request.form["username"],
                    email = request.form['email'],
                    password = request.form['password'],
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