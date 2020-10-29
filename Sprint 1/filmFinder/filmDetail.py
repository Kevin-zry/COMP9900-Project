import sqlite3
import re


def re_process(string):
    l = re.findall("'name': '[a-zA-Z ]{1,}'", string)
    l = [i[9:-1] for i in l]
    return l


def get_movie_details(filmid):
    conn = sqlite3.connect('filmFinder/database_files/filmfinder.db')
    c = conn.cursor()
    filmid = int(filmid)
    c.execute(
        f'SELECT * FROM FILMS WHERE id = {filmid}')
    x = c.fetchone()
    detail = {'id': x[0], 'title': x[1], 'genres': re_process(x[2]), 'belongs_to_collection': re_process(x[3]), 'production_countries': re_process(x[4]),
                  'release_date':x[5], 'overview':x[6], 'poster_path':x[7], 'vote_average':x[8], 'vote_count':int(x[9])}
    c.execute(f'SELECT crew FROM CREDITS WHERE id = {filmid}')
    x = c.fetchone()
    detail['crew'] = x[0]
    return detail

def add_to_wishlist(userid):
    