from datetime import date, timedelta
from handicap import db
from handicap.models import User, Score, NineHoleScore, IndexHistory

class ScoringRecord():

    rounds: list[Score] = []
    years_handicaps: list[tuple[date, float]] = []     # Keep handicap indices of the previous year.
    handicap_index: float = None
    low_handicap_index: float = None
    low_handicap_index_date: date = None
    nine_hole_waiting: Score = None

    def __init__(self, player_id=None) -> None:
        self.player = User.query.get(player_id)
        self.rounds = self.player.scores
        self.handicap_index = self.player.handicap_index
        self.low_handicap_index = self.player.low_handicap_index
        self.low_handicap_index_date = self.player.low_handicap_index_date
        self.years_handicaps = [(HI.handicap_index_date, HI.handicap_index) for HI in self.player.indexes]
        self.nine_hole_waiting = None

    def scorePage(self, per_page: int, page: int, descending=True) -> tuple[list[Score], list[int | None]]:
        """
        Return all the rounds played by the player.

        Parameters:
        self (ScoringRecord): the self object.
        per_page (int): the number of rounds to display per page.
        page (int): the page number of the rounds to display.
        descending (bool): True for most recent rounds first, False for oldest round first.

        Returns:
        A tuple of:
        a list of Score objects for the rounds played by the player, and
        a list of page numbers for the pagination (None denotes elipses).
        """
        scores = Score.query.filter_by(user_id=self.player.id)\
                            .order_by(Score.played.desc() if descending else Score.played.asc())\
                            .paginate(page=page, per_page=per_page)

        page_nos = scores.iter_pages(left_edge=4, right_edge=1, left_current=1, right_current=2)

        return list(scores), list(page_nos)

    def countingRounds(self) -> list[Score]:
        """
        Return the rounds counting towards the player's handicap.

        Parameters:
        self (ScoringRecord): the self object.

        Returns:
        A 3-tuple list of up to 8 rounds played by the player, their index in the rounds window, 
        and the number of rounds in the rounds window.
        Typically, they are the 8 lowest score differentials of the 20 most recently played rounds,
        modified as scores are accumulated.
        """
        rounds_played = len(self.rounds)

        N = rounds_played

        if rounds_played < 3:
            return []
        elif rounds_played < 6:
            M = 1
        elif rounds_played < 9:
            M = 2
        elif rounds_played < 20:
            M = 3 if rounds_played < 12 else \
                4 if rounds_played < 15 else \
                5 if rounds_played < 17 else \
                6 if rounds_played < 19 else \
                7
        else:
            # rounds_played >= 20
            N = 20  # Get the 20 most recent rounds.
            M = 8   # Average of the lowest 8 rounds

        # Get the M best scoring differentials from the N most recent rounds.
        sorted_rounds = sorted(self.rounds, key=lambda x: x.played, reverse=True)
        N_most_recent = sorted_rounds[:N]
        # Index the round from 1 to n to show user where the counting round is in the list.
        N_indexed_rounds = [(index + 1, round, N) for index, round in enumerate(N_most_recent)]
        # Sort the 3-tuple list by the score differential.
        sorted_differentials = sorted(N_indexed_rounds, key=lambda x: x[1].score_differential)
        M_best_differentials = sorted_differentials[:M]

        # Restore the played date order for display.
        return sorted(M_best_differentials, key=lambda x: x[1].played, reverse=True)
    
    def addRound(self, golf_round: Score) -> str:

        if golf_round.holes == 9:
            if len(self.rounds) < 3:
                # Combine if a nine hole round is waiting
                self.nine_hole_waiting = NineHoleScore.query.filter_by(user_id=self.player.id).first()
                if self.nine_hole_waiting:
                    combine_9_hole_rounds = Score(played=golf_round.played, holes=18, user_id=self.player.id,
                                                  course_rating=golf_round.course_rating + self.nine_hole_waiting.course_rating,
                                                  course_slope=int(round((golf_round.course_slope + self.nine_hole_waiting.course_slope)/2, 1)),
                                                  gross_adjusted_score=golf_round.gross_adjusted_score + self.nine_hole_waiting.gross_adjusted_score,
                                                  score_differential = ((golf_round.gross_adjusted_score + self.nine_hole_waiting.gross_adjusted_score)
                                                                        - (golf_round.course_rating + self.nine_hole_waiting.course_rating)) * 113
                                                                        / (int(round((golf_round.course_slope + self.nine_hole_waiting.course_slope)/2, 1))),
                                                  course=f'Front 9: {self.nine_hole_waiting.course}, back 9: {golf_round.course}.')
                    NineHoleScore.query.filter_by(id=self.nine_hole_waiting.id).delete()
                    self.nine_hole_waiting = None
                else:
                    # Add the 9 hole round to wait for another to be added.
                    self.nine_hole_waiting = NineHoleScore(played=golf_round.played,
                                                           course_rating=golf_round.course_rating,
                                                           course_slope=golf_round.course_slope,
                                                           gross_adjusted_score=golf_round.gross_adjusted_score,
                                                           course=golf_round.course, user_id=self.player.id)
                    db.session.add(self.nine_hole_waiting)
                    db.session.commit()

                    return None

            else:   # 9 holes but 3 rounds already entered so 9 hole rounds made into 18 immediately.
                combine_9_hole_rounds = Score(played=golf_round.played, holes=18, user_id=self.player.id,
                                              course_rating=golf_round.course_rating * 2,
                                              course_slope=golf_round.course_slope,
                                              gross_adjusted_score=round(golf_round.gross_adjusted_score * 2 + 1),
                                              score_differential = ((golf_round.gross_adjusted_score * 2 + 1) - golf_round.course_rating * 2)
                                                                    * 113 / golf_round.course_slope,
                                              course=f'9 holes converted to 18: {golf_round.course}.')

            # Use the combined two nine hole scores or inflated 9 to 18 hole score to add to the score record
            golf_round = combine_9_hole_rounds
        
        # Add the 18 hole round to the scoring record.
        db.session.add(golf_round)
        db.session.commit()
        self.rounds.append(golf_round)
        # Calculate the new Handicap Index
        self.handicap_index = self.handicapIndex()
        # Add the new (date, handicap index) pair to the remembered handicaps list.
        # Used when the low handicap index must be replaced with the lowest from the preceding year.
        if self.handicap_index:   # There won't be a handicap index for 1st two rounds.
            # Add the new handicap index to the history.
            db.session.add(IndexHistory(handicap_index=self.handicap_index, handicap_index_date=golf_round.played, user_id=self.player.id))
            db.session.commit()
            self.years_handicaps.append((golf_round.played, self.handicap_index))
            # Only keep pairs within one year of the new round. There will always be at least the one being added.
            self.years_handicaps = [(HI_date, HI) for (HI_date, HI) in self.years_handicaps \
                                    if golf_round.played - HI_date <= timedelta(weeks=52)]

        # When a score is added, the Low Handicap Index is re-evaluated following the Handicap Index calculation.
        if len(self.rounds) >= 20:
            time_between_round_and_lowHI = abs(golf_round.played - self.low_handicap_index_date)
            if time_between_round_and_lowHI > timedelta(weeks=52):
                # reset the low HI to the lowest in the preceding year.
                self.low_handicap_index_date, self.low_handicap_index = \
                    sorted(self.years_handicaps, key=lambda x:x[1])[0]      # Sort by HI and use the first one
            # Check for exceptional score.
            check_exceptional_round = round(golf_round.score_differential - self.handicap_index, 1)
            if 7.0 <= check_exceptional_round <= 9.9:
                self.handicap_index -= 1.0
            elif check_exceptional_round >= 10:
                self.handicap_index -= 2.0

            if self.handicap_index < self.low_handicap_index:
                # Reset the low handicap to the new one just computed.
                self.low_handicap_index = self.handicap_index
                self.low_handicap_index_date = golf_round.played

            # Update the user's low handicap index and date.
            self.player.low_handicap_index = self.low_handicap_index
            self.player.low_handicap_index_date = self.low_handicap_index_date
            db.session.commit()    # Update the user's record.

        return self.handicap_index


    def handicapIndex(self) -> float:
        '''
        Calculate the handicap index from the scores stored in the record.

        Return.
        The handicap index calculation over the RoundsRecord, or
        None, if there were not enough rounds to compute a handicap index (< 3).
        '''

        rounds_played = len(self.rounds)

        if rounds_played < 3:
            return None
        
        N = rounds_played
        adjustment = 0

        if rounds_played < 6:
            M = 1
            adjustment = -2 if rounds_played == 3 else -1 if rounds_played == 4 else 0
        elif rounds_played < 9:
            M = 2
            adjustment = -1 if rounds_played == 6 else 0
        elif rounds_played < 20:
            M = 3 if rounds_played < 12 else \
                4 if rounds_played < 15 else \
                5 if rounds_played < 17 else \
                6 if rounds_played < 19 else \
                7
        else:
            # rounds_played >= 20
            N = 20  # Get the 20 most recent rounds.
            M = 8   # Average of the lowest 8 rounds

        sorted_rounds = sorted(self.rounds, key=lambda x: x.played, reverse=True)
        most_recent = sorted_rounds[:N]

        # Get the M best scoring differentials from the N most recent rounds.
        sorted_rounds = sorted(most_recent, key=lambda x: x.score_differential)
        best_differentials = sorted_rounds[:M]

        # Sum the M best scoring differentials and divide by M for the average.
        self.handicap_index = round(sum(round.score_differential for round in best_differentials) / M, 1)
        # The Low Handicap Index is established once there are 20 rounds in the record.
        if rounds_played == 20:
            self.low_handicap_index = self.handicap_index
            self.low_handicap_index_date = most_recent[0].played
        if rounds_played >= 20:
            # Apply the caps.
            if self.handicap_index - self.low_handicap_index > 3:
                restricted_amount = (self.handicap_index - (self.low_handicap_index + 3)) / 2   # 50% of additional amount
                self.handicap_index += restricted_amount
            if self.handicap_index - self.low_handicap_index > 5:
                self.handicap_index = self.low_handicap_index + 5
        else:
            # Apply the adjustment.
            self.handicap_index += adjustment

        # Maximum handicap.
        if self.handicap_index > 54:
            self.handicap_index = 54

        return self.handicap_index