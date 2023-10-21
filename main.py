from flask import Flask, render_template,url_for,request,redirect, flash
from flask_bootstrap import Bootstrap
from flask_ckeditor import CKEditor
from flask_login import LoginManager, login_user,logout_user, UserMixin,current_user
from flask_sqlalchemy import SQLAlchemy
import gunicorn
import os
from smtplib import SMTP
import datetime as dt
from werkzeug.security import gen_salt, generate_password_hash,check_password_hash
from datetime import datetime
from sqlalchemy.orm import relationship
from sqlalchemy import MetaData, Table
from forms import RegisterForm, ForgotPasswordForm, PasswordResetForm, LoginForm, BlogPostForm,SearchForm,ContactForm
import random
from email.mime.text import MIMEText
from threading import Thread
from decoraters import proper_user_required, owner_required
from functions import app,create_file_name





app.config['SECRET_KEY'] = os.environ.get("FLASK_KEY")
ckeditor = CKEditor(app)
Bootstrap(app)



app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv("DB_URL", "sqlite:///blog_posts.db")
db = SQLAlchemy(app)

login_manager = LoginManager()
login_manager.init_app(app)

#logs in the current user
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
    forgot_password_code = db.Column(db.Integer)
    posts = relationship("BlogPosts", back_populates="author")
    draft_posts = relationship("DraftPosts", back_populates="author")
    post_history = relationship("UserPostHistory", back_populates="read_user")
    
    
# self explanatory
class DraftPosts(db.Model):
    __tablename__  = "draft_posts"
    id = db.Column(db.Integer, primary_key = True)
    title = db.Column(db.String)
    description = db.Column( db. String(250))
    body = db.Column( db.Text)
    tags = db.Column( db.String(250))
    type = db.Column( db.String(250))
    thumbnail = db.Column(db.String)
    views = db.Column(db.Integer)
    author_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    author = relationship("User", back_populates="draft_posts")


# table for articles users have read
class UserPostHistory(db.Model):
    __tablename__ = "user_post_history"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    post_id = db.Column(db.Integer, db.ForeignKey("blog_posts.id"))
    date_read = db.Column(db.DateTime, default=datetime.utcnow)

    read_user = relationship("User", back_populates="post_history")
    post = relationship("BlogPosts", back_populates="read_by_users")

    
    
#table for all data related to User posted articles 
class BlogPosts(db.Model):
    __tablename__ = "blog_posts"
    id = db.Column( db.Integer, primary_key = True)
    title = db.Column( db.String(250))
    description = db.Column( db. String(250))
    body = db.Column( db.Text)
    tags = db.Column( db.String(250))
    type = db.Column( db.String(250))
    thumbnail = db.Column(db.String)
    views = db.Column(db.Integer)
    author_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    author = relationship("User", back_populates="posts")
    read_by_users = relationship("UserPostHistory", back_populates="post")


with app.app_context():
    db.create_all()
    



# Makes the search base in header.html work
@app.context_processor
def base():
    form = SearchForm()
    return dict(search_form = form)



#All of the roots for the visual side of the website below

@app.route("/")
def home():
    posts = BlogPosts.query.all()
    user = current_user
    data = posts
    random.shuffle(posts)
    #returns  10 random posts so the website loads faster
    posts = posts[:10]
    return render_template("index.html", posts = posts,user= user, data = data)



@app.route("/support/about_us/")
def about_us():
    return render_template('about-us.html')

@app.route('/register', methods = ["GET","POST"])
def register():
    if current_user.is_authenticated:
        return redirect(url_for("home"))
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
        length = random.randint(1,25)
        encoded = request.form["password"]
        #uploads the user information to the users table 
        user = User( username = request.form["username"],
                    email = request.form["email"],
                    forgot_password_code = None,
                    password = generate_password_hash(encoded, method='pbkdf2:sha256',salt_length=length),
                    registration_date = dt.datetime.now().strftime("%b/%m/%Y"))
        db.session.add(user)
        db.session.commit()
        login_user(user) 
        return redirect(url_for('home'))
    
@app.route('/login', methods=["GET", "POST"])
def login():
    #IF the user is already logged in redirects them to the home page
    if current_user.is_authenticated:
        return redirect(url_for("home"))
    form = LoginForm()
    if request.method == "GET":
        return render_template('login.html',form = form)
    
    #Tries to log the user in if request method is not get
    email = request.form['email']
    user = User.query.filter_by( email = email).first()
    if not user:
        flash("A User with this email not found", "error")
        return  render_template('login.html', form = form)
        
    password = form.password.data
    if not check_password_hash(user.password, password):
        flash("Password is incorrect", "error")
        return render_template("login.html", form = form)
    
    #The data provided by the user was all correct logs them in
    days = dt.timedelta(days = 31, seconds = 0)
    login_user(user, remember = True, duration = days)
    return redirect(url_for('home'))

@app.route('/users/dashboard/<username>')
@proper_user_required #Makes sure users can't access other peoples dashboard
def dashboard(username):
    # Redirects none logged in users to the login page
    if not current_user.is_authenticated:
        return redirect(url_for("login"))
    
    # returns the current users dashboard
    user = User.query.filter_by(username = username).first()
    user_posts = BlogPosts.query.filter_by(author_id = user.id).all()
    return render_template("dashboard.html", user = user,user_posts = user_posts)

@app.route("/support/contact", methods = ["GET","POST"])
def contact():
    form = ContactForm()
    if request.method == "GET":
        
        if not current_user.is_authenticated:
            return render_template("contact.html", form  = form)
        form.email.data = current_user.email # If the user is already logged in populates the email field
        return render_template("contact.html", form = form)
    else:
        email = request.form["email"]
        subject = request.form["subject"]
        message = request.form["message"]
        with SMTP("smtp.gmail.com", port=587) as connection:
            connection.starttls()
            connection.login("samuelwhitehall@gmail.com", os.environ.get("EMAIL_PASSWORD"))
            connection.sendmail("samuelwhitehall@gmail.com", "samuelwhitehall@gmail.com", msg=f"Subject: {subject}\n\n From \n {email} Message : {message}")
        return redirect(url_for("home"))
        

@app.route("/add_post", methods=["GET", "POST"])
def add_post():
    if not current_user.is_authenticated:
        return redirect(url_for('login'))
    form = BlogPostForm()
    if request.method == "GET":
        return render_template('add-post.html', form = form)
    
    
    #Generates a random post thumbnail filepath with the users username attached
    if form.validate_on_submit():
        file_name = create_file_name()
        new_post = BlogPosts(
            title=form.title.data,
            description=form.description.data,
            body=form.body.data,
            tags=form.tags.data,
            thumbnail = file_name,
            type=form.type.data,
            views = 0,
            author=current_user  # Set the author to the current logged-in user
        )


        # Then, add the new post to the database
        db.session.add(new_post)
        db.session.commit()
        return redirect(url_for('home'))
    return render_template("add-post.html", form = form)
        
    
@app.route('/show_post/<post_title>/<int:post_id>')
def show_post(post_id,post_title): #has the post just so its in the url 
    post = BlogPosts.query.filter_by(id = post_id).first()
    if current_user.is_authenticated:
        if current_user.id != post.author.id: #makes sure the author can't add views to their own posts
            post.views += 1 #adds to the post views
    else:
        post.views += 1 #adds to the post views
    user = current_user
    if user.is_authenticated: #If the user is logged in adds the post to the read history
        read_history_entry = UserPostHistory(read_user=user, post=post)
        db.session.add(read_history_entry)#Add the user read history
    db.session.commit() #Commits the changes to the data base
    return render_template("post.html", post = post)



@app.route("/login/forgot_password", methods=["POST", "GET"])
def forgot_password():
    if current_user.is_authenticated:
        return redirect(url_for("home"))
    form = ForgotPasswordForm()
    if request.method == "GET":
        return render_template("forgot_password.html", form=form)
    else:
        email = request.form["email"]
        user = User.query.filter_by(email=email).first()
        if not user:
            flash("This Email not found")
            return render_template("forgot_password.html", form=form)

        code = random.randint(1000, 9999)
        user.forgot_password_code = code
        db.session.add(user)
        db.session.commit()
        url = f"http://localhost:5000{url_for('reset_password', username=user.username, email=user.email, user_id=str(user.id))}"

        body = f'Your reset code is {code} click this link to continue {url}'
        msg = MIMEText(body)
        with SMTP("smtp.gmail.com", port=587) as connection:
            connection.starttls()
            connection.login("samuelwhitehall@gmail.com", password=os.environ["EMAIL_PASSWORD"])
            connection.sendmail(from_addr="samuelwhitehall@gmail.com", to_addrs=email, msg=msg.as_string())
        return "Hello "

@app.route("/<username>/<email>/<user_id>/reset_password", methods = ["GET", "POST"])
def reset_password(username, email, user_id):
    form = PasswordResetForm()
    if request.method == "GET":
        return render_template("password_reset.html", form=form)
    
    
    user = User.query.filter_by(id = user_id).first()
    
    if str(user.forgot_password_code) != request.form["code"]:
        flash("Please make sure the reset code you entered matches the one in your email")
        return render_template("password_reset.html", form=form)
            
            
    length = random.randint(1,25)
    encoded = request.form["password1"]

    user.password = generate_password_hash(encoded, method='pbkdf2:sha256',salt_length=length)
    user.forgot_password_code == None
    db.session.add(user)
    db.session.commit()
    return redirect(url_for("home"))

        
@app.route('/search', methods=["POST"])
def search():
    form = SearchForm()
    posts = BlogPosts.query
    if form.validate_on_submit():
        searched = form.searched.data
        #search's the content of the article
        posts = posts.filter(BlogPosts.body.like('%' + searched + "%"))
        posts = posts.all()
        if posts == []:
            posts = BlogPosts.query.all()
        return render_template("index.html",posts = posts)
    return redirect(url_for("home"))

@app.route("/delete-post/<int:post_id>")
def delete(post_id):
    post = BlogPosts.query.filter_by(id = post_id).first()
    db.session.delete(post)
    db.session.commit()
    return redirect(url_for("dashboard", username = current_user.username))
    
    
@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('home'))

    
if __name__ == "__main__":
    app.run(debug=True)