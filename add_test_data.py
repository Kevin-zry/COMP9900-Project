
from filmFinder import app, db
from filmFinder.models import USERPROFILES, RATINGS
from random import randrange

for i in range(1, 21):
    rating = RATINGS(index=50000 + i, userId=500 + i, movieId=856 + i,
                     rating=randrange(1, 5), review=f'review content {i}')
    db.session.add(rating)

db.session.commit()
