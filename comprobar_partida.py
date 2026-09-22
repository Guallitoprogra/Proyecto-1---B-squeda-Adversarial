"""Prueba reproducible de una partida completa entre agentes."""

import argparse
from time import perf_counter

from agent import SearchStats, choose_action
from game import Game


def run(depth, seconds, max_turns):
    # Los dos jugadores usan el agente. La sesión se encarga de victoria y tablas.
    game = Game(max_turns=max_turns)
    started = perf_counter()
    slowest = 0
    while game.outcome() is None:
        stats = SearchStats()
        move = choose_action(game.state, depth, seconds, stats=stats, history=game.history)
        game.play(move)  # También valida cada acción que entrega el agente.
        # Interesa la decisión más lenta para comprobar el presupuesto por jugada.
        slowest = max(slowest, stats.elapsed)
    print(game.outcome())
    print(f"Jugadas: {game.turns}")
    print(f"Tiempo total: {perf_counter() - started:.3f} s")
    print(f"Decisión más lenta: {slowest:.3f} s")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--depth", type=int, default=1)
    parser.add_argument("--seconds", type=float, default=0.15)
    parser.add_argument("--max-turns", type=int, default=600)
    options = parser.parse_args()
    if options.depth < 1 or not 0 < options.seconds <= 30 or options.max_turns < 1:
        parser.error("Parámetros inválidos: profundidad y turnos positivos; 0 < segundos <= 30.")
    run(options.depth, options.seconds, options.max_turns)
