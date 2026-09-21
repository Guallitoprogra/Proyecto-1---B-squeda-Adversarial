"""Consola para probar las reglas con dos jugadores humanos."""

from hoppers import actions, initial_state, player, result, terminal, winner


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


def main():
    state = initial_state()
    print("Hoppers — partida entre dos personas")
    print("Escribe origen y destino, por ejemplo: 0 3 0 5.")
    print("Comandos: ayuda (jugadas disponibles), salir (cerrar la partida).")
    while not terminal(state):
        show_board(state)
        legal = actions(state)
        if not legal:
            print("No hay jugadas disponibles. Se detiene la sesión sin declarar ganador.")
            return
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
            state = result(state, parse_action(text))
        except ValueError as error:
            print(error)
    show_board(state)
    print(f"\nGanó el jugador {winner(state)}.")


if __name__ == "__main__":
    main()
