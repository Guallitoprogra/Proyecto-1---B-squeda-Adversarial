"""Reglas de Hoppers, independientes de la consola y del futuro agente."""

from dataclasses import dataclass


SIZE = 10
EMPTY = 0
P1 = 1
P2 = 2
DIRECTIONS = tuple(
    (dr, dc)
    for dr in (-1, 0, 1)
    for dc in (-1, 0, 1)
    if (dr, dc) != (0, 0)
)
CAMP_P1 = frozenset((r, c) for r in range(SIZE) for c in range(SIZE) if r + c <= 4)
CAMP_P2 = frozenset((9 - r, 9 - c) for r, c in CAMP_P1)

Position = tuple[int, int]
Action = tuple[Position, Position]


@dataclass(frozen=True)
class State:
    board: tuple[tuple[int, ...], ...]
    turn: int = P1


def initial_state():
    board = [[EMPTY] * SIZE for _ in range(SIZE)]
    for r, c in CAMP_P1:
        board[r][c] = P1
    for r, c in CAMP_P2:
        board[r][c] = P2
    return State(tuple(tuple(row) for row in board))


def player(state):
    return state.turn


def inside(r, c):
    return 0 <= r < SIZE and 0 <= c < SIZE


def jump_destinations(board, origin):
    """Busca todos los destinos alcanzables en una sola cadena de saltos."""
    visited = {origin}
    pending = [origin]
    while pending:
        r, c = pending.pop()
        for dr, dc in DIRECTIONS:
            middle = (r + dr, c + dc)
            landing = (r + 2 * dr, c + 2 * dc)
            lr, lc = landing
            if not inside(lr, lc) or landing in visited:
                continue
            mr, mc = middle
            # La ficha que se mueve ya no está en su casilla de origen.
            occupied = middle != origin and board[mr][mc] != EMPTY
            if occupied and board[lr][lc] == EMPTY:
                visited.add(landing)
                pending.append(landing)
    visited.remove(origin)
    return visited


def actions(state):
    """Cada jugada se representa como (origen, destino), incluso los saltos."""
    if terminal(state):
        return set()
    legal = set()
    for r in range(SIZE):
        for c in range(SIZE):
            if state.board[r][c] != player(state):
                continue
            origin = (r, c)
            for dr, dc in DIRECTIONS:
                nr, nc = r + dr, c + dc
                if inside(nr, nc) and state.board[nr][nc] == EMPTY:
                    legal.add((origin, (nr, nc)))
            # Distintas rutas al mismo destino producen el mismo estado.
            for destination in jump_destinations(state.board, origin):
                legal.add((origin, destination))
    return legal


def result(state, action):
    if action not in actions(state):
        raise ValueError("La jugada no es legal para el jugador en turno.")
    return apply_action(state, action)


def apply_action(state, action):
    """Aplicar una acción ya obtenida de actions; uso interno de la búsqueda."""
    (r, c), (nr, nc) = action
    # Copiamos las filas para que explorar una jugada no cambie el estado padre.
    board = [list(row) for row in state.board]
    board[r][c] = EMPTY
    board[nr][nc] = player(state)
    return State(tuple(tuple(row) for row in board), P2 if state.turn == P1 else P1)


def winner(state):
    if all(state.board[r][c] == P1 for r, c in CAMP_P2):
        return P1
    if all(state.board[r][c] == P2 for r, c in CAMP_P1):
        return P2
    return None


def terminal(state):
    return winner(state) is not None


def utility(state):
    """Valor desde P1: 1 si gana, -1 si gana P2 y 0 si nadie ha ganado."""
    winning_player = winner(state)
    if winning_player == P1:
        return 1
    if winning_player == P2:
        return -1
    return 0
