from flask_login import current_user
from flask import redirect, url_for
from functools import wraps


#Makes sure users can't access other peoples data
def proper_user_required(func):
    @wraps(func)
    def decorated_function(*args, **kwargs):
        if current_user.username != kwargs.get("username"):
            return redirect(url_for('add_post'))
        return func(*args, **kwargs)
    return decorated_function

def owner_required(func):
    @wraps(func)
    def decorated_function(*args, **kwargs):
        if current_user.id != 1:
            return redirect(url_for('home'))
        return func(*args, **kwargs)
    return decorated_function