from app import app
from flask import render_template, request
from app import database


@app.route('/')
def index():
    return render_template('welcome.html')


@app.route('/signIn')
def signIn():
    return render_template('signIn.html')


@app.route('/processSignIn')
def processSignIn():
    return





