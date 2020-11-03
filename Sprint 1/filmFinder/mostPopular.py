# this file is written by Jiexin Zhou z5199357
# this file contains functions with static results
import sqlite3
import re



def genre_process(string):
    l = re.findall("'name': '[a-zA-Z ]{1,}'", string)
    l = [i[9:-1] for i in l]
    return l


def highest_rating_movies(num):
    conn = sqlite3.connect('filmFinder/database_files/filmfinder.db')
    c = conn.cursor()
    c.execute(
        'SELECT id, title, release_date, genres, poster_path, vote_average FROM FILMS WHERE vote_count > 5 ORDER BY vote_average DESC LIMIT ?', (num,))
    rows = c.fetchall()
    rows_dict = [{'id': x[0], 'title':x[1], 'release_date':x[2], 'genres':genre_process(
        x[3]), 'poster':x[4], 'vote_average':x[5]} for x in rows]

    return rows_dict


def most_popular_movies(num):
    conn = sqlite3.connect('filmFinder/database_files/filmfinder.db')
    c = conn.cursor()
    c.execute(
        'SELECT id, title, release_date, genres, poster_path, vote_average FROM FILMS ORDER BY vote_count DESC LIMIT ?', (num,))
    rows = c.fetchall()
    rows_dict = [{'id':x[0],'title':x[1], 'release_date':x[2], 'genres':genre_process(x[3]), 'poster':x[4], 'vote_average':x[5]} for x in rows]
    return rows_dict


def release_date(date1, date2, num):
    conn = sqlite3.connect('filmFinder/database_files/filmfinder.db')
    c = conn.cursor()
    c.execute(
        'SELECT title FROM FILMS WHERE release_date > ? AND release_date < ?  ORDER BY VOTE_COUNT DESC LIMIT ?', (date1, date2, num))
    rows = c.fetchall()
    # print('----------release date----------')
    # for row in rows:
    #     print(row)
    # print()
    return rows

# list element order:
# text, (check)
# genre, (check)
# country, (check)
# year1, (check)
# year2, (check)
# avg_rating (check)
def genenal_search(conditions, mode, offset):
    conn = sqlite3.connect('filmFinder/database_files/filmfinder.db')
    c = conn.cursor()

    text = conditions[0]
    genre = conditions[1]
    country = conditions[2]
    year1 = conditions[3]
    year2 = conditions[4]
    avg_rating = conditions[5]

    if text != None:
        name_str = f" title LIKE '%{text}%' "
        cast_str = f''' FILMS.id IN ( SELECT id FROM CREDITS WHERE (CREDITS.crew LIKE "%{text}%")) '''

    else:
        name_str = ''
        cast_str = ''

    if genre != []:
        if len(genre) == 1:
            genre_str = f" genres LIKE '%{genre[0]}%' "
        else:
            temp = []
            for g in genre:
                temp.append(f" genres LIKE '%{g}%' ")
            genre_str = ' AND '.join(temp)
    else:
        genre_str = ''

    if country != None:
        country_str = f" production_countries LIKE '%{country}%' "
    else:
        country_str = ''

    if year1 != None:
        year1_str = f" release_date >= {year1} "
    else:
        year1_str = ''

    if year2 != None:
        year2_str = f" release_date <= {year2} "
    else:
        year2_str = ''

    if avg_rating != None:
        avg_rating_str = f" vote_average >= {avg_rating} "
    else:
        avg_rating_str = ''

    text_list = [name_str, cast_str]
    text_list = [s for s in text_list if s != '']
    text_list = ' OR '.join(text_list)
    if text_list != '':
        text_list = '(' + text_list + ')'

    filter_list = [text_list, genre_str,
                   country_str, year1_str, year2_str, avg_rating_str]
    filter_list = [s for s in filter_list if s != '']
    filter_list = ' AND '.join(filter_list)
    if filter_list != '':
        filter_list = ' WHERE ' + filter_list
    else:
        join_str = ''
    order_str = ''
    if mode == 0:  # count
        order_str = f' ORDER BY VOTE_COUNT DESC LIMIT 10 OFFSET {offset} '
    elif mode == 1:
        if filter_list == '':
            order_str = f' WHERE VOTE_COUNT >= 50 ORDER BY VOTE_AVERAGE DESC LIMIT 10 OFFSET {offset} '
        else:
            order_str = f' AND VOTE_COUNT >= 50 ORDER BY VOTE_AVERAGE DESC LIMIT 10 OFFSET {offset} '
    general_search_sql = ' SELECT id FROM FILMS ' + filter_list + order_str
    # print(general_search_sql)
    c.execute(general_search_sql)
    results = c.fetchall()
    return results


def advanced_search1(conditions, mode, offset):
    conn = sqlite3.connect('filmFinder/database_files/filmfinder.db')
    c = conn.cursor()

    title = conditions[0]
    director = conditions[1]
    casts = conditions[2] 
    genre = conditions[3]
    country = conditions[4]
    year1 = conditions[5]
    year2 = conditions[6]
    avg_rating = conditions[7]

    if title != None:
        title_str = f" title LIKE '%{title}%' "
    else:
        title_str = ''
    
    if director != None:
        director_str = f''' FILMS.id IN ( SELECT id FROM CREDITS WHERE (CREDITS.crew LIKE "%{director}%")) '''
    else:
        director_str = ''

    if casts != None:
        casts_str = f''' FILMS.id IN ( SELECT id FROM CREDITS WHERE (CREDITS.casts LIKE "%{casts}%")) '''
    else:
        casts_str = ''

    if genre != []:
        if len(genre) == 1:
            genre_str = f" genres LIKE '%{genre[0]}%' "
        else:
            temp = []
            for g in genre:
                temp.append(f" genres LIKE '%{g}%' ")
            genre_str = ' AND '.join(temp)
    else:
        genre_str = ''

    if country != None:
        country_str = f" production_countries LIKE '%{country}%' "
    else:
        country_str = ''

    if year1 != None:
        year1_str = f" release_date >= {year1} "
    else:
        year1_str = ''

    if year2 != None:
        year2_str = f" release_date <= {year2} "
    else:
        year2_str = ''

    if avg_rating != None:
        avg_rating_str = f" vote_average >= {avg_rating} "
    else:
        avg_rating_str = ''

    filter_list = [title_str, director_str, casts_str, genre_str,
                   country_str, year1_str, year2_str, avg_rating_str]
    filter_list = [s for s in filter_list if s != '']
    filter_list = ' AND '.join(filter_list)
    if filter_list != '':
        filter_list = ' WHERE ' + filter_list
    else:
        join_str = ''
    order_str = ''
    if mode == 0:  # count
        order_str = f' ORDER BY VOTE_COUNT DESC LIMIT 10 OFFSET {offset} '
    elif mode == 1:
        if filter_list == '':
            order_str = f' WHERE VOTE_COUNT >= 50 ORDER BY VOTE_AVERAGE DESC LIMIT 10 OFFSET {offset} '
        else:
            order_str = f' AND VOTE_COUNT >= 50 ORDER BY VOTE_AVERAGE DESC LIMIT 10 OFFSET {offset} '
    general_search_sql = ' SELECT id FROM FILMS ' + filter_list + order_str
    #print(general_search_sql)
    c.execute(general_search_sql)
    results = c.fetchall()
    return results

#------------------------------------------TEST---------------------------------------


def test():
    conn = sqlite3.connect('filmFinder/database_files/filmfinder.db')
    c = conn.cursor()
    # c.execute(
    #     '''SELECT title, genres FROM FILMS WHERE title LIKE '%Matrix%' ORDER BY VOTE_COUNT DESC LIMIT 10''')
    c.execute('''SELECT title FROM FILMS WHERE FILMS.id IN (SELECT CREDITS.id FROM CREDITS WHERE CREDITS.crew LIKE "%'Director', 'name': 'John Lasseter'%") ''')
    rows = c.fetchall()
    print('----------test----------')
    for row in rows:
        print(row)
    print()


def general_search_test():
    test_list = []
    test_list.append(['Matrix', [], None, None, None, 4])
    test_list.append(['Matrix', ['Action', 'Thriller'], None, None, None, None])
    test_list.append([None, ['Action', 'Thriller'], None, None, None, 4])
    test_list.append([None, [], None, 1999, 2002, 3])
    test_list.append([None, [], 'CN', None, None, 3])
    test_list.append(['TOM HANKS', [], None, None, None, None])
    test_list.append(['Matrix', [], None, None, None, None])
    test_list.append([None, [], None, None, None, None])
    for case in test_list:
        print(genenal_search(case, 0, 1))


def advanced_search_test():
    test_list = []
    test_list.append(['Matrix',None, None, [], None, None, None, 4])
    test_list.append(
        ['Matrix', None, None, ['Action', 'Thriller'], None, None, None, None])
    test_list.append(
        [None, None, None, ['Action', 'Thriller'], None, None, None, 4])
    test_list.append([None, 'Stephen Spielberg', None, [], None, 1999, 2002, 3])
    test_list.append([None, None, None, [], 'CN', None, None, 3])
    test_list.append([None, None, 'TOM HANKS', [], None, None, None, None])
    test_list.append(['Matrix', None, None, [], None, None, None, None])
    test_list.append(['bridge', 'Steven Spielberg', 'TOM HANKS', [], None, None, None, None])
    test_list.append([None, None, None, [], None, None, None, None])
    for case in test_list:
        print(advanced_search1(case, 0, 0))


# release_date(1999, 2000, 10)
# highest_ratings(10)
# print(genre_process(most_popular_movies(10)[0]['genres']))
# print(most_popular_movies(10))
# general_search_test()
# advanced_search_test()
