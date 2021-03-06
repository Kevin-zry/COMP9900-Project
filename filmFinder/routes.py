import os
import secrets
import sqlite3
from filmFinder import recommend
from flask import Flask, render_template, url_for, flash, redirect, request
from filmFinder import app, db, bcrypt
from filmFinder.forms import RegistrationForm, LoginForm, UpdateAccountForm, ReviewForm
from filmFinder.models import USERPROFILES, RATINGS
from flask_login import login_user, logout_user, current_user, login_required


from filmFinder.mostPopular import *
from filmFinder.filmDetail import *
from filmFinder.reviewDetail import *
from filmFinder.forms import *

from sqlalchemy.sql import func
from PIL import Image
from flask_paginate import Pagination

most_popular_movies = most_popular_movies(10)



def paginate(data, per_page, name):
    page = request.form.get("page", 1, type=int)
    start = (page - 1) * per_page
    end = page * per_page if len(data) > page * per_page else len(data)
    paginated_data = data[start: end]
    pagination = Pagination(page=page, per_page=per_page, total=len(
        data), record_name=name, inner_window=3, css_framework='bootstrap4')
    return paginated_data, page, per_page, pagination

@app.route("/")
@app.route("/home")
def home():
    if current_user.is_authenticated:
        userid = current_user.id
        recommend_list = ubcf(userid)
        
        highest_rating_list = highest_rating_movies(current_user.id, 10)
    else:
        recommend_list = []
        highest_rating_list = highest_rating_movies(None, 10)
    return render_template('home.html', 
        movies=most_popular_movies, # 改成前后一致
        recommend_list=recommend_list, 
                           highest_rating_movies=highest_rating_list)


@app.route("/about")
def about():
    return render_template('about.html', title='About')


@app.route('/search_temp', methods=["GET", "POST"])
def general_search():
    if request.method == "POST":
        name = request.form.get('search')
        genre = request.form.getlist('genre')
        country = request.form.get('country')
        year1 = request.form.get('year1')
        year2 = request.form.get('year2')
        
        rating = 0
        mode = request.form.get('mode')
        title=name
        if name == '':
            name = None
        if genre == '' or genre == None:
            genre = []
        
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
        
        search_results = genenal_search(conditions, mode, 0)

        res = []
        if current_user.is_authenticated:
            for i in search_results:
                res.append(get_movie_details(current_user.id, int(i[0])))
        else:
            for i in search_results:
                res.append(get_movie_details(None, int(i[0])))

        condition_results = []
        paginated_res, page, per_page, pagination = paginate(res, 10, 'search results')
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
        return render_template('search_temp.html', title='Search', condition_results=condition_results,
                               search_results=paginated_res, page=page, per_page=per_page, pagination=pagination,name=title)
    return render_template('search_temp.html', title='Search')


@app.route('/advanced_search', methods=["GET", "POST"])
def advanced_search():
    if request.method == "POST":
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
        
        search_results = advanced_search1(conditions, mode, 0)
        res = []
        if current_user.is_authenticated:
            for i in search_results:
                res.append(get_movie_details(current_user.id, int(i[0])))
        else:
            for i in search_results:
                res.append(get_movie_details(None, int(i[0])))

        paginated_res, page, per_page, pagination = paginate(res, 10, 'search results')
        
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

        return render_template('advanced.html', title='Search', condition_results=condition_results, search_results=paginated_res,
                               page=page, per_page=per_page, pagination=pagination, name=output[0], director=output[1], casts=output[2],
                               genre=output[3], country=output[4], year1=output[5], year2=output[6], mode=output[7])
    return render_template('advanced.html', title='Search', search_results='')


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
                                email=form.email.data, password=hashed_password, like=0)
            db.session.add(user)
            db.session.commit()
            flash('Your account has been created! You are now able to log in!',
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

@app.route("/account/<int:userid>", methods=["GET", "POST"])
@login_required
def account(userid):
    if userid == current_user.id:
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
            # return redirect(url_for(f'/account/{userid}'))
        elif request.method == 'GET':
            form.username.data = current_user.username
            form.email.data = current_user.email
        image_file = url_for(
            'static', filename='profile_pics/' + current_user.profile_image)
        like = current_user.like
        wishlist = get_wishlist(userid)
        blocklist = get_blocklist(userid)
        return render_template('account.html', title='Account', image_file=image_file, form=form, wishlist=wishlist, blocklist=blocklist, identify=identify, like=like)
    else:
        identify = False
        user = get_user_detail(userid)
        image_file = url_for(
            'static', filename='profile_pics/' + user['profile_image'])
        if request.method == "POST":
            blocklist_button(current_user.id, userid)
        wishlist = get_wishlist(userid)
        blocklist = get_blocklist(userid)
        return render_template('account.html', title='Account', image_file=image_file, user=user, wishlist=wishlist, blocklist=blocklist, identify=identify)



@app.route("/film/<int:filmid>", methods=["GET", "POST"])
def film(filmid):
    if current_user.is_authenticated:
        reviews = get_review_details(current_user.id, filmid)
        movie_details = get_movie_details(current_user.id, filmid)
        recommend_list = ibcf(current_user.id, filmid)
    else:
        reviews = get_review_details(None, filmid)
        movie_details = get_movie_details(None, filmid)
        recommend_list = ibcf(None, filmid)

    # paginate reviews
    my_review, reviews = reviews[0], reviews[1]
    per_page = 6
    page = request.args.get("page", 1, type=int)
    start = (page - 1) * per_page
    end = page * per_page if len(reviews) > page * per_page else len(reviews)
    paginated_reviews = reviews[start: end]
    pagination = Pagination(page=page, per_page=per_page, total=len(
        reviews), record_name='reviews', inner_window=3, css_framework='bootstrap4')
    # print('page', 'per_page', 'offset')
    # print(page, per_page, offset)   
    f_type=''
    response = ''
    if request.method == "POST":
        if 'filtertype' in request.form:
            f_type=request.form['filtertype']
            recommend_list = item_based_result_filter(filmid, recommend_list, request.form['filtertype'])
        elif current_user.is_authenticated:
            if 'add_to_wishlist' in request.form:
                userid = current_user.id
                response = wishlist_button(filmid, userid)
            elif 'block' in request.form:
                blockid = int(request.form['block'])
                response = blocklist_button(current_user.id, blockid)
            elif 'like' in request.form:
                ratingid = int(float(request.form['like']))
                like_increment(ratingid)
            elif 'review' in request.form:
                rating = float(request.form['rating'])
                review = request.form['review']
                if not review:
                    flash('Review must not be empty', category='danger')
                else:
                    add_review(current_user.id, filmid, rating, review)
        else:
        	flash('You need to login in first')
        	return redirect(url_for('login'))
    if len(recommend_list) > 10:
        recommend_list = recommend_list[:10]
    
    return render_template('film.html', movie_details=movie_details, recommend_list=recommend_list, response=response, filmid=filmid,
                           my_review=my_review, reviews=paginated_reviews, page=page, per_page=per_page, pagination=pagination,type=f_type)


@app.route("/wishlist/<int:userid>", methods=["GET", "POST"])
@login_required
def wishlist(userid):
    wishlist = get_wishlist(current_user.id)
    if request.method == "POST":
        movieid = request.form['remove_from_wishlist']
        remove_from_wishlist(userid, movieid)
    return render_template('wishlist.html', title='Wishlist', wishlist=wishlist)


@app.route("/blocklist/<int:userid>", methods=["GET", "POST"])
@login_required
def blocklist(userid):
    blocklist = get_blocklist(current_user.id)
    if request.method == "POST":
        blockid = request.form['remove_from_blocklist']
        remove_from_blocklist(userid, blockid)
    return render_template('blocklist.html', title='Blocklist', blocklist=blocklist)

@app.route("/review/<int:review_id>/delete", methods=['POST'])
@login_required
def delete_review(review_id):
    review = RATINGS.query.get_or_404(review_id)
    author = USERPROFILES.query.get(review.userId)
    if author != current_user:
        abort(403)
    db.session.delete(review)
    db.session.commit()
    flash('Your review has been deleted!', 'success')
    filmid = request.args.get('filmid')
    return redirect(f'/film/{filmid}')

@app.route("/more")
def more():
    flag = int(request.args.get('flag'))
    if flag == 1:
        if current_user.is_authenticated:
            movies = highest_rating_movies(current_user.id, 10)
        else:
            movies = highest_rating_movies(None, 10)
    else:
        movies = ubcf(current_user.id)

    per_page = 10
    page = request.args.get("page", 1, type=int)
    start = (page - 1) * per_page
    end = page * per_page if len(movies) > page * per_page else len(movies)
    paginated_movies = movies[start: end]
    pagination = Pagination(page=page, per_page=per_page, total=len(movies), record_name='movies', inner_window=3, css_framework='bootstrap4')
    
    return render_template('results.html', title='Films list', movies=paginated_movies, page=page, per_page=per_page, pagination=pagination, flag=flag)

@app.route("/404", methods=["GET", "POST"])

def not_found():
    return render_template('404.html')
