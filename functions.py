import random
from flask import request,Flask
from flask_login import current_user
import os
import string
from sqlalchemy import Table, MetaData

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = "static/images/profile_pics"

def create_file_name():
    lower_letters = string.ascii_lowercase
    upper_letters = string.ascii_uppercase
    file_path = ""
    for letter in range(50):
        file_path += random.choice(upper_letters)
        file_path += random.choice(lower_letters)
    file_path += str(current_user.id) #Makes it so there is almost no chance of duplicate.
    file = request.files['thumbnail']
    type_ = file.filename.split(".")[1]
    file_name = '.'.join([file_path,type_])
    file.save(os.path.join(app.config['UPLOAD_FOLDER'], file_name))
    return file_name
    
    
