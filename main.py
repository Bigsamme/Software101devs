from flask import Flask, render_template,url_for,request,redirect, flash
from flask_bootstrap import Bootstrap
from flask_ckeditor import CKEditor
from flask_login import LoginManager, login_required, login_user,logout_user, UserMixin
from flask_sqlalchemy import SQLAlchemy
import gunicorn
import os
from forms import RegisterForm, PostForm, LoginForm, SearchForm


app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get("FLASK_KEY")
ckeditor = CKEditor(app)
Bootstrap(app)


app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv("DB_URL", "sqlite:///posts.db")
db = SQLAlchemy(app)

login_manager = LoginManager()
login_manager.init_app(app)

@login_manager.user_loader
def load_user(user_id):
    return User.query.filter_by(id = user_id).first()

class User(UserMixin, db.Model):
    id = db.Column( db.Integer, primary_key = True)
    username = db.Column( db. String(250))
    email = db.Column( db. String(250))
    password = db.Column( db. String(250))


class Post(db.Model):
    id = db.Column( db.Integer, primary_key = True)
    title = db.Column( db. String(250))
    description = db.Column( db. String(250))
    body = db.Column( db.Text)
    language = db.Column( db. String(250))
    type = db.Column( db. String(250))
    


with app.app_context():
    db.create_all()
    


@app.route("/")
def home():
    posts = Post.query.all()
    
    return render_template("index.html", posts = posts)

@app.context_processor
def base():
    form = SearchForm()
    return dict(form = form)

@app.route("/support/about-us")
def about_us():
    return render_template('about-us.html')
@app.route('/login', methods=["GET", "POST"])
def login():
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
            return "Nope"
            



@app.route("/add-post", methods=["GET", "POST"])
@login_required
def add_post():
    if request.method == "GET":
        form = PostForm()
        return render_template('add-post.html', form = form)
    elif request.method == "POST":
        post = Post( title = request.form['title'],
                    description = request.form['description'],
                    body = request.form['body'],
                    language = request.form['language'],
                    type = request.form['type'])
        db.session.add(post)
        db.session.commit()
        return render_template('index.html')
    
@app.route('/show-post/<post_title>/<int:post_id>')
def show_post(post_id,post_title):
    post = Post.query.filter_by(id = post_id).first()
    return render_template("post.html", post = post)

@app.route('/register', methods = ["GET","POST"])
def register():
    if request.method == "GET":
        form = RegisterForm()
        return render_template('register.html', form = form)
    elif request.method == "POST":
        user = User( username = request.form["username"],
                    email = request.form['email'],
                    password = request.form['password'])
        db.session.add(user)
        db.session.commit()
        login_user(user)
        return redirect(url_for('home'))
    
@app.route('/search', methods=["POST"])
def search():
    form = SearchForm()
    posts = Post.query
    if form.validate_on_submit():
        searched = form.searched.data
        posts = posts.filter(Post.body.like('%' + searched + "%"))
        posts = posts.order_by(Post.title).all()
        if posts == []:
            posts = Post.query.all()
        return render_template("index.html",posts = posts)
    return "Hello"
    
@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('home'))
if __name__ == "__main__":
    app.run(debug=True, port=5000)