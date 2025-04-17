from flask import render_template, Blueprint
from flask_login import current_user
from handicap.handicap import ScoringRecord

main = Blueprint('main', __name__)

@main.route("/")
@main.route("/home")
def home():
    if current_user.is_authenticated:
        player = current_user.name
        player_record = ScoringRecord(current_user.id)
        current_index = player_record.handicapIndex()
        hi = round(current_index, 1) if current_index else None
        scores = player_record.countingRounds()
        del player_record
        # Adjust played dates format for display.  
        for _, score, _ in scores:
            score.played = score.played.strftime('%d-%m-%Y')
    else:
        player = ""
        hi = None
        scores = []
    return render_template('home.html', player=player, hi=hi,
                           login=current_user.is_authenticated,
                           len_scores=len(scores), scores=scores)

@main.route("/about")
def about():
    if current_user.is_authenticated:
        player = current_user.name
        player_record = ScoringRecord(current_user.id)
        current_index = player_record.handicapIndex()
        del player_record
        hi = round(current_index, 1) if current_index else None
    else:
        player = ""
        hi = None
    return render_template('about.html', title='About', player=player, hi=hi)