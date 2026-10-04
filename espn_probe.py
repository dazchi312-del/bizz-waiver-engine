import os

from bizz import (
    build_waiver_evaluations,
    find_projected_upgrades,
    rank_waiver_evaluations,
    filter_available_candidates,
)

from dotenv import load_dotenv
from espn_api.football import League
from espn_provider import convert_espn_players, find_espn_team

def load_espn_league():
    """Load private configuration and return an authenticated ESPN league."""

    load_dotenv()

    return League(
        league_id=int(os.environ["ESPN_LEAGUE_ID"]),
        year=int(os.environ["ESPN_YEAR"]),
        espn_s2=os.environ["ESPN_S2"],
        swid=os.environ["SWID"],
    )


def main():
    """Confirm that the application can read our ESPN league."""
    league = load_espn_league()
    team_id = int(os.environ["ESPN_TEAM_ID"])

    espn_team = find_espn_team(league.teams, team_id)

    if espn_team is None:
        raise ValueError(f"ESPN team {team_id} was not found")
    # Inspect roster-slot data before defining our internal representation.
    for espn_player in espn_team.roster:
        print(
            espn_player.name,
            repr(getattr(espn_player, "lineupSlot", None)),
        )
    #Translate ESPN roster data into our internal Player model

    roster = convert_espn_players(espn_team.roster)

    print(f"\n{espn_team.team_name} roster:")
    for player in roster:
        print(player)

    # Translate available ESPN players through the same adapter.
    espn_free_agents = league.free_agents(size=50)
    free_agents = convert_espn_players(espn_free_agents)

    print("\nConverted Bizz free agents:")
    for player in free_agents:
        print(player)

    # Compare each free agent against lowest projected
    # Roster player at same position
    evaluations = build_waiver_evaluations(roster, free_agents)

    # Keep only positive projected point changes.
    upgrades = find_projected_upgrades(evaluations)

    # Apply availability policy before presenting recommendations.
    available_upgrades = filter_available_candidates(upgrades)

    # Present the strongest eligible upgrade first.
    ranked_upgrades = rank_waiver_evaluations(available_upgrades)

    print("\nAvailable projected upgrades:")

    for evaluation in ranked_upgrades:
        print (
            f"ADD {evaluation.free_agent.name}, "
            f"DROP {evaluation.drop_candidate.name}: "
            f"{evaluation.projected_gain:+.2f} projected points"
        )


if __name__ == "__main__":
    main()