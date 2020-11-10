'''
YOU NEED TO HAVE THE DATABASE GENERATED FIRST.
'''

import pandas as pd
import numpy as np
import sqlite3
from filmFinder import bcrypt
import random


database = 'filmFinder/database_files/filmfinder.db'
conn = sqlite3.connect(database)
c = conn.cursor()
c.execute(f"SELECT id FROM FILMS")
movieid_list = [movieid[0] for movieid in c.fetchall()]

'''
User Detail
'''
user_num = 500
userId_list = np.array((range(1, user_num+1))).tolist()
name = [f"user{(7-len(str(x)))*'0'}{x}" for x in userId_list]
email = [f'{x}@filmfinder.com' for x in userId_list]
user_data = {'id': userId_list, 'username': name, 'email': email,
             'password': [bcrypt.generate_password_hash('12345678').decode('utf-8')]*len(userId_list), 'profile_image': '', 'like': np.zeros((user_num)).astype(int)}
user_profiles_df = pd.DataFrame(user_data)

'''
Review & Rating
'''
rating_lb = 50
rating_ub = 100
np.random.seed(0)
user_rate_num = np.random.randint(rating_lb, rating_ub, size=user_num).tolist()
rate_num = sum(user_rate_num)
np.random.seed(0)
user_rating = np.random.randint(1, 10, size=rate_num)


def half(x): return 0.5*x


user_rating = np.array([half(x) for x in user_rating])
rating_index = np.array(range(1, rate_num+1))
user_col = []
wl_user_col = []
movie_col = []
wl_movie_col = []
for i in range(user_num):
    np.random.seed(i)
    np.random.shuffle(movieid_list)
    for j in range(user_rate_num[i]):
        user_col.append(i+1)
        wl_user_col.append(i+1)
        movie_col.append(movieid_list[j])
        wl_movie_col.append(movieid_list[j*2])

id_col = np.array(range(1, rate_num+1))
user_col = np.array(user_col)
movie_col = np.array(movie_col)
like_col = np.zeros((rate_num)).astype(int)
rating_table = np.append([id_col], [user_col], axis=0)
rating_table = np.append(rating_table, [movie_col], axis=0)
rating_table = np.append(rating_table, [user_rating], axis=0)
rating_table = np.append(rating_table, [like_col], axis=0)
rating_table = np.transpose(rating_table)
rating_df = pd.DataFrame(rating_table, columns=['id', 
                         'userId', 'movieId', 'rating', 'like'])
rating_df = rating_df.astype(
    {'userId': 'int32', 'movieId': 'int32', 'rating': 'float', 'like': 'int32'})
positive_review = ['This movie is so good!', 'Best film I have ever seen.',
                   'Definately going to watch again.', 'Worth an Oscar!']
netural_review = ['Casts did well but scripts boring.',
                  'Just a little above average', 'Below my expection a bit on some points.']
negative_review = ['Do not want to watch again!!', 'Waste my two hours time watching it', 'This movie is so bad!', 'Not worth watching at all!']
for i, j in rating_df.iterrows():
    print(
        '\r' + f'Generating reviews...{int(100*i/rate_num)+1}%', end="", flush=True)
    rating = j['rating']
    if rating >= 3.5:
        rating_df.loc[i, 'review'] = random.choice(positive_review)
    elif rating >= 1.5:
        rating_df.loc[i, 'review'] = random.choice(netural_review)
    else:
        rating_df.loc[i, 'review'] = random.choice(negative_review)


'''
Wishlist
'''
wl_user_col = np.array(wl_user_col)
wl_movie_col = np.array(wl_movie_col)
wl_id_col = np.array(range(rate_num))
wishlist_table = np.append([wl_id_col], [wl_user_col], axis=0)
wishlist_table = np.append(wishlist_table, [wl_movie_col], axis=0)
wishlist_table = np.transpose(wishlist_table)
wishlist_table = wishlist_table.astype(int)
wishlist_df = pd.DataFrame(wishlist_table, columns=["id", "userid", "movieid"])

'''
Blocklist
'''
block_lb = 1
block_ub = 20
user_block_num = np.random.randint(block_lb, block_ub, size=user_num).tolist()
block_table = np.zeros((sum(user_block_num), 3)).astype(int)
user_list = [i for i in range(1, user_num + 1)]
count = -1
for userid in range(user_num):
    np.random.seed(userid)
    np.random.shuffle(user_list)
    for i in range(user_block_num[userid]):
        count += 1
        block_table[count][0] = count
        block_table[count][1] = userid+1
        block_table[count][2] = user_list[i]
block_df = pd.DataFrame(block_table, columns=['id', 'userid', 'blockid'])
'''
import to database
'''
# print(user_profiles_df)
# print(rating_df)
# print(wishlist_df)
# print(block_df)
user_profiles_df.to_sql('USERPROFILES', conn, if_exists='replace', index=False)
rating_df.to_sql('RATINGS', conn, if_exists='replace', index=False)
wishlist_df.to_sql('WISHLIST', conn, if_exists='replace', index=False)
block_df.to_sql('BLOCKING', conn, if_exists='replace', index=False)
