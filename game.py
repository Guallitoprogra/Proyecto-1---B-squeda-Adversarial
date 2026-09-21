"""Control de una partida; las condiciones de cierre no alteran los movimientos."""

from collections import Counter

from hoppers import actions, initial_state, result, winner


class Game:
    def __init__(self, state=None, max_turns=600):
        self.state = state if state is not None else initial_state()
        self.history = Counter({self.state: 1})
        self.turns = 0
        self.max_turns = max_turns

    def outcome(self):
        won = winner(self.state)
        if won is not None:
            return f"Ganó el jugador {won}."
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
        self.state = result(self.state, action)
        self.turns += 1
        self.history[self.state] += 1
