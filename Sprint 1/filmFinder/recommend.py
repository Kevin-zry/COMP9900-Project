#from filmFinder import db
#from filmFinder.models import BLOCKING, RATINGS, Films

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import or_
import numpy as np
import random



# -------------------------------------------------------------------------------------------------------------for test
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database_files/filmfinder.db'
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)

class USERPROFILES(db.Model):
    __tablename__ = 'USERPROFILES'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    username = db.Column(db.String(20), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(60), nullable=False)
    profile_image = db.Column(db.String(100), nullable=False, default='default.jpg')
    # reviews = db.relationship('Review', backref='author', lazy=True)

    def __repr__(self):
        return f'USERPROFILES_{self.id}({self.username}, {self.email}, {self.profile_image})'


class Films(db.Model):
    __tablename__ = 'FILMS'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    title = db.Column(db.String(collation='NOCASE'))
    genres = db.Column(db.String(collation='NOCASE'))
    belongs_to_collection = db.Column(db.String(collation='NOCASE'))
    production_countries = db.Column(db.String(collation='NOCASE'))
    release_date = db.Column(db.Date)
    overview = db.Column(db.Text(collation='NOCASE'))
    poster_path = db.Column(db.Text(collation='NOCASE'))
    vote_average = db.Column(db.Float)
    vote_count = db.Column(db.Integer)

class Credits(db.Model):
    __tablename__ = 'CREDITS'
    id = db.Column(db.Integer, db.ForeignKey('FILMS.id'), primary_key=True)
    cast = db.Column(db.Text(collation='NOCASE'))
    crew = db.Column(db.Text(collation='NOCASE'))

class RATINGS(db.Model):
    __tablename__ = 'RATINGS'
    index = db.Column(db.Integer, primary_key=True, autoincrement=True)
    userId = db.Column(db.Integer, db.ForeignKey('USERPROFILES.id'))
    movieId = db.Column(db.Integer, db.ForeignKey('FILMS.id'))
    rating = db.Column(db.Float)
    reviews = db.Column(db.Text(collation='NOCASE'))
    timestamp = db.Column(db.Integer)

class FOLLOWING(db.Model):
    __tablename__ = 'FOLLOWING'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    idx = db.Column(db.Integer)
    idy = db.Column(db.Integer)


class BLOCKING(db.Model):
    __tablename__ = 'BLOCKING'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    idx = db.Column(db.Integer)
    idy = db.Column(db.Integer)


# --------------------------------下面为推荐算法的部分，上面的部分都可以无视---------------------------------------------
# 无法协同过滤时的应急推荐机制，随机推荐高评分电影，未完成
def spare_recommend_method():
    return "error"





# 基于用户的协同过滤算法
'''
    1、获取该用户所有评论过的电影
    2、获取所有评论过这些电影的用户
    3、去除在blocking列表中的用户
    4、提取这些用户的评分数据
    5、第一层过滤器，使用Jaccard系数快速过滤出（first_choose_times*top_user_num）个用户
    6、第二层过滤器，使用皮尔逊相关系数在第一次的结果中得到top_user_num个相关性最高的用户
       将得到的皮尔逊相关系数从[-1,1]的取值范围转换到[0,1]的取值范围中
    7、按照（相似度*评分）求和的方式对该用户所有还没评分，但是相似用户评分的电影点评
    8、返回top_movie_num个模拟评分最高的电影
'''

# collaborative filtering based on user
def collaborative_filtering_user(userid):
    '''
        Here is config.
    '''
    # only choose these top users
    top_user_num = 10
    # first choose times, means the first filter will choose (first_choose_times * top_user_num) users
    first_choose_times = 2
    # only recommend these top movies from top users
    top_movie_num = 10
    '''
        Config end.
    '''


    # get all the film id this user has rated, return map type
    #reviewed_films = np.array(RATINGS.query.filter(RATINGS.userId == userid).with_entities(RATINGS.movieId).all()).flatten()
    rated_films = set(map(lambda x:x.movieId, RATINGS.query.filter(RATINGS.userId == userid).all()))
    print("movies has been rated:",rated_films)
    print()

    #reviewed_films = [result.movieId for result in RATINGS.query.filter(RATINGS.userId == userid).all()]
    if len(rated_films) == 0:
        return spare_recommend_method()

    # get all other users who has rated these films
    similar_users = set(map(lambda x:x.userId, RATINGS.query.filter(or_(*[RATINGS.movieId == film_id for film_id in rated_films])).all()))
    #similar_users = set([result.userId for result in RATINGS.query.filter(or_(*[RATINGS.movieId == film_id for film_id in reviewed_films])).all()])
    similar_users.remove(userid)
    print("length of similar users with block users:", len(similar_users))

    # get all other users who has been  blocked then remove them from similar_users
    block_users = set(map(lambda x:x.idy, BLOCKING.query.filter(BLOCKING.idx == userid).all()))
    print("block users:",block_users)
    similar_users = similar_users - block_users

    print("length of similar users without block users:", len(similar_users))

    if len(similar_users) == 0:
        return spare_recommend_method()

    # for fast test-----------------------------------------------------------------------------------------------
    similar_users = random.sample(similar_users, 30)
    print("for fast debug, random decrease user number to:",len(similar_users))


    # input is "userid", output is "movieid1:rate1, movieid2:rate2,...}"
    def get_rate_data(userid):
        rate_data = {}
        for search_result in RATINGS.query.filter(RATINGS.userId == userid).all():
            rate_data[search_result.movieId]=search_result.rating
        return rate_data

    current_rate_data = get_rate_data(userid)
    print("the rate of user:", current_rate_data)
    # rate_data is look like [userid, {movieid1: rate1, movieid2:rate2...}]

    # first filter
    first_choose_num = first_choose_times * top_user_num
    # use Jaccard to save time
    def get_Jaccard(key1, key2):
        value1 = len(key1&key2)
        if value1 == 0:
            return 0
        value2 = len(key1|key2)
        return value1/value2

    # store (userid, Jaccard_value, rata_data)
    first_filter_result = []
    min_Jaccard_value = 1
    current_key = set(current_rate_data.keys())
    # here use most time in progress
    for compare_id in similar_users:
        #print(len(first_filter_result), min_Jaccard_value)
        rata_data = get_rate_data(compare_id)
        Jaccard_value = get_Jaccard(current_key, set(rata_data.keys()))
        if len(first_filter_result) < first_choose_num:
            first_filter_result.append((compare_id, Jaccard_value, rata_data))
            if Jaccard_value < min_Jaccard_value:
                min_Jaccard_value = Jaccard_value
        else:
            if Jaccard_value > min_Jaccard_value:
                already_remove = False
                still_exist_the_min_value = False
                for record in first_filter_result:
                    if record[1] == min_Jaccard_value:
                        if already_remove == False:
                            first_filter_result.remove(record)
                            already_remove = True
                        elif still_exist_the_min_value == False:
                            still_exist_the_min_value = True
                            break
                if still_exist_the_min_value == False:
                    min_Jaccard_value = Jaccard_value
                first_filter_result.append((compare_id, Jaccard_value, rata_data))

    print("after first filter:", len(first_filter_result), first_filter_result[:5])

    # second filter
    # use Pearson Correlation Coefficient, but return in range[0,1]
    def CPC(rate_data1, rate_data2):
        keys1 = rate_data1.keys()
        keys2 = rate_data2.keys()
        index = list(keys1 | keys2)
        length = len(index)
        matrix1 = np.zeros(length)
        matrix2 = np.zeros(length)
        for i in range(length):
            if index[i] not in keys1:
                matrix1[i] = 0
            else:
                matrix1[i] = rate_data1[index[i]]
            if index[i] not in keys2:
                matrix2[i] = 0
            else:
                matrix2[i] = rate_data2[index[i]]
        # because Pearson Correlation Coefficient is in range[-1,1], so +1 and /2 here for generate movie sium_rates
        return (np.corrcoef(matrix1, matrix2)[0][1]+1)/2

    # get (userid, CPC_value, rata_data) as element
    second_filter_result = list(map(lambda x:(x[0], CPC(current_rate_data, x[2]), x[2]), first_filter_result))

    # used for sort
    def get_second_element(element):
        return element[1]

    second_filter_result.sort(key=get_second_element, reverse=True)
    if len(second_filter_result) > top_user_num:
        second_filter_result = second_filter_result[:top_user_num]

    print("after second filter:", len(second_filter_result), second_filter_result[:5])

    # generate recommend movies
    # rated_films is the films rated by the current user
    # recommend_movies records {movieid:(simu_rate_sum, mark_num)}
    recommend_movies = {}
    for record in second_filter_result:
        for movie in record[2].keys():
            # if the current user has not rated the film
            if movie not in rated_films:
                if movie not in recommend_movies:
                    recommend_movies[movie] = (record[1] * record[2][movie], 1)
                else:
                    recommend_movies[movie] = (recommend_movies[movie][0] + record[1] * record[2][movie], recommend_movies[movie][1]+1)
    '''
    print()
    for key in recommend_movies.keys():
        print(key, "  ", recommend_movies[key])
    print()
    '''
    # the final result is a list contain elements like (movie_id, simu_rate)
    result = []
    for key in recommend_movies.keys():
        result.append((key, recommend_movies[key][0]/recommend_movies[key][1]))

    # now the final result is a sorted list contain elements like (movie_id, simu_rate)
    result.sort(key=get_second_element, reverse=True)
    if len(result) > top_movie_num:
        result = result[:top_movie_num]
    print("the sorted result is:", result)


    return result





collaborative_filtering_user(1)
