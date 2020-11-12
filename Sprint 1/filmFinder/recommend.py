from sqlalchemy import or_
import numpy as np
import math
import re
from filmFinder.models import *
from sqlalchemy.sql.expression import func


# if collaborative_filtering is unable to continue, skip here
# return movieids randomly
def spare_recommend_method():
    # how many result to return
    result_num = 30
    return list(map(lambda x: x.movieId, RATINGS.query.order_by(func.random()).limit(result_num).all()))

# collaborative filtering based on user
# 1. get all the movies the user rated
# 2. get all the users who rated these movies
# 3. remove the users in blocking list
# 4. First filter, use Jaccard_value[len(A&B) / len(A|B)] to calculate the similarity
# 5. Second filter, use fixed cosine similarity to calculate the similarity on the result of first filter
# 6. use fixed cosine similarity as weight to calculate the mean rate of recommend movies
# 7. sort and return
def collaborative_filtering_user(userid):
    # only choose these top users
    top_user_num = 20
    # first choose times, means the first filter will choose (first_choose_times * top_user_num) users
    first_choose_times = 3

    # get all the film id this user has rated, return map type
    rated_films = set(map(lambda x: x.movieId, RATINGS.query.filter(RATINGS.userId == userid).all()))

    if len(rated_films) == 0:
        return spare_recommend_method()

    # get all other users who has rated these films
    similar_users = set(map(lambda x: x.userId, RATINGS.query.filter(or_(*[RATINGS.movieId == film_id for film_id in rated_films])).all()))
    similar_users.remove(userid)


    # get all other users who has been  blocked then remove them from similar_users
    block_users = set(map(lambda x: x.blockid, BLOCKING.query.filter(BLOCKING.userid == userid).all()))

    similar_users = list(similar_users - block_users)

    if len(similar_users) == 0:
        return spare_recommend_method()

    # input is "userid", output is "movieid1:rate1, movieid2:rate2,...}"
    def get_rate_data(userid):
        rate_data = {}
        for search_result in RATINGS.query.filter(RATINGS.userId == userid).all():
            rate_data[search_result.movieId]=search_result.rating
        return rate_data

    current_rate_data = get_rate_data(userid)

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
            rata_data = get_rate_data(compare_id)
            Jaccard_value_record[i] = get_Jaccard(current_key, set(rata_data.keys()))
        # find index of whose Jaccard_value is largest
        index_record = []
        while len(index_record) < first_choose_num:
            index = np.argmax(Jaccard_value_record)
            index_record.append(similar_users[index])
            Jaccard_value_record[index] = 0
        for index in index_record:
            rata_data = get_rate_data(index)
            first_filter_result.append((index, get_Jaccard(current_key, set(rata_data.keys())), rata_data))

    # second filter
    minus_value = sum(current_rate_data.values())/len(current_rate_data.values())
    for key in current_rate_data.keys():
        current_rate_data[key] = current_rate_data[key] - minus_value
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
        matrix2 = matrix2 - sum(compare_data.values())/len(compare_data.values())
        sim_value = np.dot(matrix1, matrix2) / (math.sqrt(np.dot(matrix1, matrix1)) * math.sqrt(np.dot(matrix2, matrix2)))
        return sim_value

    # get (userid, FCS_value, rata_data) as element
    second_filter_result = list(map(lambda x:(x[0], FCS(current_rate_data, x[2]), x[2]), first_filter_result))

    # used for sort
    def get_second_element(element):
        return element[1]

    second_filter_result.sort(key=get_second_element, reverse=True)
    if len(second_filter_result) > top_user_num:
        second_filter_result = second_filter_result[:top_user_num]

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

    # the final result is a list contain elements like (movie_id, simu_rate)
    result = []
    for key in recommend_movies.keys():
        # those films only rated by 1 user is not enough
        if recommend_movies[key][1] != 1:
            result.append((key, recommend_movies[key][0]/recommend_movies[key][1]))

    # now the final result is a sorted list contain elements like (movie_id, simu_rate)
    result.sort(key=get_second_element, reverse=True)
    recommend_ids = list(map(lambda x: x[0], result))

    # if length smaller than 8, random choose movies until have 8 ids
    if len(recommend_ids) < 8:
        recommend_ids = recommend_ids + \
                        list(map(lambda x: x.movieId, RATINGS.query.order_by(func.random()).limit(8-len(recommend_ids)).all()))

    return recommend_ids


# collaborative filtering based on item
# 1. get all the users who rated this movie
# 2. get all the movies these users rated
# 3. use len(A&B) / sqrt(len(A)*len(B)) to calculate the similarity
# 4. sort and return
def collaborative_filtering_item(movieId):
    # rate more than threshold will be thought as interested user
    threshold = 3

    def get_interested_users(movieId):
        search_result = RATINGS.query.filter(RATINGS.movieId == movieId).filter(RATINGS.rating >= threshold).all()
        return set(map(lambda x: x.userId, search_result))

    current_interested_users = get_interested_users(movieId)
    if len(current_interested_users) == 0:
        return spare_recommend_method()

    # get all other movies those users are interested in
    similar_movies = set(map(lambda x: x.movieId, RATINGS.query.filter(RATINGS.rating >= threshold).filter(
        or_(*[RATINGS.userId == user_id for user_id in current_interested_users])).all()))

    similar_movies.remove(movieId)
    if len(similar_movies) == 0:
        return spare_recommend_method()

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

    return result

# filter result based on the result of collaborative filtering based on items
# movieId is the current movie Id
# recommend_ids is the result of collaborative filtering based on items
# filtertype is '', 'genres', 'crew', 'production_countries', 'release_date'.
def item_based_result_filter(movieId, recommend_ids, filtertype):

    # split string to get names
    def split_names(input):
        result = re.findall("'name': '[a-zA-Z ]{1,}'", input)
        result = set([i[9:-1] for i in result])
        return result

    # get genres
    def get_movie_genres(id):
        result = Films.query.filter(Films.id == id).first()
        if result != None:
            result = result.genres
            result = split_names(result)
        else:
            result = set()
        return result

    # get crew
    def get_movie_crew(id):
        result = Credits.query.filter(Credits.id == id).first()
        if result != None:
            result = result.crew
        else:
            result = set()
        return result

    # get_movie_country
    def get_movie_countries(id):
        result = Films.query.filter(Films.id == id).first()
        if result != None:
            result = result.production_countries
            result = split_names(result)
        else:
            result = set()
        return result

    # get release_date
    def get_movie_date(id):
        result = Films.query.filter(Films.id == id).first()
        if result != None:
            result = result.release_date
        else:
            result = None
        return result


    # start to remove
    remove_list = []

    # filter depend on the filtertype
    if filtertype == '':
        pass

    elif filtertype == 'genres':
        for similar_id in recommend_ids:
            current_genres = get_movie_genres(movieId)
            if len(get_movie_genres(similar_id['id']) & current_genres) == 0:
                remove_list.append(similar_id)

    elif filtertype == 'crew':
        for similar_id in recommend_ids:
            current_crew = get_movie_crew(movieId)
            if get_movie_crew(similar_id['id']) != current_crew:
                remove_list.append(similar_id)

    elif filtertype == 'production_countries':
        for similar_id in recommend_ids:
            current_countries = get_movie_countries(movieId)
            if len(get_movie_countries(similar_id['id']) & current_countries) == 0:
                remove_list.append(similar_id)

    # remove all the movies' release_date difference more than 10 years
    elif filtertype == 'release_date':
        for similar_id in recommend_ids:
            current_date = get_movie_date(movieId)
            compare_date = get_movie_date(similar_id['id'])
            if compare_date == None:
                remove_list.append(similar_id)
            else:
                if abs(getattr((compare_date - current_date), 'days')) > 3650:
                    remove_list.append(similar_id)
    # end filter

    for similar_id in remove_list:
        recommend_ids.remove(similar_id)

    return recommend_ids
