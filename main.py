from flask import Flask, render_template,url_for,request
from wtforms import StringField,TextAreaField, SubmitField
from flask_wtf import FlaskForm
from flask_bootstrap import Bootstrap
from flask_ckeditor import CKEditor, CKEditorField
from flask_sqlalchemy import SQLAlchemy
import gunicorn
import os




app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get("FLASK_KEY")
ckeditor = CKEditor(app)
Bootstrap(app)

app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv("DB_URL", "sqlite:///userPosts.db")
db = SQLAlchemy(app)

class Post(db.Model):
    id = db.Column( db.Integer, primary_key = True)
    title = db.Column( db. String(250))
    description = db.Column( db. String(250))
    body = db.Column( db.Text)
    language = db.Column( db. String(250))
    type = db.Column( db. String(250))
    
class PostForm(FlaskForm):
    title = StringField("Post Title")
    description = StringField("Post Description")
    language = StringField("Post language")
    type  = StringField("Post type")
    body = CKEditorField("Blog Content")
    submit = SubmitField("Submit")

with app.app_context():
    db.create_all()
    


@app.route("/")
def home():
    posts = Post.query.all()
    
    return render_template("index.html", posts = posts)

@app.route('/login')
def login():
    return render_template('login.html')



@app.route("/add-post", methods=["GET", "POST"])
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
if __name__ == "__main__":
    app.run(debug=True, port=5000)