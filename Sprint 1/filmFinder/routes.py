import os
from filmFinder import recommend
from flask import Flask, render_template, url_for, flash, redirect, request
from filmFinder import app, db, bcrypt
from filmFinder.forms import RegistrationForm, LoginForm, UpdateAccountForm
from filmFinder.models import USERPROFILES
from flask_login import login_user, logout_user, current_user, login_required
from sqlalchemy.sql import func
import secrets
from PIL import Image
# from flask.globals import request
# from flask import g
import sqlite3
from filmFinder.mostPopular import *
from filmFinder.filmDetail import *
# from flask import jsonify

most_popular_movies = most_popular_movies(10)
highest_rating_movies = highest_rating_movies(10)

@app.route("/")
@app.route("/home")
def home():
    if current_user.is_authenticated:
        userid = current_user.get_id()
        recommend_list = ubcf(userid)
    else:
        recommend_list = []
    return render_template('home.html', 
        movies=most_popular_movies, # 改成前后一致
        recommend_list=recommend_list, 
        highest_rating_movies=highest_rating_movies)


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

        res = []
        for i in search_results:
            res.append(get_movie_details(int(i[0])))

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
        return render_template('search_temp.html', title='Search', condition_results=condition_results, search_results=res)
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

        output = [title, director, casts, genre, country, year1, year2, mode]

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
        conditions = [title, director, casts,
                      genre, country, year1, year2, rating]
        if mode == None:
            mode = 0
        else:
            mode = int(mode)
        # print(conditions)
        # conn = sqlite3.connect(
        #     'filmFinder/database_files/filmfinder.db', check_same_thread=False)
        # c = conn.cursor()
        search_results = advanced_search1(conditions, mode, offset)
        res = []
        for i in search_results:
            res.append(get_movie_details(int(i[0])))

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
        return render_template('advanced.html', title='Search', condition_results=condition_results, search_results=res, name=output[0], director=output[1], casts=output[2], genre=output[3], country=output[4], year1=output[5], year2=output[6], mode=output[7])
    return render_template('advanced.html', title='Search')


@app.route("/register", methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    form = RegistrationForm()
    if form.validate_on_submit():
        hashed_password = bcrypt.generate_password_hash(
            form.password.data).decode('utf-8')
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
            flash('Your account has been created! You are now able to log in',
                  category='success')
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
            flash('Login unsccessful! Please check your email and password',
                  category='danger')
    return render_template('login.html', title='Login', form=form)


@app.route("/logout")
def logout():
    logout_user()
    return redirect(url_for('home'))


def save_picture(form_picture):
    random_hex = secrets.token_hex(8)
    _, f_ext = os.path.splitext(form_picture.filename)
    picture_fn = random_hex + f_ext
    picture_path = os.path.join(
        app.root_path, 'static/profile_pics', picture_fn)

    output_size = (300, 300)
    img = Image.open(form_picture)
    img.thumbnail(output_size)
    img.save(picture_path)

    return picture_fn


@app.route("/account/<string:userid>", methods=["GET", "POST"])
# @login_required
def account(userid):
    if userid == current_user.get_id():
        identify = True
        form = UpdateAccountForm()
        if form.validate_on_submit():
            if form.picture.data:
                picture_file = save_picture(form.picture.data)
                current_user.profile_image = picture_file
            current_user.username = form.username.data
            current_user.email = form.email.data
            db.session.commit()
            flash('Your account has been updated!', category='success')
            return redirect(url_for('account'))
        elif request.method == 'GET':
            form.username.data = current_user.username
            form.email.data = current_user.email
        image_file = url_for(
            'static', filename='profile_pics/' + current_user.profile_image)
        
    else:
        identify = False
        form = UpdateAccountForm()
        if form.validate_on_submit():
            if form.picture.data:
                picture_file = save_picture(form.picture.data)
                current_user.profile_image = picture_file
            current_user.username = form.username.data
            current_user.email = form.email.data
            db.session.commit()
            flash('Your account has been updated!', category='success')
            return redirect(url_for('account'))
        elif request.method == 'GET':
            form.username.data = current_user.username
            form.email.data = current_user.email
        image_file = url_for(
            'static', filename='profile_pics/' + current_user.profile_image)
        if request.method == "POST":
            blocklist_button(current_user.get_id(), userid)
    wishlist = get_wishlist(userid)
    blocklist = get_blocklist(userid)
    
    return render_template('account.html', title='Account', image_file=image_file, form=form, wishlist=wishlist, blocklist=blocklist, identify=identify)


@app.route("/film/<string:filmid>", methods=["GET", "POST"])
def film(filmid):
    movie_details = get_movie_details(filmid)
    recommend_list = ibcf(filmid)
    response = ''
    if request.method == "POST":
        if current_user.is_authenticated:
            userid = current_user.get_id()
            response = wishlist_button(filmid, userid)
        else:
            response = 'You need to login first'
    return render_template('film.html', movie_details=movie_details, recommend_list=recommend_list, response=response)


@app.route("/wishlist/<string:userid>", methods=["GET", "POST"])
@login_required
def wishlist(userid):
    wishlist = get_wishlist(current_user.get_id())
    if request.method == "POST":
        movieid = request.form['remove_from_wishlist']
        remove_from_wishlist(userid, movieid)
    return render_template('wishlist.html', title='Wishlist', wishlist=wishlist)


@app.route("/blocklist/<string:userid>", methods=["GET", "POST"])
@login_required
def blocklist(userid):
    blocklist = get_blocklist(current_user.get_id())
    if request.method == "POST":
        blockid = request.form['remove_from_blocklist']
        remove_from_blocklist(userid, blockid)
    return render_template('blocklist.html', title='Blocklist', blocklist=blocklist)

