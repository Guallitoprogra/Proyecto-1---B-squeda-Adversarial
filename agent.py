"""Minimax con poda alfa-beta y profundización iterativa."""

from dataclasses import dataclass
from functools import lru_cache
from math import inf, isfinite
from time import perf_counter

from hoppers import CAMP_P1, CAMP_P2, P1, P2, actions, apply_action, winner


# Ganar debe pesar más que cualquier mejora de distancia en un tablero sin ganador.
WIN = 100_000


def assignment_distance(pieces, targets):
    """Costo mínimo de asignar una ficha a cada meta (algoritmo húngaro)."""
    # La distancia de Chebyshev cuenta pasos cuando se permiten diagonales.
    costs = [[max(abs(r - tr), abs(c - tc)) for tr, tc in targets]
             for r, c in pieces]
    n = len(pieces)
    if n != len(targets):
        raise ValueError("La evaluación requiere 15 fichas de cada jugador.")
    # Las filas son fichas y las columnas son metas. El índice 0 sirve de apoyo.
    # u y v ajustan costos; matched indica qué ficha está asignada a cada meta.
    u, v, matched = [0] * (n + 1), [0] * (n + 1), [0] * (n + 1)
    for i in range(1, n + 1):
        matched[0] = i
        column = 0
        best = [inf] * (n + 1)
        used = [False] * (n + 1)
        previous = [0] * (n + 1)
        # Buscamos una meta libre, permitiendo reasignar las fichas ya colocadas.
        while True:
            used[column] = True
            row = matched[column]
            delta, next_column = inf, 0
            for j in range(1, n + 1):
                if not used[j]:
                    cost = costs[row - 1][j - 1] - u[row] - v[j]
                    if cost < best[j]:
                        best[j], previous[j] = cost, column
                    if best[j] < delta:
                        delta, next_column = best[j], j
            # Ajustamos los costos para avanzar por la alternativa menos costosa.
            for j in range(n + 1):
                if used[j]:
                    u[matched[j]] += delta
                    v[j] -= delta
                else:
                    best[j] -= delta
            column = next_column
            if matched[column] == 0:
                break
        # Recorremos el camino encontrado y actualizamos las asignaciones.
        while column:
            previous_column = previous[column]
            matched[column] = matched[previous_column]
            column = previous_column
    return -v[0]


# En distintas ramas suelen repetirse las mismas fichas de un equipo.
# La caché permite reutilizar su puntuación sin resolver otra vez la asignación.
@lru_cache(maxsize=30_000)
def team_score(pieces, owner):
    targets = CAMP_P2 if owner == P1 else CAMP_P1
    arrived = sum(cell in targets for cell in pieces)
    distance = assignment_distance(pieces, sorted(targets))
    # Asignar metas distintas evita que todas las fichas busquen la misma esquina.
    return 30 * arrived - 10 * distance


def evaluate(state):
    """Positivo favorece a P1; negativo favorece a P2."""
    pieces1, pieces2 = [], []
    for r, row in enumerate(state.board):
        for c, owner in enumerate(row):
            if owner == P1:
                pieces1.append((r, c))
            elif owner == P2:
                pieces2.append((r, c))
    return team_score(tuple(pieces1), P1) - team_score(tuple(pieces2), P2)


@dataclass
class SearchStats:
    # Datos para mostrar cuánto exploró el agente; no forman parte del tablero.
    depth: int = 0
    nodes: int = 0
    cutoffs: int = 0
    elapsed: float = 0.0
    value: float | None = None


class SearchTimeout(Exception):
    # Esta señal permite salir de varios niveles de recursión al agotarse el tiempo.
    pass


def ordered_actions(state, preferred=None):
    targets = CAMP_P2 if state.turn == P1 else CAMP_P1
    direction = 1 if state.turn == P1 else -1

    def priority(action):
        start, end = action
        progress = direction * (sum(end) - sum(start))
        # Primero la mejor jugada anterior, después entrar en meta y avanzar.
        return (action == preferred, int(end in targets) - int(start in targets), progress)

    # El desempate fijo hace reproducibles las pruebas sin depender del orden de un set.
    return sorted(sorted(actions(state)), key=priority, reverse=True)


def choose_action(state, depth=3, time_limit=2.0, *, stats=None, history=None, cancel=None):
    """Devuelve una acción legal, o None si el estado es terminal o está bloqueado.

    history contiene estados reales anteriores, incluido el actual. La tercera
    repetición se valora como tablas cuando la sesión usa esa regla de cierre.
    """
    if isinstance(depth, bool) or not isinstance(depth, int) or depth < 1:
        raise ValueError("La profundidad debe ser un entero mayor o igual a 1.")
    if not isfinite(time_limit) or not 0 < time_limit <= 30:
        raise ValueError("El tiempo debe ser mayor que 0 y como máximo 30 segundos.")
    started = perf_counter()
    # Dejamos margen para terminar la llamada y entregar la jugada.
    deadline = started + time_limit * 0.95
    stats = stats if stats is not None else SearchStats()
    stats.depth = stats.nodes = stats.cutoffs = 0
    stats.value = None
    legal = ordered_actions(state)
    if not legal:
        stats.elapsed = perf_counter() - started
        return None
    # Si no alcanza el tiempo ni para profundidad 1, todavía tenemos una respuesta legal.
    best_action = legal[0]
    repetitions = dict(history or {})
    repetitions[state] = max(1, repetitions.get(state, 0))

    def check_time():
        # Reiniciar o cerrar la ventana también puede cancelar esta búsqueda.
        if perf_counter() >= deadline or (cancel is not None and cancel.is_set()):
            raise SearchTimeout

    def search(node, remaining, alpha, beta):
        check_time()
        stats.nodes += 1
        won = winner(node)
        if won is not None:
            # A igual victoria, preferimos alcanzarla antes; ante una derrota, retrasarla.
            return WIN + remaining if won == P1 else -WIN - remaining
        if repetitions.get(node, 0) >= 3:
            return 0
        if remaining == 0:
            # Aquí dejamos de simular y estimamos la posición con la heurística.
            value = evaluate(node)
            check_time()
            return value
        moves = ordered_actions(node)
        check_time()
        if not moves:
            return 0
        value = -inf if node.turn == P1 else inf
        for action in moves:
            # La acción ya viene del motor; no hace falta generar todas otra vez para validarla.
            child = apply_action(node, action)
            repetitions[child] = repetitions.get(child, 0) + 1
            try:
                child_value = search(child, remaining - 1, alpha, beta)
            finally:
                # Al regresar, quitamos la visita de esta rama, incluso si hubo una interrupción.
                repetitions[child] -= 1
                if repetitions[child] == 0:
                    del repetitions[child]
            if node.turn == P1:
                # Toda la evaluación usa la perspectiva de P1: maximiza; P2 minimiza.
                value = max(value, child_value)
                alpha = max(alpha, value)
            else:
                value = min(value, child_value)
                beta = min(beta, value)
            if alpha >= beta:
                # La rama ya no mejora una alternativa disponible más arriba en el árbol.
                stats.cutoffs += 1
                break
        return value

    try:
        # Solo reemplazamos la respuesta cuando termina una profundidad completa.
        for current_depth in range(1, depth + 1):
            check_time()
            iteration_best = best_action
            value = -inf if state.turn == P1 else inf
            alpha, beta = -inf, inf
            for action in ordered_actions(state, best_action):
                child = apply_action(state, action)
                repetitions[child] = repetitions.get(child, 0) + 1
                try:
                    score = search(child, current_depth - 1, alpha, beta)
                finally:
                    repetitions[child] -= 1
                    if repetitions[child] == 0:
                        del repetitions[child]
                better = score > value if state.turn == P1 else score < value
                if better:
                    value, iteration_best = score, action
                if state.turn == P1:
                    alpha = max(alpha, value)
                else:
                    beta = min(beta, value)
            best_action = iteration_best
            stats.depth, stats.value = current_depth, value
            if abs(value) >= WIN:
                break
    except SearchTimeout:
        # Conservamos la última profundidad completa, no una comparación a medias.
        pass
    stats.elapsed = perf_counter() - started
    return best_action
