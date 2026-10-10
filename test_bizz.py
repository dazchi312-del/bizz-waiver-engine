import pytest
from bizz import (
    Player,
    RoleProfile,
    RoleSignal,
    UsageWindow,
    WaiverEvaluation,
    build_waiver_evaluations,
    evaluate_free_agent,
    find_projected_upgrades,
    rank_waiver_evaluations,
    is_available_candidate,
    filter_available_candidates,
    is_droppable_player,
)
from types import SimpleNamespace
from espn_provider import (
    convert_espn_player,
    convert_espn_players,
    find_espn_team,
)
def test_positive_projected_gain():
    """A higher-projected free agent should be marked as an upgrade."""

    free_agent = Player(
        "Waiver RB", "TEST", "RB", 17.4, "ACTIVE"
    )
    drop_candidate = Player(
        "Roster RB", "TEST", "RB", 16.6, "ACTIVE"
    )

    evaluation = WaiverEvaluation(free_agent, drop_candidate)

    assert evaluation.projected_gain == pytest.approx(0.8)
    assert evaluation.is_upgrade() is True


def test_negative_projected_gain():
    """A lower-projected free agent should not be marked as an upgrade."""

    free_agent = Player("Waiver RB", "TEST", "RB", 15.0, "ACTIVE")
    drop_candidate = Player("Roster RB", "TEST", "RB", 16.6, "ACTIVE")

    evaluation = WaiverEvaluation(free_agent, drop_candidate)

    assert evaluation.projected_gain == pytest.approx(-1.6)
    assert evaluation.is_upgrade() is False


def test_no_same_position_comparison():
    """Return None when the roster has no matching position."""

    roster = [
        Player("Roster QB", "TEST", "QB", 20.0, "ACTIVE")
    ]
    free_agent = Player(
        "Waiver TE", "TEST", "TE", 10.0, "ACTIVE"
    )

    evaluation = evaluate_free_agent(roster, free_agent)

    assert evaluation is None


def test_build_waiver_evaluations():
    """Build evaluations only for comparable free agents."""

    roster = [
        Player(
            "Roster RB", "TEST", "RB", 16.0, "ACTIVE",
            roster_slot="BE",
        )
    ]

    free_agents = [
        Player("High RB", "TEST", "RB", 18.0, "ACTIVE"),
        Player("Low RB", "TEST", "RB", 14.0, "ACTIVE"),
        Player("Unmatched TE", "TEST", "TE", 10.0, "ACTIVE"),
    ]

    evaluations = build_waiver_evaluations(roster, free_agents)

    assert len(evaluations) == 2
    assert isinstance(evaluations[0], WaiverEvaluation)
    assert isinstance(evaluations[1], WaiverEvaluation)
    assert evaluations[0].free_agent.name == "High RB"
    assert evaluations[1].free_agent.name == "Low RB"


def test_rank_waiver_evaluations():
    """Rank waiver evaluations from highest gain to lowest."""

    drop_candidate = Player(
        "Roster RB", "TEST", "RB", 16.0, "ACTIVE"
    )

    evaluations = [
        WaiverEvaluation(
            Player("Small Upgrade", "TEST", "RB", 16.5, "ACTIVE"),
            drop_candidate,
        ),
        WaiverEvaluation(
            Player("Best Upgrade", "TEST", "RB", 19.0, "ACTIVE"),
            drop_candidate,
        ),
        WaiverEvaluation(
            Player("Downgrade", "TEST", "RB", 14.0, "ACTIVE"),
            drop_candidate,
        ),
    ]

    ranked = rank_waiver_evaluations(evaluations)

    assert ranked[0].free_agent.name == "Best Upgrade"
    assert ranked[1].free_agent.name == "Small Upgrade"
    assert ranked[2].free_agent.name == "Downgrade"


def test_find_projected_upgrades():
    """Keep positive upgrades and reject equal or negative gains."""

    drop_candidate = Player(
        "Roster RB", "TEST", "RB", 16.0, "ACTIVE"
    )

    evaluations = [
        WaiverEvaluation(
            Player("Upgrade", "TEST", "RB", 18.0, "ACTIVE"),
            drop_candidate,
        ),
        WaiverEvaluation(
            Player("Equal Player", "TEST", "RB", 16.0, "ACTIVE"),
            drop_candidate,
        ),
        WaiverEvaluation(
            Player("Downgrade", "TEST", "RB", 14.0, "ACTIVE"),
            drop_candidate,
        ),
    ]

    upgrades = find_projected_upgrades(evaluations)

    assert len(upgrades) == 1
    assert upgrades[0].free_agent.name == "Upgrade"
    assert upgrades[0].projected_gain == pytest.approx(2.0)


def test_convert_espn_player():
    """Translate an ESPN-shaped object into our internal Player model."""
    espn_player = SimpleNamespace(
        name="Test Waiver RB",
        proTeam="CHI",
        position="RB",
        projected_points=17.4,
        injuryStatus="ACTIVE",
    )
    player = convert_espn_player(espn_player)

    assert isinstance(player, Player)
    assert player.name == "Test Waiver RB"
    assert player.team == "CHI"
    assert player.position == "RB"
    assert player.projected_points == 17.4
    assert player.status == "ACTIVE"


def test_convert_espn_players():
    """Translate a collection of ESPN players into internal Player objects."""
    espn_players = [
        SimpleNamespace(
            name="Waiver RB",
            proTeam="CHI",
            position="RB",
            projected_points=17.4,
            injuryStatus="ACTIVE",
        ),
        SimpleNamespace(
            name="Waiver WR",
            proTeam="SEA",
            position="WR",
            projected_points=14.8,
            injuryStatus="QUESTIONABLE",
        ),
    ]

    players = convert_espn_players(espn_players)

    assert len(players) == 2
    assert all(isinstance(player, Player) for player in players)
    assert players[0].name == "Waiver RB"
    assert players[1].name == "Waiver WR"


def test_find_espn_team():
    """Find our fantasy team by its ESPN team ID."""
    teams = [
        SimpleNamespace(team_id=1, team_name="Other Team"),
        SimpleNamespace(team_id=5, team_name="The Bizz"),
    ]

    team = find_espn_team(teams, 5)

    assert team is teams[1]
    assert team.team_name == "The Bizz"
    assert find_espn_team(teams, 99) is None


def test_convert_espn_roster_player():
    """Translate an ESPN roster player that uses average projections."""
    espn_player = SimpleNamespace(
        name="Roster RB",
        proTeam="CHI",
        position="RB",
        projected_avg_points=14.2,
        injuryStatus="ACTIVE",
    )

    player = convert_espn_player(espn_player)

    assert isinstance(player, Player)
    assert player.projected_points == pytest.approx(14.2)


def test_convert_espn_player_with_empty_status():
    """Convert an empty ESPN injury status into NORMAL."""
    espn_player = SimpleNamespace(
        name="Lions D/ST",
        proTeam="DET",
        position="D/ST",
        projected_avg_points=6.36,
        injuryStatus=[],
    )

    player = convert_espn_player(espn_player)

    assert player.status == "NORMAL"

@pytest.mark.parametrize(
    "status, expected",
    [
        ("ACTIVE", True),
        ("NORMAL", True),
        ("QUESTIONABLE", True),
        ("DOUBTFUL", True),
        ("OUT", False),
        ("INJURY_RESERVE", False),
    ],
)


def test_is_available_candidate(status, expected):
    # Create a player whos status is the supplied status
    candidate = Player(
        name="Test Player",
        team="DET",
        position= "RB",
        projected_points= 12.5,
        status=status,
    )

    # Call helper function
    result = is_available_candidate(candidate)

    # Assert that the result is expected
    assert result == expected


def test_filter_available_candidates_excludes_out():
    """Exclude OUT candidates while preserving the original evaluations."""
    roster_player = Player("Roster RB", "TEST", "RB", 10.0, "ACTIVE")
    active_fa = Player("Healthy Prospect", "TEST", "RB", 15.0, "ACTIVE")
    out_fa = Player("Injured Star", "TEST", "RB", 20.0, "OUT")

    eval_active = WaiverEvaluation(active_fa, roster_player)
    eval_out = WaiverEvaluation(out_fa, roster_player)
    original_evals = [eval_active, eval_out]

    filtered_evals = filter_available_candidates(original_evals)

    assert filtered_evals == [eval_active]
    assert original_evals == [eval_active, eval_out]


def test_convert_espn_player_preserves_ir_slot():
    """Carry fantasy IR placement into the internal model."""
    espn_player = SimpleNamespace(
        name="Protected RB",
        proTeam="TEST",
        position="RB",
        projected_avg_points=0.0,
        injuryStatus="INJURY_RESERVE",
        lineupSlot="IR",
    )

    player = convert_espn_player(espn_player)

    assert player.roster_slot == "IR"
    assert player.status == "INJURY_RESERVE"

@pytest.mark.parametrize(
    "status, roster_slot, expected",
    [
        ("ACTIVE", "IR", False),
        ("INJURY_RESERVE", "BE", True),
        ("ACTIVE", None, False),
    ],
)


def test_is_droppable_player(status, roster_slot, expected):
    """Use fantasy slot placement to determine drop eligibility."""
    player = Player(
        name="Test Player",
        team="TEST",
        position="RB",
        projected_points=0.0,
        status=status,
        roster_slot=roster_slot,
    )

    assert is_droppable_player(player) == expected


def test_evaluate_free_agent_skips_ir_drop_candidate():
    """Compare against an eligible bench player even when IR projects lower."""
    protected_rb = Player(
        "Protected RB", "TEST", "RB", 0.0, "INJURY_RESERVE",
        roster_slot="IR",
    )
    bench_rb = Player(
        "Bench RB", "TEST", "RB", 3.0, "ACTIVE",
        roster_slot="BE",
    )
    free_agent = Player(
        "Waiver RB", "TEST", "RB", 9.0, "ACTIVE"
    )

    evaluation = evaluate_free_agent(
        [protected_rb, bench_rb], free_agent
    )

    assert evaluation is not None
    assert evaluation.drop_candidate is bench_rb
    assert evaluation.projected_gain == pytest.approx(6.0)


def test_evaluate_free_agent_returns_none_when_all_matching_players_are_protected():
    free_agent = Player(
        name="Rome Odunze",
        team="CHI",
        position="WR",
        projected_points=11.8,
        status="ACTIVE",
        roster_slot=None,
    )

    roster = [
        Player(
            name="WR One",
            team="TEST",
            position="WR",
            projected_points=12.5,
            status="ACTIVE",
            roster_slot="IR",
        ),
        Player(
            name="WR Two",
            team="TEST",
            position="WR",
            projected_points=10.0,
            status="ACTIVE",
            roster_slot=None,
        ),
    ]
    result = evaluate_free_agent(roster, free_agent)
    assert result is None


def test_find_projected_upgrades_excludes_zero_gain():
    free_agent = Player(
        name="Free Agent WR",
        team="TEST",
        position="WR",
        projected_points=10.0,
        status="ACTIVE",
        roster_slot=None,
    )

    drop_candidate = Player(
        name="Roster WR",
        team="TEST",
        position="WR",
        projected_points=10.0,
        status="ACTIVE",
        roster_slot="BE",
    )

    evaluation = WaiverEvaluation(
        free_agent,
        drop_candidate,
    )

    result = find_projected_upgrades([evaluation])

    assert result == []


def test_role_profile_route_delta():
    """Measure an expanding receiving role from baseline to recent usage."""
    baseline = 0.63
    recent = 0.815

    profile = RoleProfile(
        baseline_route_participation=baseline,
        recent_route_participation=recent,
    )

    assert profile.route_delta == pytest.approx(0.185)


def test_role_profile_negative_route_delta():
    """Preserve a negative delta when a receiving role declines."""
    baseline = 0.80
    recent = 0.65

    profile = RoleProfile(
        baseline_route_participation=baseline,
        recent_route_participation=recent,
    )

    assert profile.route_delta == pytest.approx(-0.15)


def test_role_profile_target_delta():
    """Evaluate expanding receiving roles using target share increase."""
    baseline = 0.18
    recent = 0.27

    profile = RoleProfile(
        baseline_target_share=baseline,
        recent_target_share=recent
    )

    assert profile.target_delta == pytest.approx(0.09)


def test_role_profile_route_delta_raises_when_route_data_missing():
    profile = RoleProfile(
        baseline_target_share=0.18,
        recent_target_share=0.27,
    )

    with pytest.raises(ValueError):
        _ = profile.route_delta


def test_usage_window_tprr():
    window = UsageWindow(
        targets=12,
        routes_run=60,
    )

    assert window.tprr == pytest.approx(0.20)


def test_usage_window_tprr_raises_when_routes_are_zero():
    window = UsageWindow(
        targets=12,
        routes_run=0,
    )

    with pytest.raises(ValueError):
        _ = window.tprr


def test_usage_window_tprr_allows_zero_targets():
    window = UsageWindow(
        targets=0,
        routes_run=40,
    )

    assert window.tprr == pytest.approx(0.0)


def test_role_profile_tprr_delta():
    baseline = UsageWindow(
        targets=8,
        routes_run=40,
    )

    recent = UsageWindow(
        targets=12,
        routes_run=40,
    )

    profile = RoleProfile(
        baseline_usage=baseline,
        recent_usage=recent,
    )

    assert profile.tprr_delta == pytest.approx(0.10)


def test_role_profile_tprr_delta_raises_when_usage_missing():
    baseline = UsageWindow(
        targets=8,
        routes_run=40,
    )

    profile = RoleProfile(
        baseline_usage=baseline,
    )

    with pytest.raises(ValueError):
        _ = profile.tprr_delta


def test_multi_signal_expansion_returns_true_when_all_deltas_positive():
    """Recognize a role expansion when all opportunity signals improve."""
    baseline = UsageWindow(
        targets=10,
        routes_run=50,
    )

    recent = UsageWindow(
        targets=15,
        routes_run=60,
    )

    profile = RoleProfile(
        baseline_route_participation=0.60,
        recent_route_participation=0.75,
        baseline_target_share=0.18,
        recent_target_share=0.25,
        baseline_usage=baseline,
        recent_usage=recent,
    )

    signal = RoleSignal(profile)

    assert signal.is_multi_signal_expansion() is True


def test_multi_signal_expansion_returns_false_when_signals_do_not_all_improve():
    """Reject multi-signal expansion when some role signals remain flat."""

    baseline = UsageWindow(
        targets=10,
        routes_run=50,
    )

    recent = UsageWindow(
        targets=12,
        routes_run=60,
    )
    # 2. Pass route participation directly as decimals to RoleProfile
    profile = RoleProfile(
        baseline_route_participation=0.60,
        recent_route_participation=0.75,
        baseline_target_share=0.18,
        recent_target_share=0.18,
        baseline_usage=baseline,
        recent_usage=recent,
    )

    signal = RoleSignal(profile)

    assert signal.is_multi_signal_expansion() is False
