from flask import Flask, render_template, url_for, flash, redirect, request
from filmFinder import app, db, bcrypt
from filmFinder.forms import RegistrationForm, LoginForm
from filmFinder.models import USERPROFILES
from flask_login import login_user, logout_user, current_user, login_required
from sqlalchemy.sql import func
# from flask.globals import request
# from flask import g
import sqlite3
from filmFinder.mostPopular import *
from filmFinder.filmDetail import *
# from flask import jsonify

movies = most_popular_movies(10)


@app.route("/")
@app.route("/home")
def home():
    return render_template('home.html', movies=movies)


@app.route("/about")
def about():
    return render_template('about.html', title='About')


@app.route('/search_temp', methods=["GET", "POST"])
def general_search():
    if request.method == "POST":
        page = 1

        name = request.form.get('search')
        genre = request.form.getlist('genre')
        country = request.form.get('country')
        year1 = request.form.get('year1')
        year2 = request.form.get('year2')
        # rating = request.form.get('rating')
        rating = 0
        mode = request.form.get('mode')

        offset = (page - 1) * 10

        if name == '':
            name = None
        if genre == '' or genre == None:
            genre = []
        # else:
        #     genre = genre.split()
        if country == '':
            country = None
        if year1 == '' or year1 == None:
            year1 = None
        else:
            year1 = int(year1)
        if year2 == '' or year2 == None:
            year2 = None
        else:
            year2 = int(year2)
        if rating == '':
            rating = None
        else:
            rating = float(rating)
        conditions = [name, genre, country, year1, year2, rating]
        if mode == None:
            mode = 0
        else:
            mode = int(mode)
        # print(conditions)
        # conn = sqlite3.connect(
        #     'filmFinder/database_files/filmfinder.db', check_same_thread=False)
        # c = conn.cursor()
        search_results = genenal_search(conditions, mode, offset)

        # return jsonify(search_results)
        condition_results = []
        for con in conditions:
            if con == None or con == [] or con == 0.0:
                continue
            else:
                condition_results.append(str(con))
        if condition_results == []:
             condition_results = 'You did not enter any value.\n There are 10 most popular movies below:'
        else:
            condition_results = 'Your search results for ' + \
                ', '.join(condition_results) + ' are:'
        return render_template('search_temp.html', title='Search', condition_results=condition_results, search_results=search_results)
    return render_template('search_temp.html', title='Search')


@app.route('/advanced_search', methods=["GET", "POST"])
def advanced_search():
    if request.method == "POST":
        page = 1

        title = request.form.get('title')
        director = request.form.get('director')
        casts = request.form.get('casts')
        genre = request.form.getlist('genre')
        country = request.form.get('country')
        year1 = request.form.get('year1')
        year2 = request.form.get('year2')
        # rating = request.form.get('rating')
        rating = 0
        mode = request.form.get('mode')

        offset = (page - 1) * 10

        if title == '':
            title = None
        if director == '':
            director = None
        if casts == '':
            casts = None
        if genre == '' or genre == None:
            genre = []
        # else:
        #     genre = genre.split()
        if country == '':
            country = None
        if year1 == '':
            year1 = None
        else:
            year1 = int(year1)
        if year2 == '':
            year2 = None
        else:
            year2 = int(year2)
        if rating == '':
            rating = None
        else:
            rating = float(rating)
        conditions = [title, director, casts, genre, country, year1, year2, rating]
        if mode == None:
            mode = 0
        else:
            mode = int(mode)
        # print(conditions)
        # conn = sqlite3.connect(
        #     'filmFinder/database_files/filmfinder.db', check_same_thread=False)
        # c = conn.cursor()
        search_results = advanced_search1(conditions, mode, offset)

        # return jsonify(search_results)
        condition_results = []
        for con in conditions:
            if con == None or con == [] or con == 0.0:
                continue
            else:
                condition_results.append(str(con))
        if condition_results == []:
             condition_results = 'You did not enter any value. There are 10 most popular movies below: '
        else:
            condition_results = 'Your search results for ' + \
                ', '.join(condition_results) + ' are:'
        return render_template('advanced.html', title='Search', condition_results=condition_results, search_results=search_results)
    return render_template('advanced.html', title='Search')


@app.route("/register", methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    form = RegistrationForm()
    if form.validate_on_submit():
        hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        if USERPROFILES.query.filter_by(username=form.username.data).first():
            flash('The username is already used', category='error')
        elif USERPROFILES.query.filter_by(email=form.email.data).first():
            flash('The email address is already used', category='error')
        else:
            maxid = db.session.query(func.max(USERPROFILES.id)).one()[0]
            # print(maxid)
            user = USERPROFILES(id=maxid+1, username=form.username.data,
                                email=form.email.data, password=hashed_password)
            db.session.add(user)
            db.session.commit()
            flash('Your account has been created! You are now able to log in', category='success')
        return redirect(url_for('home'))
    return render_template('register.html', title='Register', form=form)


@app.route("/login", methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    form = LoginForm()
    if form.validate_on_submit():
        user = USERPROFILES.query.filter_by(email=form.email.data).first()
        if user and bcrypt.check_password_hash(user.password, form.password.data):
            login_user(user, remember=form.remember.data)
            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect(url_for('home'))
        else:
            flash('Login unsccessful! Please check your email and password', category='danger')
    return render_template('login.html', title='Login', form=form)


@app.route("/logout")
def logout():
    logout_user()
    return redirect(url_for('home'))


@app.route("/account")
@login_required
def account():
    return render_template('account.html', title='Account')


@app.route("/film/<string:filmid>")
def film(filmid):
    movie_details = get_movie_details(filmid)
    # print(movie_details)
    return render_template('film.html', movie_details=movie_details)
