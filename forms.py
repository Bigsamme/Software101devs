from flask_wtf import FlaskForm
from flask_ckeditor import CKEditorField
from wtforms import EmailField,StringField,PasswordField,SubmitField
from wtforms.validators import InputRequired,length, DataRequired


class RegisterForm(FlaskForm):
    username = StringField("Username", validators=[InputRequired(),DataRequired()])
    email = EmailField("Email", validators=[InputRequired(),DataRequired()])
    password = PasswordField("Password", validators=[InputRequired(),DataRequired(),length(min=8)])
    submit = SubmitField("Sign up")
    
class PostForm(FlaskForm):
    title = StringField("Post Title")
    description = StringField("Post Description")
    language = StringField("Post language")
    type  = StringField("Post type")
    body = CKEditorField("Blog Content")
    submit = SubmitField("Submit")
    
class LoginForm(FlaskForm):
    email = EmailField("Email", validators=[InputRequired(),DataRequired()])
    password = PasswordField("Password", validators=[InputRequired(),DataRequired(),length(min=8)])
    submit = SubmitField("Log In")
    
    
class SearchForm(FlaskForm):
    searched = StringField("Searched", validators=[InputRequired()])
    submit = SubmitField("Submit")