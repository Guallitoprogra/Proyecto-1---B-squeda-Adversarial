"""Control de una partida; las condiciones de cierre no alteran los movimientos."""

from collections import Counter

from hoppers import actions, initial_state, result, winner


class Game:
    # La sesión guarda el historial; State solo guarda tablero y turno.
    def __init__(self, state=None, max_turns=600):
        self.state = state if state is not None else initial_state()
        # El estado inicial ya cuenta como la primera aparición de esa posición.
        self.history = Counter({self.state: 1})
        self.turns = 0
        self.max_turns = max_turns

    def outcome(self):
        won = winner(self.state)
        if won is not None:
            return f"Ganó el jugador {won}."
        # Son reglas de cierre de la aplicación para evitar sesiones interminables.
        # Una victoria se comprueba antes que cualquiera de estas condiciones.
        if self.history[self.state] >= 3:
            return "Tablas: la misma posición y turno se repitieron tres veces."
        if self.turns >= self.max_turns:
            return f"Tablas: se alcanzó el límite de {self.max_turns} turnos."
        if not actions(self.state):
            return "Tablas: el jugador en turno no tiene jugadas legales."
        return None

    def play(self, action):
        if self.outcome() is not None:
            raise ValueError("La partida ya terminó.")
        # Solo registramos la jugada después de que el motor la haya validado.
        self.state = result(self.state, action)
        self.turns += 1
        self.history[self.state] += 1
