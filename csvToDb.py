import pandas as pd 
import numpy as np
import glob
import os
import re
import sqlite3


def change_poster_names():
    print('Changing poster file names...')
    poster_path = glob.glob(
        'filmFinder/static/poster_downloads/*.jpg')
    for poster in poster_path:
        # print(poster[36])
        if poster[36] != '.':
            print('Changing poster file names...success')
            return poster_path
        prev = poster
        filepath = prev[:35]
        filename = prev[39:]
        
        padding = 11-len(filename)
        after = filepath+'tt'+padding*'0'+filename
        # print(after)
        os.rename(prev, after)
    print('Changing poster file names...success')
    return glob.glob(
        'filmFinder/static/poster_downloads/*.jpg')


if __name__ == "__main__":
    '''
    FUNCTION: SET UP DATABASE AND SET POSTER PATH
    INPUT: .CSV, .JPG
    OUTPUT: .DB .JPG
    STEPS:
        1. READ FROM movies_metadata.csv(TMDB_ID TO IMDB_ID MAPPING),  poster_downloads(IMDB_ID) folder
        2. SET POSTER_PATH BY CHANGING POSTER NAME TO IMDB_ID
        3. INTERSECT IMDB_ID WITH TMDB_ID, MAKE SURE ALL MOVIES HAVE POSTER, GENERATE FINAL FILM DATAFRAME
        4. READ FROM credits.csv, FILTER OUT ALL IRRELEVANT DATA
        5. RANDOMLY GENERATE USER DATA AND RATING DATA
        6. CREATING filmfinder.db DATABASE AND SET SCHEMA
        7. LOAD ALL DATA INTO DATABASE
    '''

    film_csv = 'filmFinder/the_movie_dataset/movies_metadata.csv'
    film_df = pd.read_csv(film_csv)
    film_df = film_df.drop(columns=['adult', 'budget', 'homepage', 'original_language', 'original_title', 'popularity',
                                    'production_companies', 'revenue', 'poster_path', 'runtime', 'spoken_languages', 'status', 'tagline', 'video'])
    film_df = film_df[['id', 'title', 'genres', 'belongs_to_collection', 'production_countries',
                       'release_date', 'overview', 'imdb_id', 'vote_average', 'vote_count']]
    film_df = film_df.drop([19730, 29503, 35587])
    imdb_film_id = list(set(film_df.imdb_id.unique().tolist()))
    
    poster_list = change_poster_names()

    poster_list = set([i[35:-4] for i in poster_list])

    final_film_df = pd.DataFrame()

    for i in range(len(imdb_film_id)):
        if imdb_film_id[i] in poster_list:
            matched_df = film_df.query(f"imdb_id == '{imdb_film_id[i]}'")
            final_film_df = final_film_df.append(matched_df)
            print('\r'+ f'Generating final film dataframe...{int(100*i/len(imdb_film_id))+1}%',end="", flush=True)

    print()
    print('Generating final film dataframe...success')
    
    row_num, col_num = final_film_df.shape
    print('Film row number correct.') if row_num == 8196 else print('ERROR:Film row number incorrect! Check file path.')
    final_film_df = final_film_df.rename(columns={'imdb_id': 'poster_path'})

    print('Loading credits data...')
    credits_csv = 'filmFinder/the_movie_dataset/credits.csv'
    credits_df = pd.read_csv(credits_csv)
    credits_df = credits_df[['id', 'cast', 'crew']]
    credits_df = credits_df.rename(columns={'cast': 'casts'})
    tmdb_film_id = list(set(final_film_df.id.unique().tolist()))
    print('Rearranging credits data...')
    for i, j in credits_df.iterrows():
        temp = re.search(
            ''''Director', 'name': ['|"][^,]{1,}['|"]''', j[2])
        if temp != None:
            credits_df.at[i, 'crew'] = temp.group()[20:]
    print('Droping irrelevant data...')
    for i, j in credits_df.iterrows():
        if str(j[0]) not in tmdb_film_id:
            credits_df = credits_df.drop([i])

    
    print('Loading&rearranging credits data...success')
    row_num, col_num = credits_df.shape
    print('Credits row number correct.') if row_num == 8196 else print(
        'ERROR:Credits row number incorrect! That is impossible.')


    # randomize rating and user profile
    '''
    GENERATE 500 USERS WITH ID 1-500
    EACH HAVE 1-20 RANDOM NUMBER OF RATINGS
    RATINGS SPREAD OVER 1-5 INTEGER
    NO REVIEW LEFT
    '''
    tmdb_film_id = np.array(list(set(final_film_df.id.unique().tolist())))
    # print(tmdb_film_id)
    np.random.seed(0); user_rate_num = np.random.randint(50, 100, size=500).tolist()
    rate_num = sum(user_rate_num)
    np.random.seed(0); user_rating =np.random.randint(1,6,size=rate_num)
    rating_index = np.array(range(1,rate_num+1))
    user_col = []
    movie_col = []

    for i in range(500):
        for j in range(user_rate_num[i]):
            np.random.seed(i); np.random.shuffle(tmdb_film_id)
            user_col.append(i+1)
            movie_col.append(tmdb_film_id[j])

    user_col = np.array(user_col)
    movie_col = np.array(movie_col)

    rating_table = np.append([user_col], [movie_col], axis=0)
    rating_table = np.append(rating_table, [user_rating], axis=0)
    rating_table = np.transpose(rating_table)
    rating_table = rating_table.astype(int)
    rating_df = pd.DataFrame(rating_table, columns=['userId', 'movieId', 'rating'])
    rating_df['review'] = ['No review.'] * \
        len(list(rating_df['rating'].tolist()))
    
    userId_list = list(set(rating_df['userId'].tolist()))
    name = [f'ID:{x}' for x in userId_list]
    email = [f'{x}@filmfinder.com' for x in userId_list]
    user_data = {'id': userId_list, 'username': name, 'email': email,
                'password': ['12345678']*len(userId_list), 'profile_image': ''}  # , 'birthday': ['1970-01-01']*len(userId_list)}
    user_profiles_df = pd.DataFrame(user_data)

    # create database
    print('Creating filmfinder.db...')
    database = 'filmFinder/database_files/filmfinder.db'
    if os.path.isfile(database):
        os.remove(database)
    conn = sqlite3.connect(database)
    c = conn.cursor()

    c.execute(
        '''
        CREATE TABLE USERPROFILES(
            [id] INTEGER NOT NULL PRIMARY KEY,
            [username] varchar(20) NOT NULL,
            [email] varchar(120) NOT NULL,
            [password] varchar(60) NOT NULL,
            [profile_image] VARCHAR(100) NOT NULL,
            UNIQUE (username),
            UNIQUE (email)
        )
        '''
    )

    c.execute(
        '''
        CREATE TABLE FILMS(
            [id] INTEGER PRIMARY KEY,
            [title] varchar,
            [genres] varchar,
            [belongs_to_collection] varchar,
            [production_countries] varchar,
            [release_date] date,
            [overview] text,
            [poster_path] text,
            [vote_average] float,
            [vote_count] integer
        )
        '''
    )

    c.execute(
        '''
        CREATE TABLE CREDITS(
            [id] integer PRIMARY KEY, 
            [casts] text,
            [crew] text,
            FOREIGN KEY (id) REFERENCES FILMS (id)
        )
        '''
    )

    c.execute(
        '''
        CREATE TABLE RATINGS(
            [index] INTEGER PRIMARY KEY, 
            [userId] integer, 
            [movieId] integer, 
            [rating] float,
            [review] text,
            FOREIGN KEY (userId) REFERENCES USERPROFILES (id),
            FOREIGN KEY (movieId) REFERENCES FILMS (id)
        )
        '''
    )

    c.execute(
        '''
        CREATE TABLE WISHLIST(
            [id] integer PRIMARY KEY NOT NULL,
            [userid] integer NOT NULL,
            [movieid] integer NOT NULL
        )
        '''
    )

    c.execute(
        '''
        CREATE TABLE BLOCKING(
            [id] integer PRIMARY KEY NOT NULL,
            [userid] integer NOT NULL,
            [blockid] integer NOT NULL
        )
        '''
    )


    conn.commit()
    print('Database filmfinder.db created...')
    print('Loading data to filmfinder.db...')
    conn = sqlite3.connect(database)
    c = conn.cursor()
    final_film_df['id'] = pd.to_numeric(final_film_df['id'], errors='ignore')


    final_film_df.to_sql('FILMS', conn, if_exists='replace', index=False)
    user_profiles_df.to_sql('USERPROFILES', conn,
                            if_exists='replace', index=False)
    rating_df.to_sql('RATINGS', conn, if_exists='replace', index=True)
    credits_df.to_sql('CREDITS', conn, if_exists='replace', index=None)
    print('Loading data to filmfinder.db... success')
    print('Finished!')
