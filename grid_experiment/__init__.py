from otree.api import *
import random


doc = """
Altruism & self-deception experiment with O/I grid stimuli.
"""


class Constants(BaseConstants):
    name_in_url = "grid_experiment"
    players_per_group = None
    # 4 trial rounds (with feedback) + 28 main rounds (for payment)
    num_rounds = 32
    grid_rows = 7
    grid_cols = 7
    total_cells = grid_rows * grid_cols
    # 15 difficulty levels: majority counts from 25 (hardest) to 39 (easiest)
    difficulty_levels = [25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 37, 38, 39]
    identification_bonus = cu(1)
    payoffs = {
        "win_win": {
            "A": {"player": cu(7), "charity": cu(5)},
            "B": {"player": cu(5), "charity": cu(1.5)},
        },
        "moral_conflict": {
            "A": {"player": cu(7), "charity": cu(1.5)},
            "B": {"player": cu(5), "charity": cu(5)},
        },
    }


def scenario_label(symbol: str) -> str:
    return f"Scenario {symbol}"


def scenario_symbol_for(player, scenario_name: str) -> str:
    if scenario_name == "moral_conflict":
        return player.participant.vars["moral_symbol"]
    return player.participant.vars["win_symbol"]


def is_test_mode(player):
    return player.session.config.get("test_mode", False)


def num_main_rounds(player):
    return 2 if is_test_mode(player) else 28


def last_round(player):
    return 4 + num_main_rounds(player)


def beyond_plan(player):
    """True if this round has no plan entry (i.e. we are past the test-mode limit)."""
    plan_list = player.participant.vars.get("trial_plan", [])
    return player.round_number > len(plan_list)


def get_current_plan(player):
    ensure_participant_setup(player)
    plan_list = player.participant.vars["trial_plan"]
    return plan_list[player.round_number - 1]


def ensure_participant_setup(player):
    """Set up participant-level vars and return (moral_symbol, win_symbol)."""
    participant = player.participant
    if "moral_symbol" not in participant.vars or "win_symbol" not in participant.vars:
        moral_symbol, win_symbol = random.choice([("O", "I"), ("I", "O")])
        participant.vars["moral_symbol"] = moral_symbol
        participant.vars["win_symbol"] = win_symbol
    moral_symbol = participant.vars["moral_symbol"]
    win_symbol = participant.vars["win_symbol"]

    if "trial_plan" not in participant.vars:
        n_main = 2 if player.session.config.get("test_mode", False) else 28
        participant.vars["trial_plan"] = build_trial_plan(moral_symbol, win_symbol, n_main)

    return moral_symbol, win_symbol


def ensure_round_state(player):
    ensure_participant_setup(player)
    if beyond_plan(player):
        return
    if player.field_maybe_none("grid_pattern") is None:
        plan = get_current_plan(player)
        player.actual_scenario = plan["scenario"]
        player.difficulty = plan["difficulty"]
        player.majority_symbol = plan["majority_symbol"]
        player.minority_symbol = "I" if player.majority_symbol == "O" else "O"
        player.majority_count = plan["majority_count"]
        player.minority_count = Constants.total_cells - player.majority_count
        player.grid_pattern = plan["pattern"]


def make_grid_pattern(majority_symbol: str, majority_count: int) -> str:
    minority_symbol = "I" if majority_symbol == "O" else "O"
    minority_count = Constants.total_cells - majority_count
    cells = [majority_symbol] * majority_count + [minority_symbol] * minority_count
    random.shuffle(cells)
    return "".join(cells)


def to_rows(pattern: str):
    return [
        list(pattern[i : i + Constants.grid_cols])
        for i in range(0, len(pattern), Constants.grid_cols)
    ]


def build_trial_plan(moral_symbol: str, win_symbol: str, n_main: int = 28):
    """
    Build trial plan with:
    - 4 fixed trial rounds (practice, with feedback)
    - n_main main rounds (28 normally, 2 in test mode)
    """
    plan = []

    # Helper to add a single round config
    def add_round(o_count: int, i_count: int, is_trial: bool):
        if o_count + i_count != Constants.total_cells:
            raise ValueError("O and I counts must sum to total_cells")
        if o_count > i_count:
            majority_symbol = "O"
            majority_count = o_count
        elif i_count > o_count:
            majority_symbol = "I"
            majority_count = i_count
        else:
            # Tie should not happen with odd grid size, but guard anyway
            majority_symbol = random.choice(["O", "I"])
            majority_count = o_count

        # Determine scenario from which symbol is majority in this round
        if majority_symbol == moral_symbol:
            scenario = "moral_conflict"
        elif majority_symbol == win_symbol:
            scenario = "win_win"
        else:
            scenario = random.choice(["moral_conflict", "win_win"])

        pattern = make_grid_pattern(majority_symbol, majority_count)
        plan.append(
            dict(
                scenario=scenario,
                difficulty=str(majority_count),
                majority_symbol=majority_symbol,
                majority_count=majority_count,
                pattern=pattern,
                is_trial=is_trial,
            )
        )

    # 4 TRIAL ROUNDS (practice, non-paying)
    trial_pairs = [
        (39, 10),  # 39 O, 10 I
        (10, 39),  # 10 O, 39 I
        (25, 24),  # 25 O, 24 I
        (24, 25),  # 24 O, 25 I
    ]
    for o_count, i_count in trial_pairs:
        add_round(o_count, i_count, is_trial=True)

    # MAIN ROUNDS (for payment)
    main_pairs = []

    if n_main == 2:
        # Test mode: one extreme O-majority, one extreme I-majority
        main_pairs = [(49, 0), (0, 49)]
    else:
        # Extreme cases: 49-0 and 0-49, 2 times each
        main_pairs.extend([(49, 0)] * 2)
        main_pairs.extend([(0, 49)] * 2)

        # Mid-range cases (O - I) as provided (adjusted so O+I = 49)
        base_mid_o = [
            (21, 28),
            (22, 27),
            (23, 26),
            (24, 25),
        ]
        # Mirror cases where I is majority
        base_mid_i = [
            (28, 21),
            (27, 22),
            (26, 23),
            (25, 24),
        ]
        # Use each difficulty level three times (per orientation)
        for _ in range(3):
            main_pairs.extend(base_mid_o)
            main_pairs.extend(base_mid_i)

    if len(main_pairs) != n_main:
        raise ValueError(f"Expected {n_main} main-round configurations, got {len(main_pairs)}")

    # Randomize order of main rounds
    random.shuffle(main_pairs)

    for o_count, i_count in main_pairs:
        add_round(o_count, i_count, is_trial=False)

    return plan


class Subsession(BaseSubsession):
    def creating_session(self):
        for player in self.get_players():
            moral_symbol, _ = ensure_participant_setup(player)
            player.treatment = "O_moral_conflict" if moral_symbol == "O" else "I_moral_conflict"
            # In test mode, rounds beyond the plan length are skipped by is_displayed;
            # skip setup here too to avoid IndexError.
            if beyond_plan(player):
                continue
            plan = get_current_plan(player)
            player.actual_scenario = plan["scenario"]
            player.difficulty = plan["difficulty"]
            player.majority_symbol = plan["majority_symbol"]
            player.minority_symbol = "I" if player.majority_symbol == "O" else "O"
            player.majority_count = plan["majority_count"]
            player.minority_count = Constants.total_cells - player.majority_count
            player.grid_pattern = plan["pattern"]


class Group(BaseGroup):
    pass


class Player(BasePlayer):
    actual_scenario = models.StringField()
    difficulty = models.StringField()
    majority_symbol = models.StringField()
    minority_symbol = models.StringField()
    majority_count = models.IntegerField()
    minority_count = models.IntegerField()
    grid_pattern = models.LongStringField()

    reported_symbol = models.StringField(
        choices=[("O", "O"), ("I", "I")], widget=widgets.RadioSelect
    )
    # Reaction time (in seconds) for reporting the scenario symbol on the Interpretation page
    reported_symbol_rt = models.FloatField()

    action_choice = models.StringField(
        choices=[("A", "Action A"), ("B", "Action B")], widget=widgets.RadioSelect
    )
    # Reaction time (in seconds) for choosing an action on the AllocationDecision page
    action_choice_rt = models.FloatField()

    # Accuracy rate in the non-extreme main rounds
    # (computed and stored on the final round only; not shown to participants)
    mid_main_accuracy = models.FloatField()

    # Belief about main-task identification accuracy (number of correct identifications out of 24)
    belief_identification_correct_count = models.IntegerField(min=0, max=28)
    # Bonus for a correct belief about identification accuracy (paid regardless of which round is selected)
    belief_bonus = models.CurrencyField(initial=cu(0))

    # Demographics & questionnaire (asked at the end of the experiment)
    age = models.IntegerField(min=18, max=99)
    gender_sex = models.StringField(
        choices=[
            ("female", "Female"),
            ("male", "Male"),
            ("nonbinary", "Non-binary / other"),
            ("prefer_not_say", "Prefer not to say"),
        ],
    )
    education_level = models.StringField(
        choices=[
            ("less_than_high_school", "Less than high school"),
            ("high_school", "High school"),
            ("some_college", "Some college / vocational training"),
            ("bachelor", "Bachelor's degree"),
            ("master", "Master's degree"),
            ("doctorate", "Doctorate or equivalent"),
            ("other", "Other"),
        ],
    )
    employment_status = models.StringField(
        choices=[
            ("full_time", "Employed full-time"),
            ("full_time_student", "Employed full-time, Student"),
            ("part_time", "Employed part-time"),
            ("part_time_student", "Employed part-time, Student"),
            ("self_employed", "Self-employed"),
            ("unemployed", "Unemployed"),
            ("student", "Student"),
            ("other", "Other"),
        ],
    )
    student_level = models.StringField(
        choices=[
            ("none", "Not currently a student"),
            ("high_school", "High school"),
            ("bachelor", "Bachelor's level"),
            ("master", "Master's level"),
            ("doctorate", "Doctoral level"),
            ("other", "Other"),
        ],
    )
    field_of_study = models.StringField(
        choices=[
            ("economics_business", "Economics / Business"),
            ("law", "Law"),
            ("psychology", "Psychology / Cognitive Science"),
            ("political_science", "Political Science / International Relations"),
            ("philosophy", "Philosophy / Ethics"),
            ("medicine_health", "Medicine / Health Sciences"),
            ("engineering_cs", "Engineering / Computer Science"),
            ("natural_sciences", "Natural Sciences (Physics, Chemistry, Biology)"),
            ("mathematics_statistics", "Mathematics / Statistics"),
            ("humanities", "Humanities (History, Literature, Languages)"),
            ("social_sciences", "Social Sciences (Sociology, Anthropology)"),
            ("education", "Education"),
            ("arts_design", "Arts / Design"),
            ("other", "Other"),
        ],
    )
    self_altruism = models.IntegerField(
    label="How altruistic do you consider yourself to be?",
    choices=[
        [1, "Not at all altruistic"],
        [2, "Slightly altruistic"],
        [3, "Somewhat altruistic"],
        [4, "Moderately altruistic"],
        [5, "Very altruistic"],
        [6, "Extremely altruistic"],
    ],
    widget=widgets.RadioSelect,
    )
    donate_frequency = models.IntegerField(
    label="In the past 12 months, approximately how many times have you donated money to charity or a nonprofit organization?",
    choices=[
        [1, "0 times"],
        [2, "1 time"],
        [3, "2–3 times"],
        [4, "4–6 times"],
        [5, "7–11 times"],
        [6, "12 or more times"],
    ],
        widget=widgets.RadioSelect,
    )
    task_difficulty = models.IntegerField(
    label="How would you rate the difficulty level of the symbol task in this experiment?",
    choices=[
        [1, "Very easy"],
        [2, "Easy"],
        [3, "Somewhat easy"],
        [4, "Somewhat difficult"],
        [5, "Difficult"],
        [6, "Very difficult"],
    ],
    widget=widgets.RadioSelect,
    )
    study_purpose = models.LongStringField(
        label="What do you think this study was about? (max. 50 words)",
    )

    # Treatment assignment: "O_moral_conflict" or "I_moral_conflict"
    treatment = models.StringField(initial="")

    identification_correct = models.BooleanField(initial=False)
    identification_bonus_awarded = models.CurrencyField(initial=cu(0))
    charity_payoff = models.CurrencyField(initial=cu(0))
    consent = models.StringField(
        choices=[("yes", "I consent to participate"), ("no", "I do not consent")],
        widget=widgets.RadioSelect,
    )
    # Comprehension test answers (multiple choice)
    comp1_q1 = models.StringField(
        choices=[
            ("true_scenario", "The true active scenario, Scenario O"),
            ("reported_scenario", "The scenario I reported, Scenario I"),
        ],
        widget=widgets.RadioSelect,
    )
    comp1_q2 = models.StringField(
        choices=[
            ("scenario_o", "Scenario O"),
            ("scenario_i", "Scenario I"),
        ],
        widget=widgets.RadioSelect,
    )
    comp1_q3 = models.StringField(
        choices=[
            ("scenario_i", "Scenario I"),
            ("scenario_o", "Scenario O"),
        ],
        widget=widgets.RadioSelect,
    )
    comp1_q4 = models.StringField(
        choices=[
            ("action_a_always_better", "Action A always gives me more than Action B, regardless of which scenario is active."),
            ("depends_on_scenario", "Which action gives me more depends on which scenario is active."),
            ("action_b_always_better", "Action B always gives me more than Action A, regardless of which scenario is active."),
        ],
        widget=widgets.RadioSelect,
    )
    comp1_q5 = models.StringField(
        choices=[
            ("charity_a_both", "Action A, in both scenarios"),
            ("charity_b_both", "Action B, in both scenarios"),
            ("charity_depends_scenario", "It depends on which scenario is active"),
        ],
        widget=widgets.RadioSelect,
    )

    comp2_q1 = models.StringField(
        choices=[
            ("true_scenario", "The true active scenario, Scenario I"),
            ("reported_scenario", "The scenario I reported, Scenario O"),
        ],
        widget=widgets.RadioSelect,
    )
    comp2_q2 = models.StringField(
        choices=[
            ("scenario_i", "Scenario I"),
            ("scenario_o", "Scenario O"),
        ],
        widget=widgets.RadioSelect,
    )
    comp2_q3 = models.StringField(
        choices=[
            ("scenario_o", "Scenario O"),
            ("scenario_i", "Scenario I"),
        ],
        widget=widgets.RadioSelect,
    )
    comp2_q4 = models.StringField(
        choices=[
            ("5_points", "€5"),
            ("7_points", "€7"),
        ],
        widget=widgets.RadioSelect,
    )
    comp2_q5 = models.StringField(
        choices=[
            ("charity_payoff_constant", "The charity receives the same amount for a given action, regardless of which scenario is active"),
            ("charity_payoff_varies", "The charity's earnings for the same action can differ depending on which scenario is active"),
        ],
        widget=widgets.RadioSelect,
    )

    def grid_rows(self):
        if self.field_maybe_none("grid_pattern") is None:
            ensure_round_state(self)
        pattern = self.field_maybe_none("grid_pattern")
        if pattern is None:
            return []
        return to_rows(pattern)

    def set_outcomes(self):
        # identification accuracy & bonus
        if self.reported_symbol == self.majority_symbol:
            self.identification_correct = True
            self.identification_bonus_awarded = Constants.identification_bonus
        else:
            self.identification_correct = False
            self.identification_bonus_awarded = cu(0)

        # action payoffs
        payoff_info = Constants.payoffs[self.actual_scenario][self.action_choice]
        base_payoff = payoff_info["player"]
        self.charity_payoff = payoff_info["charity"]

        # final payoff
        self.payoff = base_payoff + self.identification_bonus_awarded


class Consent(Page):
    form_model = "player"
    form_fields = ["consent"]

    @staticmethod
    def is_displayed(player: Player):
        return player.round_number == 1

    @staticmethod
    def before_next_page(player: Player, timeout_happened):
        # Store consent at the participant level so it is available in all rounds
        player.participant.vars["consent"] = player.consent


class NoConsent(Page):
    @staticmethod
    def is_displayed(player: Player):
        return (
            player.round_number == 1
            and player.participant.vars.get("consent") == "no"
        )

    @staticmethod
    def vars_for_template(player: Player):
        player.participant.payoff = cu(0)
        return dict()


class Introduction(Page):
    @staticmethod
    def is_displayed(player: Player):
        return (
            player.round_number == 1
            and player.participant.vars.get("consent") == "yes"
        )

    @staticmethod
    def vars_for_template(player: Player):
        ensure_round_state(player)
        moral_symbol = player.participant.vars["moral_symbol"]
        win_symbol = player.participant.vars["win_symbol"]
        payoffs = Constants.payoffs
        payoffs_x = payoffs["moral_conflict"] if moral_symbol == "O" else payoffs["win_win"]
        payoffs_o = payoffs["win_win"] if moral_symbol == "O" else payoffs["moral_conflict"]
        return dict(
            num_rounds=Constants.num_rounds,
            grid_size=f"{Constants.grid_rows} × {Constants.grid_cols}",
            display_seconds=2,
            identification_bonus=Constants.identification_bonus,
            scenario_label_moral=scenario_label(moral_symbol),
            scenario_label_win=scenario_label(win_symbol),
            payoffs_x=payoffs_x,
            payoffs_o=payoffs_o,
        )


class MappingInfo(Page):
    @staticmethod
    def is_displayed(player: Player):
        return (
            player.round_number == 1
            and player.participant.vars.get("consent") == "yes"
        )

    @staticmethod
    def vars_for_template(player: Player):
        ensure_round_state(player)
        moral_symbol = player.participant.vars["moral_symbol"]
        win_symbol = player.participant.vars["win_symbol"]
        payoffs = Constants.payoffs
        payoffs_x = payoffs["moral_conflict"] if moral_symbol == "O" else payoffs["win_win"]
        payoffs_o = payoffs["win_win"] if moral_symbol == "O" else payoffs["moral_conflict"]
        return dict(
            moral_symbol=moral_symbol,
            win_symbol=win_symbol,
            scenario_label_moral=scenario_label(moral_symbol),
            scenario_label_win=scenario_label(win_symbol),
            payoffs=payoffs,
            payoffs_x=payoffs_x,
            payoffs_o=payoffs_o,
        )


class Stimulus(Page):
    timeout_seconds = 5
    timer_text = "Stimulus on screen"

    @staticmethod
    def is_displayed(player: Player):
        consent_ok = player.participant.vars.get("consent") == "yes"
        comp_passed = player.participant.vars.get("comp_passed", False)
        comp_failed = player.participant.vars.get("comp_failed", False)
        if not consent_ok or comp_failed or beyond_plan(player):
            return False
        if player.round_number <= 4:
            return True
        return comp_passed

    @staticmethod
    def vars_for_template(player: Player):
        ensure_round_state(player)
        return dict(
            grid_rows=player.grid_rows(),
            grid_cols=Constants.grid_cols,
            majority_symbol=player.majority_symbol,
            majority_count=player.majority_count,
            minority_symbol=player.minority_symbol,
            minority_count=player.minority_count,
            scenario_label_moral=scenario_label(player.participant.vars["moral_symbol"]),
            scenario_label_win=scenario_label(player.participant.vars["win_symbol"]),
            timeout_seconds=Stimulus.timeout_seconds,
        )


class Interpretation(Page):
    form_model = "player"
    form_fields = ["reported_symbol", "reported_symbol_rt"]

    @staticmethod
    def vars_for_template(player: Player):
        ensure_round_state(player)
        moral_symbol = player.participant.vars["moral_symbol"]
        win_symbol = player.participant.vars["win_symbol"]
        payoffs = Constants.payoffs
        # Always show Scenario O left, Scenario I right
        payoffs_x = payoffs["moral_conflict"] if moral_symbol == "O" else payoffs["win_win"]
        payoffs_o = payoffs["win_win"] if moral_symbol == "O" else payoffs["moral_conflict"]
        return dict(
            grid_rows=player.grid_rows(),
            grid_cols=Constants.grid_cols,
            moral_symbol=moral_symbol,
            win_symbol=win_symbol,
            scenario_label_moral=scenario_label(moral_symbol),
            scenario_label_win=scenario_label(win_symbol),
            payoffs=payoffs,
            payoffs_x=payoffs_x,
            payoffs_o=payoffs_o,
        )

    @staticmethod
    def error_message(player: Player, values):
        if values["reported_symbol"] not in {"O", "I"}:
            return "Please select which symbol you believe appeared more often."

    @staticmethod
    def is_displayed(player: Player):
        consent_ok = player.participant.vars.get("consent") == "yes"
        comp_passed = player.participant.vars.get("comp_passed", False)
        comp_failed = player.participant.vars.get("comp_failed", False)
        if not consent_ok or comp_failed or beyond_plan(player):
            return False
        if player.round_number <= 4:
            return True
        return comp_passed


class AllocationDecision(Page):
    form_model = "player"
    form_fields = ["action_choice", "action_choice_rt"]

    @staticmethod
    def is_displayed(player: Player):
        consent_ok = player.participant.vars.get("consent") == "yes"
        comp_passed = player.participant.vars.get("comp_passed", False)
        comp_failed = player.participant.vars.get("comp_failed", False)
        if not consent_ok or comp_failed or beyond_plan(player):
            return False
        if player.round_number <= 4:
            return True
        return comp_passed

    @staticmethod
    def vars_for_template(player: Player):
        ensure_round_state(player)
        payoffs = Constants.payoffs
        moral_symbol = player.participant.vars["moral_symbol"]
        win_symbol = player.participant.vars["win_symbol"]
        # Always show Scenario O left, Scenario I right
        payoffs_x = payoffs["moral_conflict"] if moral_symbol == "O" else payoffs["win_win"]
        payoffs_o = payoffs["win_win"] if moral_symbol == "O" else payoffs["moral_conflict"]
        
        reported_symbol = player.field_maybe_none("reported_symbol") or win_symbol
        if reported_symbol == moral_symbol:
            chosen_scenario = "moral_conflict"
            chosen_scenario_label = scenario_label(moral_symbol)
            chosen_scenario_symbol = moral_symbol
        elif reported_symbol == win_symbol:
            chosen_scenario = "win_win"
            chosen_scenario_label = scenario_label(win_symbol)
            chosen_scenario_symbol = win_symbol
        else:
            chosen_scenario = "win_win"
            chosen_scenario_label = scenario_label(win_symbol)
            chosen_scenario_symbol = win_symbol
        
        return dict(
            moral_symbol=moral_symbol,
            win_symbol=win_symbol,
            scenario_label_moral=scenario_label(moral_symbol),
            scenario_label_win=scenario_label(win_symbol),
            scenario=player.actual_scenario,
            payoffs=payoffs,
            payoffs_x=payoffs_x,
            payoffs_o=payoffs_o,
            chosen_scenario=chosen_scenario,
            chosen_scenario_label=chosen_scenario_label,
            chosen_scenario_symbol=chosen_scenario_symbol,
            chosen_payoffs=payoffs_x if chosen_scenario_symbol == "O" else payoffs_o,
            other_payoffs=payoffs_o if chosen_scenario_symbol == "O" else payoffs_x,
        )

    @staticmethod
    def before_next_page(player: Player, timeout_happened):
        player.set_outcomes()


class RoundSummary(Page):
    @staticmethod
    def is_displayed(player: Player):
        # Show feedback only for the 4 practice rounds
        return (
            player.participant.vars.get("consent") == "yes"
            and player.round_number <= 4
        )

    @staticmethod
    def vars_for_template(player: Player):
        moral_symbol = player.participant.vars["moral_symbol"]
        win_symbol = player.participant.vars["win_symbol"]
        payoffs = Constants.payoffs
        payoffs_x = payoffs["moral_conflict"] if moral_symbol == "O" else payoffs["win_win"]
        payoffs_o = payoffs["win_win"] if moral_symbol == "O" else payoffs["moral_conflict"]
        # reported_symbol can be None in edge cases; guard against that
        reported_symbol = player.field_maybe_none("reported_symbol") or ""
        # action_choice can be None in some edge cases (e.g. debugging); guard against that
        action_choice = player.field_maybe_none("action_choice")
        if action_choice and player.field_maybe_none("actual_scenario"):
            base_payoff = payoffs[player.actual_scenario][action_choice]["player"]
        else:
            base_payoff = cu(0)

        return dict(
            identification_correct=player.identification_correct,
            identification_bonus=player.identification_bonus_awarded,
            action_choice=action_choice or "",
            actual_scenario=player.actual_scenario,
            actual_scenario_symbol=scenario_symbol_for(player, player.actual_scenario)
            if player.actual_scenario
            else "",
            actual_scenario_label=scenario_label(
                scenario_symbol_for(player, player.actual_scenario)
            )
            if player.actual_scenario
            else "",
            charity_payoff=player.charity_payoff,
            total_rounds=Constants.num_rounds,
            player_payoff=player.payoff,
            base_payoff=base_payoff,
            moral_symbol=moral_symbol,
            win_symbol=win_symbol,
            payoffs_x=payoffs_x,
            payoffs_o=payoffs_o,
            reported_symbol=reported_symbol,
        )


class FinalPage(Page):
    @staticmethod
    def is_displayed(player: Player):
        return player.round_number == last_round(player) and player.participant.vars.get(
            "consent"
        ) == "yes"

    @staticmethod
    def vars_for_template(player: Player):
        pvars = player.participant.vars
        comp_failed = pvars.get("comp_failed", False)

        # If comprehension failed, no main-task earnings; show excluded screen
        if comp_failed:
            player.participant.payoff = cu(0)
            return dict(
                excluded=True,
                payment_round=None,
                payment_player_payoff=None,
                payment_charity_payoff=None,
            )

        # Compute accuracy in the non-extreme main rounds (majority_count < 49)
        # and store it for export (on the final-round player and in participant.vars).
        main_round_players = player.in_rounds(5, last_round(player))
        mid_round_players = [
            p for p in main_round_players if p.majority_count < Constants.total_cells
        ]
        if mid_round_players:
            correct_count = sum(1 for p in mid_round_players if p.identification_correct)
            accuracy = correct_count / len(mid_round_players)
        else:
            accuracy = 0.0
        player.mid_main_accuracy = accuracy
        pvars["mid_main_accuracy"] = accuracy

        # Choose one paying round from main-task rounds (rounds 5..num_rounds),
        # but do this only once and store it on the participant so that refreshing
        # the final page does not change the selected round.
        if "paying_round_number" in pvars:
            paying_round_number = pvars["paying_round_number"]
        else:
            # Fallback: derive a deterministic paying round from participant.code
            # (so even if participant.vars is not persisted in this request context,
            # refreshing the page will not change the selected round).
            main_round_numbers = list(range(5, last_round(player) + 1))
            seeded_rng = random.Random(player.participant.code)
            paying_round_number = seeded_rng.choice(main_round_numbers)
            pvars["paying_round_number"] = paying_round_number
        # Get this player's record in the chosen paying round
        payment_player = player.in_round(paying_round_number)
        round_payoff = payment_player.payoff
        belief_bonus = pvars.get("belief_bonus", cu(0))

        # Set participant.payoff to the true payment amount so SessionPayments
        # shows the correct figure (round earnings + belief bonus only).
        player.participant.payoff = round_payoff + belief_bonus

        # Store charity payoff for data export
        pvars["charity_payoff_selected_round"] = float(payment_player.charity_payoff)

        participation_fee = float(player.session.config.get("participation_fee", 5.0))
        total_euros = float(round_payoff + belief_bonus) + participation_fee

        return dict(
            excluded=False,
            payment_round=paying_round_number,
            payment_player_payoff=round_payoff,
            payment_charity_payoff=payment_player.charity_payoff,
            belief_bonus=belief_bonus,
            participation_fee_str=f"{participation_fee:.2f}",
            total_euros_str=f"{total_euros:.2f}",
        )


class BeliefAccuracy(Page):
    form_model = "player"
    form_fields = ["belief_identification_correct_count"]

    @staticmethod
    def is_displayed(player: Player):
        pvars = player.participant.vars
        consent_ok = pvars.get("consent") == "yes"
        comp_failed = pvars.get("comp_failed", False)
        return consent_ok and not comp_failed and player.round_number == last_round(player)

    @staticmethod
    def vars_for_template(player: Player):
        total_main_rounds = num_main_rounds(player)
        return dict(
            total_main_rounds=total_main_rounds,
        )

    @staticmethod
    def before_next_page(player: Player, timeout_happened):
        # Compute true number of correct identifications in main-task rounds
        main_round_players = player.in_rounds(5, last_round(player))
        correct_count = sum(1 for p in main_round_players if p.identification_correct)
        guess = player.field_maybe_none("belief_identification_correct_count")
        if guess is None:
            guess = -1
        if guess == correct_count:
            player.belief_bonus = cu(5)
        else:
            player.belief_bonus = cu(0)
        pvars = player.participant.vars
        pvars["belief_correct_main_identifications"] = correct_count
        pvars["belief_identification_guess"] = guess
        pvars["belief_bonus"] = player.belief_bonus


class Questionnaire(Page):
    form_model = "player"
    form_fields = [
        "age",
        "gender_sex",
        "education_level",
        "employment_status",
        "student_level",
        "field_of_study",
        "self_altruism",
        "donate_frequency",
        "task_difficulty",
        "study_purpose",
    ]

    @staticmethod
    def is_displayed(player: Player):
        pvars = player.participant.vars
        return (
            pvars.get("consent") == "yes"
            and player.round_number == last_round(player)
            and not pvars.get("comp_failed", False)
        )

    @staticmethod
    def before_next_page(player: Player, timeout_happened):
        pvars = player.participant.vars
        comp_failed = pvars.get("comp_failed", False)
        if comp_failed:
            return
        if "paying_round_number" not in pvars:
            main_round_numbers = list(range(5, last_round(player) + 1))
            pvars["paying_round_number"] = random.choice(main_round_numbers)


class ComprehensionTest1(Page):
    form_model = "player"
    form_fields = ["comp1_q1", "comp1_q2", "comp1_q3", "comp1_q4", "comp1_q5"]

    @staticmethod
    def is_displayed(player: Player):
        pvars = player.participant.vars
        return (
            pvars.get("consent") == "yes"
            and player.round_number == 4
            and not pvars.get("comp_passed", False)
            and not pvars.get("comp_failed", False)
        )

    @staticmethod
    def vars_for_template(player: Player):
        ensure_round_state(player)
        moral_symbol = player.participant.vars["moral_symbol"]
        win_symbol = player.participant.vars["win_symbol"]
        payoffs = Constants.payoffs
        payoffs_x = payoffs["moral_conflict"] if moral_symbol == "O" else payoffs["win_win"]
        payoffs_o = payoffs["win_win"] if moral_symbol == "O" else payoffs["moral_conflict"]
        return dict(
            payoffs_x=payoffs_x,
            payoffs_o=payoffs_o,
        )

    @staticmethod
    def before_next_page(player: Player, timeout_happened):
        pvars = player.participant.vars
        correct_answers = {
            "comp1_q1": "true_scenario",
            "comp1_q2": "scenario_o",
            "comp1_q3": "scenario_i",
            "comp1_q4": "action_a_always_better",
            "comp1_q5": "charity_depends_scenario",
        }
        wrong_fields = [
            f for f, expected in correct_answers.items()
            if getattr(player, f) != expected
        ]
        pvars["comp1_wrong_fields"] = wrong_fields
        if not wrong_fields:
            pvars["comp_passed"] = True
        else:
            pvars["needs_second_test"] = True


class ComprehensionTest2(Page):
    form_model = "player"
    form_fields = ["comp2_q1", "comp2_q2", "comp2_q3", "comp2_q4", "comp2_q5"]

    @staticmethod
    def is_displayed(player: Player):
        pvars = player.participant.vars
        return (
            pvars.get("consent") == "yes"
            and player.round_number == 4
            and pvars.get("needs_second_test", False)
            and not pvars.get("comp_passed", False)
            and not pvars.get("comp_failed", False)
        )

    @staticmethod
    def vars_for_template(player: Player):
        ensure_round_state(player)
        moral_symbol = player.participant.vars["moral_symbol"]
        win_symbol = player.participant.vars["win_symbol"]
        payoffs = Constants.payoffs
        payoffs_x = payoffs["moral_conflict"] if moral_symbol == "O" else payoffs["win_win"]
        payoffs_o = payoffs["win_win"] if moral_symbol == "O" else payoffs["moral_conflict"]
        return dict(
            payoffs_x=payoffs_x,
            payoffs_o=payoffs_o,
        )

    @staticmethod
    def before_next_page(player: Player, timeout_happened):
        pvars = player.participant.vars
        correct_answers = {
            "comp2_q1": "true_scenario",
            "comp2_q2": "scenario_i",
            "comp2_q3": "scenario_o",
            "comp2_q4": "5_points",
            "comp2_q5": "charity_payoff_varies",
        }
        all_correct = all(
            getattr(player, field) == expected
            for field, expected in correct_answers.items()
        )
        if all_correct:
            pvars["comp_passed"] = True
        else:
            pvars["comp_failed"] = True


class ComprehensionFailNotice(Page):
    @staticmethod
    def is_displayed(player: Player):
        pvars = player.participant.vars
        return (
            pvars.get("consent") == "yes"
            and player.round_number == 4
            and pvars.get("needs_second_test", False)
            and not pvars.get("comp_passed", False)
            and not pvars.get("comp_failed", False)
        )

    @staticmethod
    def vars_for_template(player: Player):
        pvars = player.participant.vars
        wrong_fields = set(pvars.get("comp1_wrong_fields", []))

        # Human-readable labels for each answer value
        choice_labels = {
            "comp1_q1": {
                "true_scenario": "The true active scenario, Scenario O",
                "reported_scenario": "The scenario I reported, Scenario I",
            },
            "comp1_q2": {
                "scenario_o": "Scenario O",
                "scenario_i": "Scenario I",
            },
            "comp1_q3": {
                "scenario_i": "Scenario I",
                "scenario_o": "Scenario O",
            },
            "comp1_q4": {
                "action_a_always_better": "Action A always gives me more than Action B, regardless of which scenario is active.",
                "depends_on_scenario": "Which action gives me more depends on which scenario is active.",
                "action_b_always_better": "Action B always gives me more than Action A, regardless of which scenario is active.",
            },
            "comp1_q5": {
                "charity_a_both": "Action A, in both scenarios",
                "charity_b_both": "Action B, in both scenarios",
                "charity_depends_scenario": "It depends on which scenario is active",
            },
        }

        meta = [
            dict(
                field="comp1_q1",
                number=1,
                question="If the true active scenario is Scenario O but you mistakenly report Scenario I, which scenario is used to calculate payoffs?",
                correct_value="true_scenario",
                correct="The true active scenario, Scenario O",
                explanation="Your report does not change which scenario is active. Payoffs are always determined by the TRUE active scenario — the one set by the actual grid majority — regardless of what you report.",
            ),
            dict(
                field="comp1_q2",
                number=2,
                question="If there are more O symbols on the grid, which scenario is the true active scenario?",
                correct_value="scenario_o",
                correct="Scenario O",
                explanation="The symbol that appears more often in the grid determines the active scenario. More O symbols → Scenario O is active.",
            ),
            dict(
                field="comp1_q3",
                number=3,
                question="If there are more I symbols on the grid, which scenario is the true active scenario?",
                correct_value="scenario_i",
                correct="Scenario I",
                explanation="More I symbols → Scenario I is active.",
            ),
            dict(
                field="comp1_q4",
                number=4,
                question="Which statement is true about your own payoff across the two scenarios?",
                correct_value="action_a_always_better",
                correct="Action A always gives me more than Action B, regardless of which scenario is active.",
                explanation="Your personal payoff depends only on the action you choose, not on which scenario is active. Action A always gives you €7 and Action B always gives you €5 in BOTH scenarios. The scenario only affects what the charity receives.",
            ),
            dict(
                field="comp1_q5",
                number=5,
                question="Across the two scenarios, which action gives the charity more?",
                correct_value="charity_depends_scenario",
                correct="It depends on which scenario is active",
                explanation="The charity's payoff from each action is not the same across both scenarios. Please review the payoff tables above carefully and compare what the charity receives from Action A and Action B in Scenario O versus Scenario I.",
            ),
        ]

        all_items = []
        for m in meta:
            participant_value = getattr(player, m["field"], None) or ""
            participant_answer = choice_labels[m["field"]].get(participant_value, participant_value)
            is_correct = m["field"] not in wrong_fields
            all_items.append(dict(
                number=m["number"],
                question=m["question"],
                participant_answer=participant_answer,
                is_correct=is_correct,
                correct=m["correct"],
                explanation=m["explanation"],
            ))

        moral_symbol = pvars.get("moral_symbol", "O")
        payoffs = Constants.payoffs
        payoffs_x = payoffs["moral_conflict"] if moral_symbol == "O" else payoffs["win_win"]
        payoffs_o = payoffs["win_win"] if moral_symbol == "O" else payoffs["moral_conflict"]
        return dict(
            all_items=all_items,
            payoffs_x=payoffs_x,
            payoffs_o=payoffs_o,
            identification_bonus=Constants.identification_bonus,
        )


class ComprehensionFinalFail(Page):
    @staticmethod
    def is_displayed(player: Player):
        pvars = player.participant.vars
        return (
            pvars.get("consent") == "yes"
            and player.round_number == 4
            and pvars.get("comp_failed", False)
        )


class ComprehensionPassNotice(Page):
    @staticmethod
    def is_displayed(player: Player):
        pvars = player.participant.vars
        return (
            pvars.get("consent") == "yes"
            and player.round_number == 4
            and pvars.get("comp_passed", False)
            and not pvars.get("comp_failed", False)
        )


page_sequence = [
    Consent,
    NoConsent,
    Introduction,
    MappingInfo,
    Stimulus,
    Interpretation,
    AllocationDecision,
    RoundSummary,
    ComprehensionTest1,
    ComprehensionFailNotice,
    ComprehensionTest2,
    ComprehensionFinalFail,
    ComprehensionPassNotice,
    BeliefAccuracy,
    Questionnaire,
    FinalPage,
]

