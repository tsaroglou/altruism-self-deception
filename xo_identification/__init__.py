from otree.api import *
import random


doc = """
Pure X/O identification task with 20 main trials (no scenarios or payoffs).
"""


class Constants(BaseConstants):
    name_in_url = "xo_identification"
    players_per_group = None
    num_rounds = 20
    grid_rows = 7
    grid_cols = 7
    total_cells = grid_rows * grid_cols


def make_grid_pattern(majority_symbol: str, majority_count: int) -> str:
    """Create a shuffled pattern string with a given majority symbol/count."""
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


def build_plan():
    """
    Build plan for 20 identification-only rounds:
    - Use the same 10 mid-difficulty X/O pairs as the main task in grid_experiment
      (majority counts 29, 28, 27, 26, 25), plus their mirrors.
    - Each of these 10 configurations appears twice, for 20 total rounds.
    """
    plan = []

    def add_round(x_count: int, o_count: int):
        if x_count + o_count != Constants.total_cells:
            raise ValueError("X and O counts must sum to total_cells")
        if x_count > o_count:
            majority_symbol = "X"
            majority_count = x_count
        elif o_count > x_count:
            majority_symbol = "O"
            majority_count = o_count
        else:
            majority_symbol = random.choice(["X", "O"])
            majority_count = x_count

        pattern = make_grid_pattern(majority_symbol, majority_count)
        plan.append(
            dict(
                majority_symbol=majority_symbol,
                majority_count=majority_count,
                pattern=pattern,
            )
        )

    # Base mid-difficulty X-minority / O-majority pairs
    base_mid_x_o = [
        (20, 29),
        (21, 28),
        (22, 27),
        (23, 26),
        (24, 25),
    ]
    # Mirrors (X-majority / O-minority)
    base_mid_o_x = [
        (29, 20),
        (28, 21),
        (27, 22),
        (26, 23),
        (25, 24),
    ]

    # 10 distinct configurations, each used twice = 20 rounds total
    for _ in range(2):
        for x_count, o_count in base_mid_x_o + base_mid_o_x:
            add_round(x_count, o_count)

    if len(plan) != 20:
        raise ValueError("Expected 20 identification-only configurations")

    random.shuffle(plan)
    return plan


def ensure_round_state(player: "Player"):
    """
    Ensure that the current round's grid pattern and majority info are set
    for this player. This is defensive in case creating_session did not
    populate these fields (e.g., older sessions or migrations).
    """
    participant = player.participant
    if "xo_plan" not in participant.vars:
        participant.vars["xo_plan"] = build_plan()
    plan_list = participant.vars["xo_plan"]
    index = player.round_number - 1
    if 0 <= index < len(plan_list):
        plan = plan_list[index]
        if player.field_maybe_none("majority_symbol") is None:
            player.majority_symbol = plan["majority_symbol"]
        if player.field_maybe_none("majority_count") is None:
            player.majority_count = plan["majority_count"]
        if player.field_maybe_none("grid_pattern") is None:
            player.grid_pattern = plan["pattern"]


class Subsession(BaseSubsession):
    def creating_session(self):
        # Build a single 20-round plan for each participant and store it in participant.vars
        for player in self.get_players():
            participant = player.participant
            if "xo_plan" not in participant.vars:
                participant.vars["xo_plan"] = build_plan()
            plan = participant.vars["xo_plan"][player.round_number - 1]
            player.majority_symbol = plan["majority_symbol"]
            player.majority_count = plan["majority_count"]
            player.grid_pattern = plan["pattern"]


class Group(BaseGroup):
    pass


class Player(BasePlayer):
    majority_symbol = models.StringField()
    majority_count = models.IntegerField()
    grid_pattern = models.LongStringField()

    reported_symbol = models.StringField(
        choices=[("X", "X"), ("O", "O")], widget=widgets.RadioSelect
    )
    view_again_count = models.IntegerField(initial=0)
    reported_symbol_rt = models.FloatField()
    identification_correct = models.BooleanField(initial=False)
    # Overall accuracy across all 20 identification trials (set on final round only)
    overall_accuracy = models.FloatField()

    def grid_rows(self):
        pattern = self.field_maybe_none("grid_pattern")
        if pattern is None:
            return []
        return to_rows(pattern)

    def set_identification_outcome(self):
        # Be defensive in case majority_symbol was not pre-populated for some reason.
        majority_symbol = self.field_maybe_none("majority_symbol")
        if majority_symbol is None:
            pattern = self.field_maybe_none("grid_pattern") or ""
            count_x = pattern.count("X")
            count_o = pattern.count("O")
            if count_x > count_o:
                majority_symbol = "X"
            elif count_o > count_x:
                majority_symbol = "O"
            else:
                majority_symbol = random.choice(["X", "O"])
            self.majority_symbol = majority_symbol
        self.identification_correct = self.reported_symbol == majority_symbol


class Stimulus(Page):
    timeout_seconds = 5

    @staticmethod
    def vars_for_template(player: Player):
        ensure_round_state(player)
        return dict(
            grid_rows=player.grid_rows(),
            grid_cols=Constants.grid_cols,
        )


class Identification(Page):
    form_model = "player"
    form_fields = ["reported_symbol", "view_again_count", "reported_symbol_rt"]

    @staticmethod
    def vars_for_template(player: Player):
        ensure_round_state(player)
        return dict(
            grid_rows=player.grid_rows(),
            grid_cols=Constants.grid_cols,
        )

    @staticmethod
    def before_next_page(player: Player, timeout_happened):
        ensure_round_state(player)
        player.set_identification_outcome()
        # On the final round, compute and store overall accuracy across all trials
        if player.round_number == Constants.num_rounds:
            all_players = player.in_rounds(1, Constants.num_rounds)
            if all_players:
                correct_count = sum(1 for p in all_players if p.identification_correct)
                accuracy = correct_count / len(all_players)
            else:
                accuracy = 0.0
            player.overall_accuracy = accuracy
            player.participant.vars["xo_overall_accuracy"] = accuracy


class FinalScreen(Page):
    @staticmethod
    def is_displayed(player: Player):
        return player.round_number == Constants.num_rounds

    @staticmethod
    def vars_for_template(player: Player):
        # Prefer stored value; fall back to recomputing defensively
        accuracy = player.field_maybe_none("overall_accuracy")
        if accuracy is None:
            all_players = player.in_rounds(1, Constants.num_rounds)
            if all_players:
                correct_count = sum(1 for p in all_players if p.identification_correct)
                accuracy = correct_count / len(all_players)
            else:
                accuracy = 0.0
        return dict(
            total_rounds=Constants.num_rounds,
            overall_accuracy=accuracy,
            accuracy_percent=accuracy * 100,
        )


class Intro(Page):
    @staticmethod
    def is_displayed(player: Player):
        return player.round_number == 1

    @staticmethod
    def vars_for_template(player: Player):
        return dict(total_rounds=Constants.num_rounds)


page_sequence = [Intro, Stimulus, Identification, FinalScreen]

