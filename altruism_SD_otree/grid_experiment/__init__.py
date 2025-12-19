from otree.api import *
import random


doc = """
Altruism & self-deception experiment with X/O grid stimuli.
"""


class Constants(BaseConstants):
    name_in_url = "grid_experiment"
    players_per_group = None
    num_rounds = 48
    grid_rows = 7
    grid_cols = 7
    total_cells = grid_rows * grid_cols
    difficulty_levels = {
        "hard": 30,   # majority count (difference of 19: 30 vs 19)
        "medium": 35, # majority count (difference of 14: 35 vs 14)
        "easy": 40,   # majority count (difference of 9: 40 vs 9)
    }
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
    # half of the rounds per scenario by default
    num_moral = Constants.num_rounds // 2
    num_win = Constants.num_rounds - num_moral
    scenarios = ["moral_conflict"] * num_moral + ["win_win"] * num_win
    random.shuffle(scenarios)

    difficulty_names = list(Constants.difficulty_levels.keys())
    difficulty_pool = (
        difficulty_names * (Constants.num_rounds // len(difficulty_names) + 1)
    )[: Constants.num_rounds]
    random.shuffle(difficulty_pool)

    trials = []
    for scenario, difficulty in zip(scenarios, difficulty_pool):
        majority_symbol = moral_symbol if scenario == "moral_conflict" else win_symbol
        majority_count = Constants.difficulty_levels[difficulty]
        pattern = make_grid_pattern(majority_symbol, majority_count)
        trials.append(
            dict(
                scenario=scenario,
                difficulty=difficulty,
                majority_symbol=majority_symbol,
                majority_count=majority_count,
                pattern=pattern,
            )
        )
    return trials


class Subsession(BaseSubsession):
    def creating_session(self):
        if self.round_number == 1:
            for player in self.get_players():
                moral_symbol, win_symbol = random.choice([("X", "O"), ("O", "X")])
                player.participant.vars["moral_symbol"] = moral_symbol
                player.participant.vars["win_symbol"] = win_symbol
                player.participant.vars["view_again_cost"] = self.session.config.get(
                    "view_again_cost", Constants.view_again_cost
                )
                # NOTE: Trial plan is generated once and cached in participant vars.
                # If you change Constants.difficulty_levels, you must create a NEW session
                # for the changes to take effect (existing sessions use the cached plan).
                player.participant.vars["trial_plan"] = build_trial_plan(
                    moral_symbol, win_symbol
                )

        for player in self.get_players():
            plan = player.participant.vars["trial_plan"][self.round_number - 1]
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
    view_again_cost_applied = models.CurrencyField(initial=cu(0))
    charity_payoff = models.CurrencyField(initial=cu(0))

    def grid_rows(self):
        return to_rows(self.grid_pattern)

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
        cost_per_view = self.session.config.get(
            "view_again_cost", Constants.view_again_cost
        )
        total_cost = cost_per_view * self.view_again_count
        self.view_again_cost_applied = total_cost

        # final payoff
        self.payoff = base_payoff + self.identification_bonus_awarded - total_cost


class Introduction(Page):
    @staticmethod
    def is_displayed(player: Player):
        return player.round_number == 1

    @staticmethod
    def vars_for_template(player: Player):
        return dict(
            num_rounds=Constants.num_rounds,
            grid_size=f"{Constants.grid_rows} × {Constants.grid_cols}",
            display_seconds=2,
            identification_bonus=Constants.identification_bonus,
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
        return dict(
            moral_symbol=player.participant.vars["moral_symbol"],
            win_symbol=player.participant.vars["win_symbol"],
        )


class Stimulus(Page):
    timeout_seconds = 10
    timer_text = "Stimulus on screen"

    @staticmethod
    def vars_for_template(player: Player):
        return dict(
            grid_rows=player.grid_rows(),
            grid_cols=Constants.grid_cols,
            majority_symbol=player.majority_symbol,
            majority_count=player.majority_count,
            minority_symbol=player.minority_symbol,
            minority_count=player.minority_count,
        )


class Interpretation(Page):
    form_model = "player"
    form_fields = ["reported_symbol", "view_again_count", "reaction_time"]

    @staticmethod
    def vars_for_template(player: Player):
        return dict(
            grid_rows=player.grid_rows(),
            grid_cols=Constants.grid_cols,
            moral_symbol=player.participant.vars["moral_symbol"],
            win_symbol=player.participant.vars["win_symbol"],
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
        payoffs = Constants.payoffs
        return dict(
            moral_symbol=player.participant.vars["moral_symbol"],
            win_symbol=player.participant.vars["win_symbol"],
            scenario=player.actual_scenario,
            payoffs=payoffs,
        )

    @staticmethod
    def before_next_page(player: Player, timeout_happened):
        player.set_outcomes()


class RoundSummary(Page):
    @staticmethod
    def vars_for_template(player: Player):
        return dict(
            identification_correct=player.identification_correct,
            identification_bonus=player.identification_bonus_awarded,
            view_again_cost=player.view_again_cost_applied,
            action_choice=player.action_choice,
            actual_scenario=player.actual_scenario,
            charity_payoff=player.charity_payoff,
            total_rounds=Constants.num_rounds,
        )


page_sequence = [
    Introduction,
    MappingInfo,
    Stimulus,
    Interpretation,
    AllocationDecision,
    RoundSummary,
]

