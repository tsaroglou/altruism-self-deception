from otree.api import Bot, Submission
from . import (
    Consent,
    Introduction,
    MappingInfo,
    Stimulus,
    Interpretation,
    AllocationDecision,
    RoundSummary,
    ComprehensionTest1,
    ComprehensionPassNotice,
    FinalPage,
    Constants,
)


class PlayerBot(Bot):
    def play_round(self):
        p = self.player

        # Round 1: consent + intro + mapping
        if p.round_number == 1:
            yield Consent, {"consent": "yes"}
            yield Introduction
            yield MappingInfo

        # Rounds 1-4: trial rounds with feedback
        if p.round_number <= 4:
            # Stimulus page has no submit button; use Submission with check_html=False
            yield Submission(Stimulus, {}, check_html=False)
            # Always choose X and Action A for testing; logic is what we care about here
            yield Interpretation, {
                "reported_symbol": "X",
                "view_again_count": 0,
                "reported_symbol_rt": 0,
            }
            yield AllocationDecision, {
                "action_choice": "A",
                "action_choice_rt": 0,
            }
            yield RoundSummary

        # After the 4th trial, do the first comprehension check (answer all correctly)
        if p.round_number == 4:
            yield ComprehensionTest1, {
                "comp1_q1": "true_scenario",
                "comp1_q2": "scenario_x",
                "comp1_q3": "scenario_o",
                "comp1_q4": "true_scenario",
            }
            # After passing, show the pass-notice screen
            yield ComprehensionPassNotice

        # Rounds 5+ are main rounds: no RoundSummary, but we still go through the task
        # This includes the very last round so that the app is on FinalPage after it.
        if p.round_number > 4 and p.round_number <= Constants.num_rounds:
            yield Submission(Stimulus, {}, check_html=False)
            yield Interpretation, {
                "reported_symbol": "X",
                "view_again_count": 0,
                "reported_symbol_rt": 0,
            }
            yield AllocationDecision, {
                "action_choice": "A",
                "action_choice_rt": 0,
            }

        # Final page at the very end (after the last main round)
        if p.round_number == Constants.num_rounds:
            # FinalPage has no submit button; use Submission with check_html=False
            yield Submission(FinalPage, {}, check_html=False)

