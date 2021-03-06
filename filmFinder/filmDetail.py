import sqlite3
import re
from filmFinder.recommend import *
from flask import flash
from filmFinder.reviewDetail import get_movie_avg_rating


def re_process(string):
    # print(string)
    if string:
        l = re.findall("'name': '[a-zA-Z ]{1,}'", string)
        l = [i[9:-1] for i in l]
        return l
    else:
        return ['No data.']


def get_movie_details(userid, filmid):
    conn = sqlite3.connect('filmFinder/database_files/filmfinder.db')
    c = conn.cursor()
    filmid = int(filmid)
    c.execute(
        f'SELECT * FROM FILMS WHERE id = {filmid}')
    x = c.fetchone()
    detail = {'id': x[0], 'title': x[1], 'genres': re_process(x[2]), 'belongs_to_collection': re_process(x[3]), 'production_countries': re_process(x[4]),
              'release_date': x[5], 'overview': x[6], 'poster_path': x[7], 'vote_average': get_movie_avg_rating(userid, filmid), 'vote_count': int(x[9])}
    c.execute(f'SELECT crew FROM CREDITS WHERE id = {filmid}')
    x = c.fetchone()
    detail['crew'] = x[0][1:-1]
    c.execute(f'SELECT casts FROM CREDITS WHERE id = {filmid}')
    x = c.fetchone()
    cast_process = re_process(x[0])
    detail['casts'] = [i for i in cast_process]
    return detail


def ibcf(userid, filmid):
    item_list = collaborative_filtering_item(int(filmid))
    result_list = []
    if item_list:
        for item in item_list:
            result_list.append(get_movie_details(userid, item))
    return result_list


def ubcf(userid):
    item_list = collaborative_filtering_user(int(userid))
    result_list = []
    if item_list:
        for item in item_list:
            result_list.append(get_movie_details(userid, item))
    return result_list


def wishlist_button(filmid, userid):
    conn = sqlite3.connect('filmFinder/database_files/filmfinder.db')
    c = conn.cursor()
    c.execute(
        f"SELECT userid, movieid FROM WISHLIST WHERE userid = {userid} and movieid = {filmid}")
    already_added_check = c.fetchall()
    if not already_added_check:
        c.execute(f"SELECT max(id) FROM WISHLIST")
        maxid = c.fetchone()
        c.execute(
            f"INSERT INTO WISHLIST (id, userid, movieid) VALUES ({maxid[0]}, {userid}, {filmid})")
        conn.commit()
        return 'Add to wishlist successfully.'
    else:
        return 'Already in wishlist.'


def get_wishlist(userid):
    conn = sqlite3.connect('filmFinder/database_files/filmfinder.db')
    c = conn.cursor()
    c.execute(f"SELECT movieid FROM WISHLIST WHERE userid = {userid}")
    wishlist_film_id = c.fetchall()
    # print(wishlist_film_id)
    if wishlist_film_id:
        return [get_movie_details(userid, filmid[0]) for filmid in wishlist_film_id]
    return []


def get_blocklist(userid):
    conn = sqlite3.connect('filmFinder/database_files/filmfinder.db')
    c = conn.cursor()
    c.execute(
        f"SELECT u.id, u.username, u.profile_image FROM USERPROFILES u WHERE u.id in (SELECT blockid FROM BLOCKING WHERE userid = {userid})")
    blocklist_id = c.fetchall()
    # print(blocklist_id)
    if blocklist_id:
        block = []
        for block_user in blocklist_id:
            profile = {
                'id': block_user[0], 'username': block_user[1], 'profile_image': block_user[2]}
            block.append(profile)
        return block
    return []


def remove_from_wishlist(userid, movieid):
    conn = sqlite3.connect('filmFinder/database_files/filmfinder.db')
    c = conn.cursor()
    c.execute(
        f" DELETE FROM WISHLIST WHERE userid = {int(userid)} and movieid = {int(movieid)} ")
    conn.commit()


def remove_from_blocklist(userid, blockid):
    conn = sqlite3.connect('filmFinder/database_files/filmfinder.db')
    c = conn.cursor()
    c.execute(
        f" DELETE FROM BLOCKING WHERE userid = {int(userid)} and blockid = {int(blockid)} ")
    conn.commit()


def blocklist_button(userid, blockid):
    conn = sqlite3.connect('filmFinder/database_files/filmfinder.db')
    c = conn.cursor()
    c.execute(
        f" SELECT userid, blockid FROM BLOCKING WHERE userid = {userid} AND blockid = {blockid} ")
    exist_check = c.fetchall()
    if not exist_check:
        c.execute(f"SELECT max(id) FROM blocking")
        maxid = c.fetchone()
        c.execute(
            f" INSERT INTO BLOCKING (id, userid, blockid) VALUES ({maxid[0]+1}, {userid}, {blockid}) ")
        conn.commit()
        return "Add to blocklist successfully."
    else:
        return "Already in blocklist"


def get_user_detail(userid):
    conn = sqlite3.connect('filmFinder/database_files/filmfinder.db')
    c = conn.cursor()
    c.execute(
        f" SELECT * FROM USERPROFILES WHERE id = {userid} ")
    user = c.fetchone()
    c.execute(f"SELECT SUM(like) FROM RATINGS WHERE userId = {userid}")
    like_sum = c.fetchone()
    if user:
        user_details = {'id': user[0], 'username': user[1],
                        'email': user[2], 'profile_image': user[4], 'like':like_sum[0]}
        return user_details
    else:
        return {}

def like_increment(ratingid):
    conn = sqlite3.connect('filmFinder/database_files/filmfinder.db')
    c = conn.cursor()
    c.execute(
        f" UPDATE RATINGS SET like = (like + 1) WHERE id = {ratingid} ")
    conn.commit()
