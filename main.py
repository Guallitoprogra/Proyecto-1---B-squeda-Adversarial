"""Modos de juego por consola."""

import argparse

from agent import SearchStats, choose_action
from game import Game

from hoppers import actions, initial_state, player


def show_board(state):
    print("\n    " + " ".join(str(c) for c in range(10)))
    print("   " + "--" * 10)
    for r, row in enumerate(state.board):
        print(f"{r:2} |" + " ".join("." if cell == 0 else str(cell) for cell in row))
    print("\n1 = jugador 1, 2 = jugador 2, . = casilla vacía")


def parse_action(text):
    try:
        r, c, nr, nc = map(int, text.split())
    except ValueError:
        raise ValueError("Escribe cuatro números: fila columna fila_destino columna_destino.") from None
    return ((r, c), (nr, nc))


def main(mode="humano-humano", depth=3, seconds=2.0, human=1, max_turns=600):
    game = Game(initial_state(), max_turns=max_turns)
    print(f"Hoppers — {mode}")
    print("Escribe origen y destino, por ejemplo: 0 3 0 5.")
    print("Comandos: ayuda (jugadas disponibles), salir (cerrar la partida).")
    while game.outcome() is None:
        state = game.state
        show_board(state)
        legal = actions(state)
        agent_turn = mode == "agente-agente" or (mode == "humano-agente" and state.turn != human)
        if agent_turn:
            stats = SearchStats()
            action = choose_action(state, depth, seconds, stats=stats, history=game.history)
            game.play(action)
            print(f"Agente {state.turn}: {action} | profundidad {stats.depth} | "
                  f"{stats.nodes} nodos | {stats.elapsed:.3f} s")
            continue
        try:
            text = input(f"\nTurno del jugador {player(state)}: ").strip().lower()
        except (EOFError, KeyboardInterrupt):
            print("\nPartida interrumpida.")
            return
        if text == "salir":
            print("Partida cerrada.")
            return
        if text == "ayuda":
            for (r, c), (nr, nc) in sorted(legal):
                print(f"  {r} {c} {nr} {nc}")
            continue
        try:
            # El motor valida también los saltos múltiples; la consola solo lee datos.
            game.play(parse_action(text))
        except ValueError as error:
            print(error)
    show_board(game.state)
    print(f"\n{game.outcome()}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Jugar Hoppers por consola")
    parser.add_argument("--mode", choices=["humano-humano", "humano-agente", "agente-agente"],
                        default="humano-agente")
    parser.add_argument("--depth", type=int, default=3)
    parser.add_argument("--seconds", type=float, default=2)
    parser.add_argument("--human", type=int, choices=[1, 2], default=1)
    parser.add_argument("--max-turns", type=int, default=600)
    options = parser.parse_args()
    if options.depth < 1 or not 0 < options.seconds <= 30 or options.max_turns < 1:
        parser.error("Usa profundidad y turnos positivos, y un tiempo entre 0 y 30 (sin incluir 0).")
    main(options.mode, options.depth, options.seconds, options.human, options.max_turns)
