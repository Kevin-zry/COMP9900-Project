#from filmFinder import db
#from filmFinder.models import BLOCKING, RATINGS, Films

#from flask import Flask
#from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import or_
import numpy as np
import math
import re
from filmFinder.models import *
from sqlalchemy.sql.expression import func

# 无法协同过滤时的应急推荐机制，随机推荐电影
'''
    当协同过滤算法无法正常计算时跳转到这里
    1. 该电影或者用户没有任何评分
    2. 该电影或者用户的相似电影/用户为空
    此时，随机返回电影
'''
def spare_recommend_method():
    # how many result to return
    result_num = 30
    return list(map(lambda x: x.movieId, RATINGS.query.order_by(func.random()).limit(result_num).all()))


# 基于用户的协同过滤算法
'''
    1、获取该用户所有评论过的电影
    2、获取所有评论过这些电影的用户
    3、去除在blocking列表中的用户
    4、提取这些用户的评分数据
    5、第一层过滤器，使用Jaccard系数（交集数/并集数）快速过滤出（first_choose_times*top_user_num）个用户, 双方评分过的所有电影，交集数量/并集数量
    6、第二层过滤器，使用修正余弦相似度（将每个用户减去自身的平均分后求余弦相似度）在第一次的结果中得到top_user_num个相关性最高的用户
    7、按照（相似度*评分）求和的方式对该用户所有还没评分，但是相似用户评分的电影点评进行加权平均
    8、返回模拟评分最高的电影
'''
# collaborative filtering based on user
def collaborative_filtering_user(userid):
    # only choose these top users
    top_user_num = 20
    # first choose times, means the first filter will choose (first_choose_times * top_user_num) users
    first_choose_times = 3

    # get all the film id this user has rated, return map type
    #reviewed_films = np.array(RATINGS.query.filter(RATINGS.userId == userid).with_entities(RATINGS.movieId).all()).flatten()
    rated_films = set(map(lambda x: x.movieId, RATINGS.query.filter(RATINGS.userId == userid).all()))
    #print("movies has been rated:",rated_films)
    #print()

    #reviewed_films = [result.movieId for result in RATINGS.query.filter(RATINGS.userId == userid).all()]
    if len(rated_films) == 0:
        return spare_recommend_method()

    # get all other users who has rated these films
    similar_users = set(map(lambda x: x.userId, RATINGS.query.filter(or_(*[RATINGS.movieId == film_id for film_id in rated_films])).all()))
    #similar_users = set([result.userId for result in RATINGS.query.filter(or_(*[RATINGS.movieId == film_id for film_id in reviewed_films])).all()])
    #print(similar_users)
    similar_users.remove(userid)
    #print(similar_users)
    # print("length of similar users with block users:", len(similar_users))


    # get all other users who has been  blocked then remove them from similar_users
    block_users = set(map(lambda x: x.blockid, BLOCKING.query.filter(BLOCKING.userid == userid).all()))

    # print("block users:",block_users)

    similar_users = list(similar_users - block_users)

    # print("length of similar users without block users:", len(similar_users))

    if len(similar_users) == 0:
        return spare_recommend_method()

    # input is "userid", output is "movieid1:rate1, movieid2:rate2,...}"
    def get_rate_data(userid):
        rate_data = {}
        for search_result in RATINGS.query.filter(RATINGS.userId == userid).all():
            rate_data[search_result.movieId]=search_result.rating
        return rate_data

    current_rate_data = get_rate_data(userid)
    # print("the rate of user:", current_rate_data)
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
    current_key = set(current_rate_data.keys())

    if len(similar_users) < first_choose_num:
        for compare_id in similar_users:
            rata_data = get_rate_data(compare_id)
            first_filter_result.append((compare_id, get_Jaccard(current_key, set(rata_data.keys())), rata_data))
    else:
        Jaccard_value_record = np.zeros(len(similar_users))
        # record all Jaccard_value
        for i in range(len(similar_users)):
            compare_id = similar_users[i]
            # print(len(first_filter_result), min_Jaccard_value)
            rata_data = get_rate_data(compare_id)
            Jaccard_value_record[i] = get_Jaccard(current_key, set(rata_data.keys()))
        #print("Jaccard_value_record",Jaccard_value_record)
        # find index of whose Jaccard_value is largest
        index_record = []
        while len(index_record) < first_choose_num:
            index = np.argmax(Jaccard_value_record)
            index_record.append(similar_users[index])
            Jaccard_value_record[index] = 0
        #print("index_record",index_record )
        for index in index_record:
            rata_data = get_rate_data(index)
            first_filter_result.append((index, get_Jaccard(current_key, set(rata_data.keys())), rata_data))

    #print("after first filter:", len(first_filter_result), first_filter_result[:5])


    # second filter
    minus_value = sum(current_rate_data.values())/len(current_rate_data.values())
    for key in current_rate_data.keys():
        current_rate_data[key] = current_rate_data[key] - minus_value
    #print(current_rate_data)
    # use fixed cosine similarity
    def FCS(current_data, compare_data):
        keys1 = current_data.keys()
        keys2 = compare_data.keys()
        index = list(keys1 & keys2)
        length = len(index)
        matrix1 = np.zeros(length)
        matrix2 = np.zeros(length)
        for i in range(length):
            matrix1[i] = current_data[index[i]]
            matrix2[i] = compare_data[index[i]]
        #return np.corrcoef(matrix1, matrix2)[0][1]
        #matrix1 = matrix1 - 2.5
        matrix2 = matrix2 - sum(compare_data.values())/len(compare_data.values())
        sim_value = np.dot(matrix1, matrix2) / (math.sqrt(np.dot(matrix1, matrix1)) * math.sqrt(np.dot(matrix2, matrix2)))
        #print(sim_value, matrix1, matrix2)
        return sim_value

    # get (userid, FCS_value, rata_data) as element
    second_filter_result = list(map(lambda x:(x[0], FCS(current_rate_data, x[2]), x[2]), first_filter_result))
    #print("similar users after first filter:",list(map(lambda x: x[0], second_filter_result)))

    # used for sort
    def get_second_element(element):
        return element[1]

    second_filter_result.sort(key=get_second_element, reverse=True)
    if len(second_filter_result) > top_user_num:
        second_filter_result = second_filter_result[:top_user_num]

    #print("after second filter:", len(second_filter_result), list(map(lambda x:(x[0],x[1]),second_filter_result)))

    # generate recommend movies
    # rated_films is the films rated by the current user
    # recommend_movies records {movieid:(simu_rate_sum, mark_num)}
    recommend_movies = {}
    for record in second_filter_result:
        for movie in record[2].keys():
            # if the current user has not rated the film
            if movie not in rated_films:
                if movie not in recommend_movies:
                    #print(record[1],type(record[1]))
                    #print(record[2][movie], type(record[2][movie]))
                    recommend_movies[movie] = (record[1] * record[2][movie], 1)
                    #print(record[1], record[2][movie], record[1] * record[2][movie], 1)
                else:
                    recommend_movies[movie] = (recommend_movies[movie][0] + record[1] * record[2][movie], recommend_movies[movie][1]+1)
                    #print(record[1], record[2][movie], record[1] * record[2][movie], 1)

    #print("recommend_movies",recommend_movies)
    # the final result is a list contain elements like (movie_id, simu_rate)
    result = []
    for key in recommend_movies.keys():
        # those films only rated by 1 user is not enough
        if recommend_movies[key][1] != 1:
            result.append((key, recommend_movies[key][0]/recommend_movies[key][1]))

    # now the final result is a sorted list contain elements like (movie_id, simu_rate)
    result.sort(key=get_second_element, reverse=True)
    #print("the sorted result is:", result)
    recommend_ids = list(map(lambda x: x[0], result))
    #print(type(recommend_ids[0]))

    # if length smaller than 8, random choose movies until have 8 ids
    if len(recommend_ids) < 8:
        recommend_ids = recommend_ids + \
                        list(map(lambda x: x.movieId, RATINGS.query.order_by(func.random()).limit(8-len(recommend_ids)).all()))

    return recommend_ids

# get genres
def get_movie_genres(id):
    result = Films.query.filter(Films.id == id).first()
    if result != None:
        result = result.genres
        result = re.findall("'name': '[a-zA-Z ]{1,}'", result)
        result = [i[9:-1] for i in result]
        result = set(result)
    else:
        result = set()
    return result


# 基于物品的协同过滤算法
'''
    1、将所有评分大于阈值的用户设置为偏好该物品的用户，得到每部电影对应的喜好用户集合
    2、对类型有重合的电影，用交集长度/sqrt(双方长度之积)得到物品的相似度
    3、筛选出想要的相似度靠前的电影
'''
# collaborative filtering based on item
def collaborative_filtering_item(movieId):
    # rate more than threshold will be thought as interested user
    threshold = 3

    def get_interested_users(movieId):
        search_result = RATINGS.query.filter(RATINGS.movieId == movieId).filter(RATINGS.rating >= threshold).all()
        return set(map(lambda x: x.userId, search_result))

    current_interested_users = get_interested_users(movieId)
    current_genres = get_movie_genres(movieId)
    if len(current_interested_users) == 0:
        return spare_recommend_method()

    # get all other movies those users are interested in
    similar_movies = set(map(lambda x: x.movieId, RATINGS.query.filter(RATINGS.rating >= threshold).filter(
        or_(*[RATINGS.userId == user_id for user_id in current_interested_users])).all()))

    similar_movies.remove(movieId)
    if len(similar_movies) == 0:
        return spare_recommend_method()

    # only remain those movies has same genres
    remove_list = []
    for similar_id in similar_movies:
        if len(get_movie_genres(similar_id) & current_genres) == 0:
            remove_list.append(similar_id)
    if len(similar_movies) - len(remove_list) < 8:
        if len(similar_movies) < 8:
            remove_list = []
        else:
            remove_list = remove_list[:len(similar_movies)-8]
    for similar_id in remove_list:
            similar_movies.remove(similar_id)

    # calculate similar weight
    similar_movies = list(similar_movies)
    record = np.zeros(len(similar_movies))
    for i in range(len(similar_movies)):
        compare_movie_id = similar_movies[i]
        compare_users = get_interested_users(compare_movie_id)
        w = len(current_interested_users & compare_users)/ math.sqrt(len(current_interested_users)*len(compare_users))
        record[i] = w

    result = []

    while len(result) < len(record):
        index = np.argmax(record)
        result.append(similar_movies[index])
        record[index] = 0

    # if length smaller than 8, random choose movies until have 8 ids
    if len(result) < 8:
        result = result + \
                 list(map(lambda x: x.movieId,RATINGS.query.order_by(func.random()).limit(8 - len(result)).all()))

    return result



# 根据电影id获取电影名，用于测试
def get_movie_name(id):
    result = Films.query.filter(Films.id == id).first()
    if result != None:
        return result.title
    else:
        return None
