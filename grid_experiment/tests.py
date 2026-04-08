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
                "reported_symbol": "O",
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
                "comp1_q2": "scenario_o",
                "comp1_q3": "scenario_i",
                "comp1_q4": "action_a_always_better",
                "comp1_q5": "charity_depends_scenario",
            }
            # After passing, show the pass-notice screen
            yield ComprehensionPassNotice

        # Rounds 5+ are main rounds: no RoundSummary, but we still go through the task
        if p.round_number > 4 and p.round_number <= Constants.num_rounds:
            yield Submission(Stimulus, {}, check_html=False)
            yield Interpretation, {
                "reported_symbol": "O",
                "reported_symbol_rt": 0,
            }
            yield AllocationDecision, {
                "action_choice": "A",
                "action_choice_rt": 0,
            }

        # At the very end, answer belief and questionnaire, then show final page
        if p.round_number == Constants.num_rounds:
            # Belief about identification accuracy: always guess all main rounds correct for testing
            yield BeliefAccuracy, {"belief_identification_correct_count": Constants.num_rounds - 4}
            # Questionnaire: fill with simple placeholder values
            yield Questionnaire, {
                "age": 30,
                "gender_sex": "male",
                "education_level": "bachelor",
                "employment_status": "student",
                "student_level": "master",
                "field_of_study": "Test field",
                "self_altruism": 3,
                "donate_frequency": 2,
                "task_difficulty": 3,
                "study_purpose": "Testing the experiment code.",
            }
            # FinalPage has no submit button; use Submission with check_html=False
            yield Submission(FinalPage, {}, check_html=False)

