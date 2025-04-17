from flask import Blueprint, render_template
from flask_login import current_user
from handicap.handicap import ScoringRecord

errors = Blueprint('errors', __name__)

@errors.app_errorhandler(404)
def error_404(error):
    player= current_user.name if current_user.is_authenticated else ""
    if player:
        sr = ScoringRecord(current_user.id)
        hi = sr.handicapIndex()
        del sr
    else:
        hi = None
    return render_template('errors/404.html', player=player, hi=hi), 404

@errors.app_errorhandler(403)
def error_403(error):
    player = current_user.name if current_user.is_authenticated else ""
    if player:
        sr = ScoringRecord(current_user.id)
        hi = sr.handicapIndex()
        del sr
    else:
        hi = None
    return render_template('errors/403.html', player=player, hi=hi), 403

@errors.app_errorhandler(500)
def error_500(error):
    player= current_user.name if current_user.is_authenticated else ""
    if player:
        sr = ScoringRecord(current_user.id)
        hi = sr.handicapIndex()
        del sr
    else:
        hi = None
    return render_template('errors/500.html', player=player, hi=hi), 500
