from otree.api import *
import random


doc = """
Altruism & self-deception experiment with X/O grid stimuli.
"""


class Constants(BaseConstants):
    name_in_url = "grid_experiment"
    players_per_group = None
    # 4 trial rounds (with feedback) + 24 main rounds (for payment)
    num_rounds = 28
    grid_rows = 7
    grid_cols = 7
    total_cells = grid_rows * grid_cols
    # 15 difficulty levels: majority counts from 25 (hardest) to 39 (easiest)
    difficulty_levels = [25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 37, 38, 39]
    identification_bonus = cu(1)
    view_again_cost = cu(0.5)
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


def get_view_again_cost(player):
    return Constants.view_again_cost


def scenario_label(symbol: str) -> str:
    return f"Scenario {symbol}"


def scenario_symbol_for(player, scenario_name: str) -> str:
    if scenario_name == "moral_conflict":
        return player.participant.vars["moral_symbol"]
    return player.participant.vars["win_symbol"]


def get_current_plan(player):
    ensure_participant_setup(player)
    plan_list = player.participant.vars["trial_plan"]
    return plan_list[player.round_number - 1]


def ensure_participant_setup(player):
    participant = player.participant
    if "moral_symbol" not in participant.vars or "win_symbol" not in participant.vars:
        moral_symbol, win_symbol = random.choice([("X", "O"), ("O", "X")])
        participant.vars["moral_symbol"] = moral_symbol
        participant.vars["win_symbol"] = win_symbol
    moral_symbol = participant.vars["moral_symbol"]
    win_symbol = participant.vars["win_symbol"]

    participant.vars["view_again_cost"] = get_view_again_cost(player)

    if "trial_plan" not in participant.vars:
        participant.vars["trial_plan"] = build_trial_plan(moral_symbol, win_symbol)


def ensure_round_state(player):
    ensure_participant_setup(player)
    if player.field_maybe_none("grid_pattern") is None:
        plan = get_current_plan(player)
        player.actual_scenario = plan["scenario"]
        player.difficulty = plan["difficulty"]
        player.majority_symbol = plan["majority_symbol"]
        player.minority_symbol = "O" if player.majority_symbol == "X" else "X"
        player.majority_count = plan["majority_count"]
        player.minority_count = Constants.total_cells - player.majority_count
        player.grid_pattern = plan["pattern"]


def make_grid_pattern(majority_symbol: str, majority_count: int) -> str:
    minority_symbol = "O" if majority_symbol == "X" else "X"
    minority_count = Constants.total_cells - majority_count
    cells = [majority_symbol] * majority_count + [minority_symbol] * minority_count
    random.shuffle(cells)
    return "".join(cells)


def to_rows(pattern: str):
    return [
        list(pattern[i : i + Constants.grid_cols])
        for i in range(0, len(pattern), Constants.grid_cols)
    ]


def build_trial_plan(moral_symbol: str, win_symbol: str):
    """
    Build trial plan with:
    - 4 fixed trial rounds (practice, with feedback)
    - 24 main rounds (for payment) with specified X/O counts
    """
    plan = []

    # Helper to add a single round config
    def add_round(x_count: int, o_count: int, is_trial: bool):
        if x_count + o_count != Constants.total_cells:
            raise ValueError("X and O counts must sum to total_cells")
        if x_count > o_count:
            majority_symbol = "X"
            majority_count = x_count
        elif o_count > x_count:
            majority_symbol = "O"
            majority_count = o_count
        else:
            # Tie should not happen with odd grid size, but guard anyway
            majority_symbol = random.choice(["X", "O"])
            majority_count = x_count

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
        (39, 10),  # 39 X, 10 O
        (10, 39),  # 10 X, 39 O
        (25, 24),  # 25 X, 24 O
        (24, 25),  # 24 X, 25 O
    ]
    for x_count, o_count in trial_pairs:
        add_round(x_count, o_count, is_trial=True)

    # MAIN ROUNDS (for payment) - 24 rounds with specified X/O counts
    main_pairs = []

    # Extreme cases: 49-0 and 0-49, 2 times each
    main_pairs.extend([(49, 0)] * 2)
    main_pairs.extend([(0, 49)] * 2)

    # Mid-range cases (X - O) as provided (adjusted so X+O = 49)
    # Keep only the harder levels (majority counts 29 down to 25)
    base_mid_x_o = [
        (20, 29),
        (21, 28),
        (22, 27),
        (23, 26),
        (24, 25),
    ]
    # Mirror cases (X - O) where previously O was majority (adjusted so X+O = 49)
    base_mid_o_x = [
        (29, 20),
        (28, 21),
        (27, 22),
        (26, 23),
        (25, 24),
    ]
    # Use each remaining difficulty level twice (per orientation)
    for _ in range(2):
        main_pairs.extend(base_mid_x_o)
        main_pairs.extend(base_mid_o_x)

    if len(main_pairs) != 24:
        raise ValueError("Expected 24 main-round configurations")

    # Randomize order of main rounds
    random.shuffle(main_pairs)

    for x_count, o_count in main_pairs:
        add_round(x_count, o_count, is_trial=False)

    return plan


class Subsession(BaseSubsession):
    def creating_session(self):
        for player in self.get_players():
            ensure_participant_setup(player)
            plan = get_current_plan(player)
            player.actual_scenario = plan["scenario"]
            player.difficulty = plan["difficulty"]
            player.majority_symbol = plan["majority_symbol"]
            player.minority_symbol = "O" if player.majority_symbol == "X" else "X"
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
        choices=[("X", "X"), ("O", "O")], widget=widgets.RadioSelect
    )
    view_again_count = models.IntegerField(initial=0)
    # Reaction time (in seconds) for reporting the scenario symbol on the Interpretation page
    reported_symbol_rt = models.FloatField()

    action_choice = models.StringField(
        choices=[("A", "Action A"), ("B", "Action B")], widget=widgets.RadioSelect
    )
    # Reaction time (in seconds) for choosing an action on the AllocationDecision page
    action_choice_rt = models.FloatField()

    # Accuracy rate in the 20 non-extreme main rounds
    # (computed and stored on the final round only; not shown to participants)
    mid_main_accuracy = models.FloatField()

    identification_correct = models.BooleanField(initial=False)
    identification_bonus_awarded = models.CurrencyField(initial=cu(0))
    net_identification_bonus = models.CurrencyField(initial=cu(0))
    view_again_cost_applied = models.CurrencyField(initial=cu(0))
    charity_payoff = models.CurrencyField(initial=cu(0))
    consent = models.StringField(
        choices=[("yes", "I consent to participate"), ("no", "I do not consent")],
        widget=widgets.RadioSelect,
    )
    # Comprehension test answers (multiple choice)
    comp1_q1 = models.StringField(
        choices=[
            ("true_scenario", "The true active scenario (Scenario X or O)"),
            ("reported_scenario", "The scenario I reported"),
        ],
        widget=widgets.RadioSelect,
    )
    comp1_q2 = models.StringField(
        choices=[
            ("scenario_x", "Scenario X"),
            ("scenario_o", "Scenario O"),
        ],
        widget=widgets.RadioSelect,
    )
    comp1_q3 = models.StringField(
        choices=[
            ("scenario_o", "Scenario O"),
            ("scenario_x", "Scenario X"),
        ],
        widget=widgets.RadioSelect,
    )
    comp1_q4 = models.StringField(
        choices=[
            ("true_scenario", "The true active scenario determined by the grid"),
            ("reported_scenario", "The scenario I reported"),
        ],
        widget=widgets.RadioSelect,
    )

    comp2_q1 = models.StringField(
        choices=[
            ("true_scenario", "The true active scenario (Scenario X or O)"),
            ("reported_scenario", "The scenario I reported"),
        ],
        widget=widgets.RadioSelect,
    )
    comp2_q2 = models.StringField(
        choices=[
            ("scenario_x", "Scenario X"),
            ("scenario_o", "Scenario O"),
        ],
        widget=widgets.RadioSelect,
    )
    comp2_q3 = models.StringField(
        choices=[
            ("scenario_o", "Scenario O"),
            ("scenario_x", "Scenario X"),
        ],
        widget=widgets.RadioSelect,
    )
    comp2_q4 = models.StringField(
        choices=[
            ("true_scenario", "The true active scenario determined by the grid"),
            ("reported_scenario", "The scenario I reported"),
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

        # view-again cost (per request)
        cost_per_view = get_view_again_cost(self)
        total_cost = cost_per_view * self.view_again_count
        self.view_again_cost_applied = total_cost
        self.net_identification_bonus = (
            self.identification_bonus_awarded - self.view_again_cost_applied
        )

        # final payoff
        self.payoff = base_payoff + self.net_identification_bonus


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
        payoffs_x = payoffs["moral_conflict"] if moral_symbol == "X" else payoffs["win_win"]
        payoffs_o = payoffs["win_win"] if moral_symbol == "X" else payoffs["moral_conflict"]
        return dict(
            num_rounds=Constants.num_rounds,
            grid_size=f"{Constants.grid_rows} × {Constants.grid_cols}",
            display_seconds=2,
            identification_bonus=Constants.identification_bonus,
            scenario_label_moral=scenario_label(moral_symbol),
            scenario_label_win=scenario_label(win_symbol),
            view_again_cost=player.participant.vars.get(
                "view_again_cost", Constants.view_again_cost
            ),
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
        payoffs_x = payoffs["moral_conflict"] if moral_symbol == "X" else payoffs["win_win"]
        payoffs_o = payoffs["win_win"] if moral_symbol == "X" else payoffs["moral_conflict"]
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
        if not consent_ok or comp_failed:
            return False
        # Always allow the 4 practice rounds
        if player.round_number <= 4:
            return True
        # For main rounds, only proceed if comprehension was passed
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
    form_fields = ["reported_symbol", "view_again_count", "reported_symbol_rt"]

    @staticmethod
    def vars_for_template(player: Player):
        ensure_round_state(player)
        moral_symbol = player.participant.vars["moral_symbol"]
        win_symbol = player.participant.vars["win_symbol"]
        payoffs = Constants.payoffs
        # Always show Scenario X left, Scenario O right
        payoffs_x = payoffs["moral_conflict"] if moral_symbol == "X" else payoffs["win_win"]
        payoffs_o = payoffs["win_win"] if moral_symbol == "X" else payoffs["moral_conflict"]
        return dict(
            grid_rows=player.grid_rows(),
            grid_cols=Constants.grid_cols,
            moral_symbol=moral_symbol,
            win_symbol=win_symbol,
            scenario_label_moral=scenario_label(moral_symbol),
            scenario_label_win=scenario_label(win_symbol),
            scenario_label_x=scenario_label("X"),
            scenario_label_o=scenario_label("O"),
            payoffs=payoffs,
            payoffs_x=payoffs_x,
            payoffs_o=payoffs_o,
            view_again_cost=player.participant.vars.get(
                "view_again_cost", Constants.view_again_cost
            ),
        )

    @staticmethod
    def error_message(player: Player, values):
        if values["reported_symbol"] not in {"X", "O"}:
            return "Please select which symbol you believe appeared more often."

    @staticmethod
    def is_displayed(player: Player):
        consent_ok = player.participant.vars.get("consent") == "yes"
        comp_passed = player.participant.vars.get("comp_passed", False)
        comp_failed = player.participant.vars.get("comp_failed", False)
        if not consent_ok or comp_failed:
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
        if not consent_ok or comp_failed:
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
        # Always show Scenario X left, Scenario O right
        payoffs_x = payoffs["moral_conflict"] if moral_symbol == "X" else payoffs["win_win"]
        payoffs_o = payoffs["win_win"] if moral_symbol == "X" else payoffs["moral_conflict"]
        
        reported_symbol = player.reported_symbol
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
            chosen_payoffs=payoffs_x if chosen_scenario_symbol == "X" else payoffs_o,
            other_payoffs=payoffs_o if chosen_scenario_symbol == "X" else payoffs_x,
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
        payoffs_x = payoffs["moral_conflict"] if moral_symbol == "X" else payoffs["win_win"]
        payoffs_o = payoffs["win_win"] if moral_symbol == "X" else payoffs["moral_conflict"]
        # reported_symbol can be None in edge cases; guard against that
        reported_symbol = player.field_maybe_none("reported_symbol") or ""
        # action_choice can be None in some edge cases (e.g. debugging); guard against that
        action_choice = player.field_maybe_none("action_choice")
        if action_choice and player.field_maybe_none("actual_scenario"):
            base_payoff = payoffs[player.actual_scenario][action_choice]["player"]
        else:
            base_payoff = cu(0)
        
        x_was_chosen = (reported_symbol == "X")
        o_was_chosen = (reported_symbol == "O")
        x_was_correct = x_was_chosen and (player.majority_symbol == "X")
        o_was_correct = o_was_chosen and (player.majority_symbol == "O")
        
        return dict(
            identification_correct=player.identification_correct,
            identification_bonus=player.identification_bonus_awarded,
            net_identification_bonus=player.net_identification_bonus,
            view_again_cost=player.view_again_cost_applied,
            view_again_count=player.view_again_count,
            view_again_label="view" if player.view_again_count == 1 else "views",
            view_again_unit_cost=get_view_again_cost(player),
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
            scenario_label_x=scenario_label("X"),
            scenario_label_o=scenario_label("O"),
            payoffs_x=payoffs_x,
            payoffs_o=payoffs_o,
            x_was_chosen=x_was_chosen,
            o_was_chosen=o_was_chosen,
            x_was_correct=x_was_correct,
            o_was_correct=o_was_correct,
            reported_symbol=reported_symbol,
        )


class FinalPage(Page):
    @staticmethod
    def is_displayed(player: Player):
        return player.round_number == Constants.num_rounds and player.participant.vars.get(
            "consent"
        ) == "yes"

    @staticmethod
    def vars_for_template(player: Player):
        pvars = player.participant.vars
        comp_failed = pvars.get("comp_failed", False)

        # If comprehension failed, no main-task earnings; show excluded screen
        if comp_failed:
            return dict(
                excluded=True,
                payment_round=None,
                payment_player_payoff=None,
                payment_charity_payoff=None,
            )

        # Compute accuracy in the 20 non-extreme main rounds (majority_count < 49)
        # and store it for export (on the final-round player and in participant.vars).
        main_round_players = player.in_rounds(5, Constants.num_rounds)
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
            main_round_numbers = list(range(5, Constants.num_rounds + 1))
            paying_round_number = random.choice(main_round_numbers)
            pvars["paying_round_number"] = paying_round_number
        # Get this player's record in the chosen paying round
        payment_player = player.in_round(paying_round_number)

        return dict(
            excluded=False,
            payment_round=paying_round_number,
            payment_player_payoff=payment_player.payoff,
            payment_charity_payoff=payment_player.charity_payoff,
        )


class ComprehensionTest1(Page):
    form_model = "player"
    form_fields = ["comp1_q1", "comp1_q2", "comp1_q3", "comp1_q4"]

    @staticmethod
    def is_displayed(player: Player):
        return (
            player.participant.vars.get("consent") == "yes"
            and player.round_number == 4
            and not player.participant.vars.get("comp_passed", False)
            and not player.participant.vars.get("comp_failed", False)
        )

    @staticmethod
    def vars_for_template(player: Player):
        ensure_round_state(player)
        moral_symbol = player.participant.vars["moral_symbol"]
        win_symbol = player.participant.vars["win_symbol"]
        payoffs = Constants.payoffs
        payoffs_x = payoffs["moral_conflict"] if moral_symbol == "X" else payoffs["win_win"]
        payoffs_o = payoffs["win_win"] if moral_symbol == "X" else payoffs["moral_conflict"]
        return dict(
            payoffs_x=payoffs_x,
            payoffs_o=payoffs_o,
        )

    @staticmethod
    def before_next_page(player: Player, timeout_happened):
        pvars = player.participant.vars
        correct_answers = {
            "comp1_q1": "true_scenario",
            "comp1_q2": "scenario_x",
            "comp1_q3": "scenario_o",
            "comp1_q4": "true_scenario",
        }
        all_correct = all(
            getattr(player, field) == expected
            for field, expected in correct_answers.items()
        )
        if all_correct:
            pvars["comp_passed"] = True
        else:
            pvars["needs_second_test"] = True


class ComprehensionTest2(Page):
    form_model = "player"
    form_fields = ["comp2_q1", "comp2_q2", "comp2_q3", "comp2_q4"]

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
        payoffs_x = payoffs["moral_conflict"] if moral_symbol == "X" else payoffs["win_win"]
        payoffs_o = payoffs["win_win"] if moral_symbol == "X" else payoffs["moral_conflict"]
        return dict(
            payoffs_x=payoffs_x,
            payoffs_o=payoffs_o,
        )

    @staticmethod
    def before_next_page(player: Player, timeout_happened):
        pvars = player.participant.vars
        correct_answers = {
            "comp2_q1": "true_scenario",
            "comp2_q2": "scenario_o",
            "comp2_q3": "scenario_x",
            "comp2_q4": "true_scenario",
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
    ComprehensionPassNotice,
    FinalPage,
]

