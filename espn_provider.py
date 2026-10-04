from bizz import Player

def get_espn_projection(espn_player):
    """Return the most consistently available ESPN projection."""
    projected_average = getattr(
        espn_player,
        "projected_avg_points",
        None,
    )

    if projected_average is not None:
        return projected_average

    weekly_projection = getattr(
        espn_player,
        "projected_points",
        None,
    )

    if weekly_projection is not None:
        return weekly_projection

    return 0.0


def get_espn_status(espn_player):
    """Normalize espn injury status into a nonempty string"""
    status = getattr(espn_player, "injuryStatus", None)
    if not status:
        return "NORMAL"
    return status


def convert_espn_player(espn_player):
    """Translate one ESPN player into an internal Player object."""
    return Player(
        name=espn_player.name,
        team=espn_player.proTeam,
        position=espn_player.position,
        projected_points=get_espn_projection(espn_player),
        status=get_espn_status(espn_player),
        roster_slot=getattr(espn_player, "lineupSlot", None),
    )

def convert_espn_players(espn_players):
    """Translate a collection of ESPN players into internal Player objects."""
    players = []

    for espn_player in espn_players:
        player = convert_espn_player(espn_player)
        players.append(player)

    return players




def find_espn_team(espn_teams, team_id):
    """Return ESPN team matching team_id, or none if not found"""
    for team in espn_teams:
        if team.team_id == team_id:
            return team
    return None


