from flask import Flask, render_template,url_for
import gunicorn



app = Flask(__name__)

@app.route("/")
def home():
    return render_template("index.html")

@app.route('/login')
def login():
    return render_template('login.html')

@app.route("/post")
def show_post():
    return render_template('post.html')


if __name__ == "__main__":
    app.run(debug=True, port=5000)