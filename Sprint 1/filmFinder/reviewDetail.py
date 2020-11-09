from flask import flash
from filmFinder import db
from filmFinder.models import BLOCKING, RATINGS, USERPROFILES


# Imput: current userid, movieid
# Output: list of form [review1, review2,...], where each element is a dict {title:..., userid:...}
# It does not contain reviews whose owner is in the block list

def get_review_details(current_user_id, movieId):
    block_users = []
    if current_user_id:
        block_users = set(map(lambda x: x.blockid, BLOCKING.query.filter(
            BLOCKING.userid == current_user_id).all()))
    reviews = RATINGS.query.filter(RATINGS.movieId == movieId).all()
    output = []
    for review in reviews:
        if review.userId not in block_users:
            review_info = {}
            user_info = USERPROFILES.query.filter(USERPROFILES.id == review.userId).first()
            review_info['id'] = review.id
            review_info['userId'] = review.userId
            review_info['username'] = user_info.username
            review_info['email'] = user_info.email
            review_info['profile_image'] = user_info.profile_image
            review_info['rating'] = review.rating
            review_info['review'] = review.review
            output.append(review_info)

    return output

# add or delete review
# userId, movieId, rating: int
# review: string

def add_review(userId, movieId, rating, review):
    if RATINGS.query.filter(RATINGS.userId == userId).filter(RATINGS.movieId == movieId).first() != None:
        flash('You have already written a review. Delete this to add a new one', category='danger')
    else:
        db.session.add(RATINGS(userId=userId, movieId=movieId, rating=rating, review=review))
    db.session.commit()


def delete_review(userId, movieId):
    user = RATINGS.query.filter(RATINGS.userId == userId).filter(RATINGS.movieId == movieId).first()
    db.session.delete(user)
    db.session.commit()

