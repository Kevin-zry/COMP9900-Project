from datetime import datetime
from filmFinder import db, login_manager
from flask_login import UserMixin

@login_manager.user_loader
def load_user(user_id):
    return USERPROFILES.query.get(int(user_id))


class USERPROFILES(db.Model, UserMixin):
    __tablename__ = 'USERPROFILES'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    username = db.Column(db.String(20), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(60), nullable=False)
    profile_image = db.Column(db.String(100), nullable=False, default='default.jpg')
    like = db.Column(db.Integer, default=0)
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
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    userId = db.Column(db.Integer, db.ForeignKey('USERPROFILES.id'))
    movieId = db.Column(db.Integer, db.ForeignKey('FILMS.id'))
    rating = db.Column(db.Float)
    review = db.Column(db.Text(collation='NOCASE'))


class FOLLOWING(db.Model):
    __tablename__ = 'FOLLOWING'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    userid = db.Column(db.Integer)
    movieid = db.Column(db.Integer)


class BLOCKING(db.Model):
    __tablename__ = 'BLOCKING'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    userid = db.Column(db.Integer)
    blockid = db.Column(db.Integer)


class WISHLIST(db.Model):
    __tablename__ = 'WISHLIST'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    userid = db.Column(db.Integer)
    movieid = db.Column(db.Integer)


# class Review(db.Model):
#     id = db.Column(db.Integer, primary_key=True)
#     rating = db.Column(db.Integer)  # 0-5
#     content = db.Column(db.Text, nullable=False)
#     date_posted = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
#     user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

#     def __repr__(self):
#         return f"Post_{self.id}('{self.rating}', '{self.date_posted}')"
