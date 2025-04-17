from datetime import date
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, FloatField, IntegerField, DateField
from wtforms.validators import DataRequired, NumberRange, Optional, ValidationError, AnyOf

class ScoreForm(FlaskForm):
    course = StringField('Course Name', validators=[Optional()])
    played = DateField('Date', validators=[DataRequired()], format='%Y-%m-%d')
    strokes = IntegerField('Score (after adjustments, if any)', validators=[DataRequired()])
    rating = FloatField('Course Rating', validators=[DataRequired()])
    slope = IntegerField('Slope Rating', validators=[DataRequired(), NumberRange(min=55, max=155)])
    holes = IntegerField('Holes Played', validators=[Optional(), AnyOf(values=[9, 18])])
    submit = SubmitField('Post')

    def validate_strokes(self, strokes):
        if 27 >= strokes.data > 150:
            raise ValidationError('That score is unlikely.')
    
    def validate_played(self, played):
        today = date.today()
        if played.data > today:
            raise ValidationError('The date must be in the past.')