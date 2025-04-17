from copy import deepcopy
from flask import render_template, url_for, redirect, flash, request, abort, Blueprint
from flask_login import current_user, login_required
from handicap import db
from handicap.scores.forms import ScoreForm
from handicap.models import Score, IndexHistory
from handicap.handicap import ScoringRecord

scores = Blueprint('scores', __name__)

@scores.route("/allscores", methods=['GET', 'POST'])
def all_scores():
    page = request.args.get('page', 1, type=int)    # Default to page 1.
    per_page = request.args.get('per_page', 5, type=int)   # Default to 6 scores per page.#
    if current_user.is_authenticated:
        player = current_user.name
        player_record = ScoringRecord(current_user.id)
        current_index = player_record.handicapIndex()
        hi = round(current_index, 1) if current_index else None
        scores, page_nos = player_record.scorePage(per_page, page)
        show_page_buttons = len(page_nos) > 1
        del player_record
        # Adjust played dates format for display.  
        for score in scores:
            score.played = score.played.strftime('%d-%m-%Y')
    else:
        player = ""
        hi = None
        show_page_buttons = False
        scores = []
        page_nos = []
    #print(f"Scores length: {len(scores)}")
    return render_template('allscores.html', player=player, hi=hi,
                           login=current_user.is_authenticated,
                           len_scores=len(scores), scores=scores,
                           show_page_buttons=show_page_buttons,
                           page_nos=page_nos, page=page)

@scores.route('/score/new', methods=['GET', 'POST'])
@login_required
def new_score():
    form = ScoreForm(holes=18)                              # Default to 18 holes for convenience.
    if form.validate_on_submit():
        score = Score(played=form.played.data,
                      course_rating=form.rating.data,
                      course_slope=form.slope.data,
                      gross_adjusted_score=form.strokes.data,
                      course=form.course.data,
                      holes=form.holes.data,
                      # Compute the derived scoring differential.
                      score_differential=(form.strokes.data - form.rating.data) * 113 / form.slope.data,
                      user_id=current_user.id,
                      shot_by=current_user)
        scoring_record = ScoringRecord(current_user.id)
        #print(f"Old handicap index: {current_user.handicap_index}")
        current_user.handicap_index = scoring_record.addRound(score) # Add the score to the scoring record. (PJIS does this update the user's db record on commit? If not it should update the User record in handicap.py)
        #print(f"New handicap index: {current_user.handicap_index}")
        del scoring_record
        db.session.commit()
        flash('Your score has been added!', 'success')
        return redirect(url_for('main.home'))
    current_user.handicap_index = ScoringRecord(current_user.id).handicapIndex()
    return render_template('create_score.html', title='Add Round',
                           player=current_user.name, hi=current_user.handicap_index, 
                           form=form, legend='New Round')

@scores.route('/score/<int:score_id>')
def score(score_id):
    score = Score.query.get_or_404(score_id)
    if score.shot_by != current_user:
        abort(403)
    current_user.handicap_index = ScoringRecord(current_user.id).handicapIndex()
    score_date = score.played.strftime('%d-%m-%Y')
    return render_template('score.html', title='Round Score',
                           player=current_user.name if current_user.is_active else "",
                           hi=current_user.handicap_index if current_user.is_active else "",
                           score=score, played=score_date)

@scores.route('/score/<int:score_id>/update', methods=['GET', 'POST'])
@login_required
def update_score(score_id):
    score = Score.query.get_or_404(score_id)
    if score.shot_by != current_user:
        abort(403)
    remember_date = score.played
    form = ScoreForm()
    if form.validate_on_submit():
        # Update the score record. The scoring differential is recalculated.
        score.played = form.played.data
        score.gross_adjusted_score = form.strokes.data
        score.course_rating = form.rating.data
        score.course_slope = form.slope.data
        score.course = form.course.data
        score.holes = form.holes.data
        score.score_differential = (form.strokes.data - form.rating.data) * 113 / form.slope.data
        db.session.commit()
        # Update the index history record.
        scoring_record = ScoringRecord(current_user.id)
        handicap_index = scoring_record.handicapIndex()
        del scoring_record 
        index_history = IndexHistory.query.filter_by(user_id=current_user.id).all()
        update_ih = next((ih for ih in index_history if ih.handicap_index_date == remember_date), None)
        update_ih.handicap_index = handicap_index
        db.session.commit()
        flash('Your score has been updated!', 'success')
        return redirect(url_for('scores.score', score_id=score.id))
    elif request.method == 'GET':
        form.played.data = score.played
        form.strokes.data = score.gross_adjusted_score
        form.rating.data = score.course_rating
        form.slope.data = score.course_slope
        form.course.data = score.course
        form.holes.data = score.holes

    current_user.handicap_index = ScoringRecord(current_user.id).handicapIndex()
    return render_template('create_score.html', title='Update Score',
                           player=current_user.name, hi=current_user.handicap_index,
                           form=form, legend='Update Score')

@scores.route('/score/<int:score_id>/delete', methods=['POST'])
@login_required
def delete_score(score_id):
    score = Score.query.get_or_404(score_id)
    if score.shot_by != current_user:
        abort(403)
    db.session.delete(score)
    db.session.commit()
    flash('Your score has been deleted!', 'success')
    return redirect(url_for('main.home'))
