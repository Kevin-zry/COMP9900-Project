from filmFinder.models import *

# import is the current userid and movieid
# output is a list [review1, review2,...]
# each element in list is a dict {userId:..., username:...}
# it does not contain reviews whose owner is in the block list
def get_review_datails(current_user_id, movieId):
    block_users = set(map(lambda x: x.blockid, BLOCKING.query.filter(BLOCKING.userid == current_user_id).all()))
    reviews = RATINGS.query.filter(RATINGS.movieId == movieId).all()
    output = []
    for review in reviews:
        if review.userId not in block_users:
            review_info = {}
            user_info = USERPROFILES.query.filter(USERPROFILES.id == review.userId).first()
            review_info['userId'] = review.userId
            review_info['username'] = user_info.username
            review_info['email'] = user_info.email
            review_info['profile_image'] = user_info.profile_image
            review_info['rating'] = review.rating
            review_info['review'] = review.review
            output.append(review_info)

    return output

# add or change review
# userId, movieId, rate is int
# review is a string
def add_or_change_review(userId, movieId, rating, review):
    if RATINGS.query.filter(RATINGS.userId == userId).filter(RATINGS.movieId == movieId).first() != None:
        RATINGS.query.filter(RATINGS.userId == userId).filter(RATINGS.movieId == movieId).update({'rating':rating, 'review':review})
    else:
        db.session.add(RATINGS(userId=userId, movieId=movieId, rating=rating, review=review))
    db.session.commit()

# delete review
def delete_review(userId, movieId):
    user = RATINGS.query.filter(RATINGS.userId == userId).filter(RATINGS.movieId == movieId).first()
    db.session.delete(user)
    db.session.commit()

