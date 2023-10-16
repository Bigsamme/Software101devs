from flask_wtf import FlaskForm
from flask_ckeditor import CKEditorField
from wtforms import EmailField,StringField,PasswordField,SubmitField,FileField
from wtforms.validators import InputRequired,length, DataRequired


class RegisterForm(FlaskForm):
    username = StringField("Username", validators=[InputRequired(),DataRequired()])
    email = EmailField("Email", validators=[InputRequired(),DataRequired()])
    password = PasswordField("Password", validators=[InputRequired(),DataRequired(),length(min=8)])
    submit = SubmitField("Sign up")
    
class BlogPostForm(FlaskForm):
    title = StringField("Post Title",validators=[DataRequired(),InputRequired()])
    description = StringField("Post Description",validators=[DataRequired(),InputRequired()])
    language = StringField("Post language",validators=[DataRequired(),InputRequired()])
    thumbnail = FileField("Thumbnail",validators=[DataRequired(),InputRequired()])
    type  = StringField("Post type",validators=[DataRequired(),InputRequired()])
    body = CKEditorField("Blog Content",validators=[DataRequired(),InputRequired()])
    submit = SubmitField("Submit",validators=[DataRequired(),InputRequired()])
    
class LoginForm(FlaskForm):
    email = EmailField("Email", validators=[InputRequired(),DataRequired()])
    password = PasswordField("Password", validators=[InputRequired(),DataRequired(),length(min=8)])
    submit = SubmitField("Log In")
    
    
class SearchForm(FlaskForm):
    searched = StringField("Searched", validators=[InputRequired()])
    submit = SubmitField("Submit")

    
class ContactForm(FlaskForm):
    email = EmailField("Email", validators=[InputRequired()])
    subject = StringField("Subject",validators=[InputRequired()])
    message = CKEditorField("Message", validators=[InputRequired()])
    submit = SubmitField("Send")
    
class ForgotPasswordForm(FlaskForm):
    email = EmailField("Email")
    submit = SubmitField("Submit")
    
class PasswordResetForm(FlaskForm):
    password1 = PasswordField("Password")
    code = StringField("Reset Code")
    password2 = PasswordField("Confirm password")
    submit =  SubmitField("Submit Password")