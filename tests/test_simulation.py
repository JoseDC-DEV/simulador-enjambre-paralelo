import math
from dataclasses import replace

import pytest

from core.entities import Asteroid, Projectile
from core.simulation import (
    INITIAL_LIVES,
    LEFT,
    MAX_ASTEROID_SPEED,
    MAX_ASTEROID_RADIUS,
    MIN_ASTEROID_RADIUS,
    MUZZLE_OFFSET,
    PROJECTILE_SPEED,
    PROJECTILE_TTL,
    RIGHT,
    ROTATION_SPEED,
    SHOOT,
    SHOOT_COOLDOWN,
    THRUST,
    THRUST_ACCEL,
    apply_events,
    create_initial_state,
    run_frames,
    update,
)
from core.transformations import POINTS_PER_ASTEROID, update_asteroid
from core.waves import release_all

WIDTH, HEIGHT = 1200.0, 800.0
DT = 1 / 60
SIZES = [1000, 3000, 5000]
NO_EVENTS = frozenset()


def active_state(n, seed=1):
    """Partida con los n asteroides ya en pantalla (peor caso)."""
    return release_all(create_initial_state(n, WIDTH, HEIGHT, seed=seed))


# --- Inicialización ---

@pytest.mark.parametrize("n", SIZES)
def test_initial_state_queues_requested_asteroids_in_pending(n):
    state = create_initial_state(n, WIDTH, HEIGHT, seed=1)

    assert isinstance(state.pending, tuple)
    assert isinstance(state.asteroids, tuple)
    assert isinstance(state.projectiles, tuple)
    assert len(state.pending) == n
    assert state.asteroids == ()
    assert tuple(a.id for a in state.pending) == tuple(range(n))


def test_initial_state_basic_values():
    state = create_initial_state(10, WIDTH, HEIGHT)

    assert state.player.lives == INITIAL_LIVES
    assert (state.player.x, state.player.y) == (WIDTH / 2, HEIGHT / 2)
    assert (state.score, state.running, state.frame, state.won) == (0, True, 0, False)
    assert state.projectiles == ()


def test_pending_asteroids_spawn_on_an_edge_moving_inwards():
    state = create_initial_state(1000, WIDTH, HEIGHT, seed=3)

    for a in state.pending:
        assert 0 <= a.x <= WIDTH and 0 <= a.y <= HEIGHT
        assert abs(a.vx) <= MAX_ASTEROID_SPEED and abs(a.vy) <= MAX_ASTEROID_SPEED
        assert MIN_ASTEROID_RADIUS <= a.radius <= MAX_ASTEROID_RADIUS
        assert a.health == 1  # todos mueren de un impacto
        if a.x == 0.0:
            assert a.vx > 0
        elif a.x == WIDTH - 1.0:
            assert a.vx < 0
        elif a.y == 0.0:
            assert a.vy > 0
        else:
            assert a.y == HEIGHT - 1.0 and a.vy < 0


def test_same_seed_gives_same_state_and_different_seed_differs():
    assert create_initial_state(500, WIDTH, HEIGHT, seed=42) == create_initial_state(
        500, WIDTH, HEIGHT, seed=42
    )
    assert create_initial_state(500, WIDTH, HEIGHT, seed=1) != create_initial_state(
        500, WIDTH, HEIGHT, seed=2
    )


# --- Actualización secuencial ---

@pytest.mark.parametrize("n", SIZES)
def test_update_processes_all_active_asteroids_keeping_order(n):
    state = active_state(n)
    result = update(state, NO_EVENTS, DT, WIDTH, HEIGHT)

    assert len(result.asteroids) == n
    assert tuple(a.id for a in result.asteroids) == tuple(a.id for a in state.asteroids)


def test_update_returns_new_state_and_original_stays_intact():
    state = create_initial_state(1000, WIDTH, HEIGHT, seed=7)
    snapshot = create_initial_state(1000, WIDTH, HEIGHT, seed=7)

    result = update(state, frozenset({THRUST, LEFT}), DT, WIDTH, HEIGHT)

    assert result is not state
    assert result.frame == state.frame + 1
    assert state == snapshot


def test_update_moves_asteroids_correctly():
    state = active_state(100, seed=5)
    result = update(state, NO_EVENTS, DT, WIDTH, HEIGHT)

    for before, after in zip(state.asteroids, result.asteroids):
        assert after == update_asteroid(before, DT)


def test_asteroids_that_leave_the_screen_disappear_instead_of_wrapping():
    final = run_frames(active_state(1000, seed=9), 600, DT, WIDTH, HEIGHT)  # 10 s

    assert len(final.asteroids) < 1000  # algunos ya salieron
    assert all(
        -a.radius <= a.x <= WIDTH + a.radius and -a.radius <= a.y <= HEIGHT + a.radius
        for a in final.asteroids
    )


@pytest.mark.parametrize("n", SIZES)
def test_sequential_update_is_deterministic(n):
    first = run_frames(create_initial_state(n, WIDTH, HEIGHT, seed=11), 5, DT, WIDTH, HEIGHT)
    second = run_frames(create_initial_state(n, WIDTH, HEIGHT, seed=11), 5, DT, WIDTH, HEIGHT)

    assert first == second


def test_run_frames_counts_frames():
    state = create_initial_state(10, WIDTH, HEIGHT)

    assert run_frames(state, 0, DT, WIDTH, HEIGHT) == state
    assert run_frames(state, 12, DT, WIDTH, HEIGHT).frame == 12


# --- Cola con límite dentro de update ---

def test_screen_fills_up_to_the_limit_and_never_beyond():
    state = create_initial_state(1000, WIDTH, HEIGHT, seed=1, max_active=15)
    counts = []
    for _ in range(600):
        state = update(state, NO_EVENTS, DT, WIDTH, HEIGHT)
        counts.append(len(state.asteroids))
        if not state.running:
            break

    assert max(counts) == 15
    assert all(c <= 15 for c in counts)


def test_density_stays_constant_while_the_queue_lasts():
    state = create_initial_state(1000, WIDTH, HEIGHT, seed=5, max_active=15)
    for _ in range(1200):  # 20 s: ya han salido asteroides y han entrado otros
        state = replace(update(state, NO_EVENTS, DT, WIDTH, HEIGHT), running=True)

    assert len(state.asteroids) == 15
    assert len(state.pending) < 1000 - 15  # la cola se ha ido consumiendo


def test_every_asteroid_is_accounted_for_exactly_once():
    state = create_initial_state(60, WIDTH, HEIGHT, seed=2, max_active=10)
    seen = set()
    for _ in range(60 * 200):
        state = replace(update(state, NO_EVENTS, DT, WIDTH, HEIGHT), running=True)
        seen |= {a.id for a in state.asteroids}
        if not state.pending and not state.asteroids:
            break

    assert seen == set(range(60))  # todos entraron, ninguno se perdió
    assert state.pending == () and state.asteroids == ()


def test_difficulty_depends_on_total_queue_size():
    def duration(total):
        s = create_initial_state(total, WIDTH, HEIGHT, seed=4, max_active=10)
        frames = 0
        while (s.pending or s.asteroids) and frames < 60 * 3000:
            s = replace(update(s, NO_EVENTS, DT, WIDTH, HEIGHT), running=True)
            frames += 1
        return frames

    assert duration(20) < duration(80)


def test_victory_when_queue_is_exhausted_and_screen_is_clear():
    state = create_initial_state(0, WIDTH, HEIGHT)  # cola vacía
    done = run_frames(state, 1, DT, WIDTH, HEIGHT)

    assert done.running is False and done.won is True
    assert done.player.lives == INITIAL_LIVES  # ganó, no murió


def test_no_victory_while_asteroids_remain():
    state = create_initial_state(5, WIDTH, HEIGHT, seed=1, max_active=5)
    assert run_frames(state, 30, DT, WIDTH, HEIGHT).won is False


# --- Eventos ---

def test_no_events_keeps_player_velocity_and_angle():
    state = create_initial_state(1, WIDTH, HEIGHT)
    result = apply_events(state, NO_EVENTS, DT)

    assert result.player == state.player


def test_rotation_events_change_angle():
    state = create_initial_state(1, WIDTH, HEIGHT)
    right = apply_events(state, frozenset({RIGHT}), DT)
    left = apply_events(state, frozenset({LEFT}), DT)
    both = apply_events(state, frozenset({LEFT, RIGHT}), DT)

    assert right.player.angle == pytest.approx(state.player.angle + ROTATION_SPEED * DT)
    assert left.player.angle == pytest.approx(state.player.angle - ROTATION_SPEED * DT)
    assert both.player.angle == pytest.approx(state.player.angle)


def test_thrust_accelerates_along_facing_direction():
    base = create_initial_state(1, WIDTH, HEIGHT)
    facing_right = replace(base, player=replace(base.player, angle=0.0))

    result = apply_events(facing_right, frozenset({THRUST}), DT)

    assert result.player.vx == pytest.approx(THRUST_ACCEL * DT)
    assert result.player.vy == pytest.approx(0.0, abs=1e-9)
    assert facing_right.player.vx == 0.0  # el original no cambia


# --- Disparos ---

def empty_state():
    return create_initial_state(0, WIDTH, HEIGHT)


def test_shoot_creates_projectile_at_ship_nose():
    state = empty_state()  # la nave apunta hacia arriba
    result = apply_events(state, frozenset({SHOOT}), DT)

    assert len(result.projectiles) == 1
    p = result.projectiles[0]
    assert p.id == state.frame
    assert p.ttl == PROJECTILE_TTL
    assert p.vx == pytest.approx(0.0, abs=1e-9)
    assert p.vy == pytest.approx(-PROJECTILE_SPEED)
    assert p.y == pytest.approx(state.player.y - MUZZLE_OFFSET)
    assert state.projectiles == ()  # el original no cambia


def test_no_shoot_event_creates_no_projectile():
    assert apply_events(empty_state(), NO_EVENTS, DT).projectiles == ()


def test_shooting_respects_cooldown():
    state = empty_state()
    first = apply_events(state, frozenset({SHOOT}), DT)
    too_soon = apply_events(first, frozenset({SHOOT}), DT)
    assert len(too_soon.projectiles) == 1

    old_projectile = Projectile(
        id=0, x=0.0, y=0.0, vx=0.0, vy=0.0,
        ttl=PROJECTILE_TTL - SHOOT_COOLDOWN - 0.01,
    )
    ready = apply_events(replace(state, projectiles=(old_projectile,)), frozenset({SHOOT}), DT)
    assert len(ready.projectiles) == 2


# --- Colisiones dentro de update ---

def make_target(x, y) -> Asteroid:
    return Asteroid(id=0, x=x, y=y, vx=0.0, vy=0.0, radius=10.0, health=1)


def test_projectile_destroys_asteroid_and_scores():
    base = empty_state()
    state = replace(
        base,
        asteroids=(make_target(300.0, 300.0),),
        projectiles=(Projectile(id=0, x=300.0, y=300.0, vx=0.0, vy=0.0, ttl=1.0),),
        pending=(make_target(900.0, 700.0),),  # la cola no está vacía: no hay victoria
        max_active=0,  # y nada entra en este frame
    )
    result = update(state, NO_EVENTS, DT, WIDTH, HEIGHT)

    assert result.asteroids == ()
    assert result.score == POINTS_PER_ASTEROID
    assert result.running is True


def test_asteroid_touching_ship_ends_the_game():
    base = empty_state()
    state = replace(base, asteroids=(make_target(base.player.x, base.player.y),))
    result = update(state, NO_EVENTS, DT, WIDTH, HEIGHT)

    assert result.running is False and result.won is False
    assert result.player.lives == 0
    assert state.running is True and state.player.lives == INITIAL_LIVES
