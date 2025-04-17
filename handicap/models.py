from typing import List, Optional
from datetime import date
from itsdangerous import URLSafeTimedSerializer as Serialiser # allows confirmed data coming back as sent in password updating.
from flask_login import UserMixin
from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from flask_mail import Message
from flask import url_for, current_app as app
from handicap import db, login_manager, mail

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

class User(db.Model, UserMixin):
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[Optional[str]] = mapped_column(String(40))
    email: Mapped[str] = mapped_column(unique=True)
    image_file: Mapped[str] = mapped_column(String(20), default='default.jpg')
    password: Mapped[int] = mapped_column(String(60))   # Will be 60 characetr hash values
    handicap_index: Mapped[Optional[float]]
    low_handicap_index: Mapped[Optional[float]]
    low_handicap_index_date: Mapped[Optional[date]]

    scores: Mapped[List['Score']] = relationship(back_populates='shot_by', cascade='all, delete-orphan')
    indexes: Mapped[List['IndexHistory']] = relationship(back_populates='player', cascade='all, delete-orphan')
    nine_hole_scores: Mapped[List['NineHoleScore']] = relationship(back_populates='shot_by', cascade='all, delete-orphan')

    def get_reset_token(self):
        s = Serialiser(app.config['SECRET_KEY'], salt='password-reset')
        token = s.dumps({'user_id': self.id})
        return token
    
    def send_reset_email(self):
        token = self.get_reset_token()
        msg = Message('Message from Handicap Index', sender='phil@cluesome.com', recipients=[self.email])
        msg.body = f'''To reset your password, visit the following link:
{url_for('users.reset_token', token=token, _external=True)}

The link will expire after 30 minutes.
If you did not make this request, please ignore this email.
'''
        mail.send(msg)
  
    @staticmethod
    def verify_reset_token(token, expires_sec=60*30):   # 30 minutes.
        s = Serialiser(app.config['SECRET_KEY'], salt='password-reset')
        try:
            user_id = s.loads(token, max_age=expires_sec)['user_id']
        except:
            return None
        return User.query.get(user_id)    

    def __repr__(self):
        quote = "'"
        quote_comma = "', "
        comma_quote = ", '"
        return f"User({self.id}, {quote + self.name + quote_comma if self.name else ''}'{self.email}', '{self.image_file}'" + \
                    f"{' ' + str(round(self.handicap_index, 1)) if self.handicap_index else ''}" + \
                    f"{', ' + str(round(self.low_handicap_index, 1)) + ',' if self.low_handicap_index else ''}" + \
                    f"{' ' + str(self.low_handicap_index_date) if self.low_handicap_index_date else ''})"

class Score(db.Model):
    id: Mapped[int] = mapped_column(primary_key=True)
    played: Mapped[date]
    course_rating: Mapped[float]
    course_slope: Mapped[int]
    gross_adjusted_score: Mapped[int]
    course: Mapped[Optional[str]]
    holes: Mapped[int] = mapped_column(default=18)
    score_differential: Mapped[float]
    user_id: Mapped[int] = mapped_column(ForeignKey('user.id'))
    shot_by: Mapped['User'] = relationship(back_populates='scores')

    def __repr__(self):
        return f"Score({self.id}, '{self.played}', {self.course_rating}, {self.course_slope}, {self.gross_adjusted_score}, '{self.course}', {self.score_differential}, {self.user_id})"

class NineHoleScore(db.Model):
    id: Mapped[int] = mapped_column(primary_key=True)
    played: Mapped[date]
    course_rating: Mapped[float]
    course_slope: Mapped[int]
    gross_adjusted_score: Mapped[int]
    course: Mapped[Optional[str]]
    user_id: Mapped[int] = mapped_column(ForeignKey('user.id'))
    shot_by: Mapped['User'] = relationship(back_populates='nine_hole_scores')

    def __repr__(self):
        return f"NineHoleScore({self.id}, '{self.played}', {self.course_rating}, {self.course_slope}, {self.gross_adjusted_score}, '{self.course}', {self.user_id})"
    
class IndexHistory(db.Model):
    id: Mapped[int] = mapped_column(primary_key=True)
    handicap_index: Mapped[float]
    handicap_index_date: Mapped[date]
    user_id: Mapped[int] = mapped_column(ForeignKey('user.id'))

    player: Mapped['User'] = relationship(back_populates='indexes')

    def __repr__(self):
        return f"IndexHistory({self.id}, {self.handicap_index}, '{self.handicap_index_date}', {self.user_id})"