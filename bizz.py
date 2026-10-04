"""
The Bizz Weekly Edge Engine.

Analyzes league, roster, projection, and opportunity data to produce
an explainable weekly waiver-claim plan.
"""
class Player:
    """Represents one NFL player and the weekly data used by the analyzer."""
    def __init__(self, name, team, position, projected_points, status, roster_slot=None):
        self.name = name
        self.team = team
        self.position = position
        self.projected_points = projected_points
        self.status = status
        self.roster_slot = roster_slot

    def __str__(self):
        return f"{self.name} ({self.team}, {self.position}) - {self.projected_points} projected points [{self.status}]"

class WaiverEvaluation:
    """Represents one possible free-agent add/drop comparison."""
    def __init__(self, free_agent, drop_candidate):
        self.free_agent = free_agent
        self.drop_candidate = drop_candidate
        self.projected_gain = (
            free_agent.projected_points
            - drop_candidate.projected_points
        )

    def is_upgrade(self):
        """Return True when the free agent improves the position."""
        return self.projected_gain > 0

    def __str__(self):
        """Return the evaluation as one actionable recommendation"""
        return (
            f"ADD {self.free_agent.name}, "
            f"DROP {self.drop_candidate.name}, "
            f"+ {self.projected_gain:.1f} projected points"
        )
       

def main():
    #Mission Control: load data, request evaluations, and present results.
    roster = load_sample_roster()
    free_agents = load_sample_free_agents()

    #Build valid Add/Drop comparisons from the available players
    evaluations = build_waiver_evaluations(roster, free_agents)
    #Keep only free agents that improve the roster
    upgrades = find_projected_upgrades(evaluations)
    #Put strongest projected upgrades first
    ranked_upgrades = rank_waiver_evaluations(upgrades)
    #Present evaluation to user
    if not ranked_upgrades:
        print("No projected waiver upgrades found")
        return

    # Recommendations
    for evaluation in ranked_upgrades:
        print(evaluation)

def load_sample_roster():
    """Return temporary roster data for development and testing."""
    roster = []
    roster.append(Player("Drake Maye", "NE", "QB", 19.9, "ACTIVE"))
    roster.append(Player("Omarion Hampton", "LAC", "RB", 16.6, "ACTIVE"))
    return roster

def load_sample_free_agents():
    """Return temporary waiver data for development and testing."""
    free_agents = []
    free_agents.append(
        Player("Test waiver RB", "Test", "RB", 17.4, "ACTIVE"))
    free_agents.append(
        Player("Test waiver RB low", "Test", "RB", 15.0, "ACTIVE"))
    # This TE fixture excercises the no-compairison guard in main()
    free_agents.append(
        Player("Test waiver TE", "Test", "TE", 10, "Active")
    )
    return free_agents

def find_lowest_projected_player(roster, position):
    """Return the lowest-projected player at a position, or None."""

    # Build a comparison pool containing only the requested position.
    same_position = []
    for player in roster:
        if player.position == position:
            same_position.append(player)
    if not same_position:
        return None
    # Use the first match as the baseline, then scan the remaining players.
    lowest_player = same_position[0]
    for player in same_position[1:]:
        if player.projected_points < lowest_player.projected_points:
            lowest_player = player
    return lowest_player

def evaluate_free_agent(roster, free_agent):
    """ Return an evaluation or None when no eligible position match exicists """
    droppable_players = []

    for player in roster:
        if is_droppable_player(player):
            droppable_players.append(player)

    drop_candidate = find_lowest_projected_player(
        droppable_players, free_agent.position
    )

    if drop_candidate is None:
        return None
    return WaiverEvaluation(free_agent, drop_candidate)

def build_waiver_evaluations(roster, free_agents):
    """Return valid evaluation of all comparable free agents"""

    evaluations = []

    for free_agent in free_agents:
        evaluation = evaluate_free_agent(roster, free_agent)

        # An unmatched position cannot produce ADD/DROP comparison
        if evaluation is None:
            continue
        evaluations.append(evaluation)
    return(evaluations)

def get_projected_gain(evaluation):
    """Return the projected gain used to rank an evaluation"""
    return evaluation.projected_gain

def rank_waiver_evaluations(evaluations):
    """Return a new list from highest projected gain to lowest"""
    return sorted(
        evaluations,
        key=get_projected_gain,
        reverse=True
    )

def find_projected_upgrades(evaluations):
    """Return only evaluations that improve the roster"""
    upgrades = []

    for evaluation in evaluations:
        if evaluation.is_upgrade():
            upgrades.append(evaluation)
    return upgrades

def is_available_candidate(player):
    """Return if player is elgible for recommendation"""
    unavailable_statuses = {"OUT", "INJURY_RESERVE"}

    return player.status not in unavailable_statuses

def filter_available_candidates(evaluations):
    """Keep evaluations whos free agents  meet our availability policy"""
    available_evaluations = []

    for evaluation in evaluations:
        if is_available_candidate(evaluation.free_agent):
            available_evaluations.append(evaluation)

    return available_evaluations

def is_droppable_player(player):
    """Return whether our policy allows considering this player for a drop"""
    return player.roster_slot is not None and player.roster_slot != "IR"

if __name__ == "__main__":
    main()
