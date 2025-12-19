from otree.api import *
import random


doc = """
Altruism & self-deception experiment with X/O grid stimuli.
"""


class Constants(BaseConstants):
    name_in_url = "grid_experiment"
    players_per_group = None
    num_rounds = 30
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
    Build trial plan with 30 rounds:
    - 15 difficulty levels (majority counts from 25 to 39)
    - Each difficulty level appears twice: once with O as majority, once with X as majority
    - Scenario is determined by which symbol maps to which scenario (moral_symbol -> moral_conflict, win_symbol -> win_win)
    - Trials are shuffled randomly
    """
    trials = []
    
    # Create 30 trials: 15 difficulty levels × 2 symbols (O and X)
    for majority_count in Constants.difficulty_levels:
        # Trial with O as majority
        trials.append({
            "majority_count": majority_count,
            "majority_symbol": "O",
        })
        # Trial with X as majority
        trials.append({
            "majority_count": majority_count,
            "majority_symbol": "X",
        })
    
    # Assign scenarios based on symbol-to-scenario mapping
    final_trials = []
    for trial in trials:
        # Determine scenario: if majority_symbol matches moral_symbol, it's moral_conflict
        # If it matches win_symbol, it's win_win
        if trial["majority_symbol"] == moral_symbol:
            scenario = "moral_conflict"
        elif trial["majority_symbol"] == win_symbol:
            scenario = "win_win"
        else:
            # This shouldn't happen, but handle edge case
            scenario = random.choice(["moral_conflict", "win_win"])
        
        pattern = make_grid_pattern(trial["majority_symbol"], trial["majority_count"])
        final_trials.append(
            dict(
                scenario=scenario,
                difficulty=str(trial["majority_count"]),  # Store as string for compatibility
                majority_symbol=trial["majority_symbol"],
                majority_count=trial["majority_count"],
                pattern=pattern,
            )
        )
    
    # Shuffle the final trials to randomize order
    random.shuffle(final_trials)
    
    return final_trials


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
    reaction_time = models.FloatField()

    action_choice = models.StringField(
        choices=[("A", "Action A"), ("B", "Action B")], widget=widgets.RadioSelect
    )

    identification_correct = models.BooleanField(initial=False)
    identification_bonus_awarded = models.CurrencyField(initial=cu(0))
    net_identification_bonus = models.CurrencyField(initial=cu(0))
    view_again_cost_applied = models.CurrencyField(initial=cu(0))
    charity_payoff = models.CurrencyField(initial=cu(0))

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


class Introduction(Page):
    @staticmethod
    def is_displayed(player: Player):
        return player.round_number == 1

    @staticmethod
    def vars_for_template(player: Player):
        ensure_round_state(player)
        return dict(
            num_rounds=Constants.num_rounds,
            grid_size=f"{Constants.grid_rows} × {Constants.grid_cols}",
            display_seconds=2,
            identification_bonus=Constants.identification_bonus,
            scenario_label_moral=scenario_label(player.participant.vars["moral_symbol"]),
            scenario_label_win=scenario_label(player.participant.vars["win_symbol"]),
            view_again_cost=player.participant.vars.get(
                "view_again_cost", Constants.view_again_cost
            ),
        )


class MappingInfo(Page):
    @staticmethod
    def is_displayed(player: Player):
        return player.round_number == 1

    @staticmethod
    def vars_for_template(player: Player):
        ensure_round_state(player)
        return dict(
            moral_symbol=player.participant.vars["moral_symbol"],
            win_symbol=player.participant.vars["win_symbol"],
            scenario_label_moral=scenario_label(player.participant.vars["moral_symbol"]),
            scenario_label_win=scenario_label(player.participant.vars["win_symbol"]),
            payoffs=Constants.payoffs,
        )


class Stimulus(Page):
    timeout_seconds = 2
    timer_text = "Stimulus on screen"

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
    form_fields = ["reported_symbol", "view_again_count", "reaction_time"]

    @staticmethod
    def vars_for_template(player: Player):
        ensure_round_state(player)
        moral_symbol = player.participant.vars["moral_symbol"]
        win_symbol = player.participant.vars["win_symbol"]
        # Get scenario labels for X and O
        scenario_label_x = scenario_label("X")
        scenario_label_o = scenario_label("O")
        
        return dict(
            grid_rows=player.grid_rows(),
            grid_cols=Constants.grid_cols,
            moral_symbol=moral_symbol,
            win_symbol=win_symbol,
            scenario_label_moral=scenario_label(moral_symbol),
            scenario_label_win=scenario_label(win_symbol),
            scenario_label_x=scenario_label_x,
            scenario_label_o=scenario_label_o,
            view_again_cost=player.participant.vars.get(
                "view_again_cost", Constants.view_again_cost
            ),
        )

    @staticmethod
    def error_message(player: Player, values):
        if values["reported_symbol"] not in {"X", "O"}:
            return "Please select which symbol you believe appeared more often."


class AllocationDecision(Page):
    form_model = "player"
    form_fields = ["action_choice"]

    @staticmethod
    def vars_for_template(player: Player):
        ensure_round_state(player)
        payoffs = Constants.payoffs
        moral_symbol = player.participant.vars["moral_symbol"]
        win_symbol = player.participant.vars["win_symbol"]
        
        # Determine which scenario corresponds to the reported symbol
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
            # Fallback (shouldn't happen)
            chosen_scenario = "win_win"
            chosen_scenario_label = scenario_label(win_symbol)
            chosen_scenario_symbol = win_symbol
        
        # Get payoffs for the chosen scenario
        chosen_payoffs = {
            "A": payoffs[chosen_scenario]["A"],
            "B": payoffs[chosen_scenario]["B"],
        }
        
        return dict(
            moral_symbol=moral_symbol,
            win_symbol=win_symbol,
            scenario_label_moral=scenario_label(moral_symbol),
            scenario_label_win=scenario_label(win_symbol),
            scenario=player.actual_scenario,
            payoffs=payoffs,
            chosen_scenario=chosen_scenario,
            chosen_scenario_label=chosen_scenario_label,
            chosen_scenario_symbol=chosen_scenario_symbol,
            chosen_payoffs=chosen_payoffs,
        )

    @staticmethod
    def before_next_page(player: Player, timeout_happened):
        player.set_outcomes()


class RoundSummary(Page):
    @staticmethod
    def vars_for_template(player: Player):
        moral_symbol = player.participant.vars["moral_symbol"]
        win_symbol = player.participant.vars["win_symbol"]
        reported_symbol = player.reported_symbol
        
        # Get scenario labels for X and O
        x_scenario_label = scenario_label("X")
        o_scenario_label = scenario_label("O")
        
        # Determine if the reported symbol was correct
        # Show result only for the symbol they chose
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
            action_choice=player.action_choice,
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
            moral_symbol=moral_symbol,
            win_symbol=win_symbol,
            scenario_label_x=x_scenario_label,
            scenario_label_o=o_scenario_label,
            x_was_chosen=x_was_chosen,
            o_was_chosen=o_was_chosen,
            x_was_correct=x_was_correct,
            o_was_correct=o_was_correct,
            reported_symbol=reported_symbol,
        )


page_sequence = [
    Introduction,
    MappingInfo,
    Stimulus,
    Interpretation,
    AllocationDecision,
    RoundSummary,
]

