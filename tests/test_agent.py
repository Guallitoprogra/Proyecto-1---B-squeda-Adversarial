import itertools
import threading
import unittest
from time import perf_counter

from agent import WIN, SearchStats, assignment_distance, choose_action, evaluate
from hoppers import CAMP_P1, CAMP_P2, P1, P2, State, actions, apply_action, initial_state, winner


def almost_won(owner):
    board = [[0] * 10 for _ in range(10)]
    for cell in CAMP_P2:
        board[cell[0]][cell[1]] = P1
    for cell in CAMP_P1:
        board[cell[0]][cell[1]] = P2
    if owner == P1:
        board[5][9], board[4][9] = 0, P1
    else:
        board[4][0], board[5][0] = 0, P2
    # Alejamos también una ficha rival para que todavía no haya un ganador.
    if owner == P1:
        board[4][0], board[5][0] = 0, P2
    else:
        board[5][9], board[4][9] = 0, P1
    return State(tuple(tuple(row) for row in board), owner)


def plain_minimax(state, depth):
    won = winner(state)
    if won is not None:
        return WIN + depth if won == P1 else -WIN - depth
    if depth == 0:
        return evaluate(state)
    values = [plain_minimax(apply_action(state, action), depth - 1) for action in actions(state)]
    return (max(values) if state.turn == P1 else min(values)) if values else 0


class AgentTests(unittest.TestCase):
    def test_assignment_matches_exhaustive_solution(self):
        pieces = [(0, 0), (2, 3), (4, 1), (1, 1)]
        targets = [(7, 5), (1, 4), (4, 3), (2, 0)]
        expected = min(sum(max(abs(r - tr), abs(c - tc))
                           for (r, c), (tr, tc) in zip(pieces, order))
                       for order in itertools.permutations(targets))
        self.assertEqual(assignment_distance(pieces, targets), expected)

    def test_initial_evaluation_is_balanced(self):
        self.assertEqual(evaluate(initial_state()), 0)

    def test_both_players_take_immediate_win(self):
        for owner in (P1, P2):
            state = almost_won(owner)
            action = choose_action(state, depth=2, time_limit=2)
            self.assertEqual(winner(apply_action(state, action)), owner)

    def test_alpha_beta_matches_plain_minimax(self):
        for owner in (P1, P2):
            state = State(initial_state().board, owner)
            stats = SearchStats()
            action = choose_action(state, depth=2, time_limit=20, stats=stats)
            self.assertEqual(stats.depth, 2)
            expected = plain_minimax(state, 2)
            self.assertEqual(stats.value, expected)
            self.assertEqual(plain_minimax(apply_action(state, action), 1), expected)
            self.assertGreater(stats.cutoffs, 0)

    def test_tiny_budget_still_returns_legal_move(self):
        state = initial_state()
        started = perf_counter()
        stats = SearchStats()
        action = choose_action(state, depth=50, time_limit=0.001, stats=stats)
        self.assertIn(action, actions(state))
        self.assertLess(perf_counter() - started, 0.5)
        self.assertEqual(stats.depth, 0)

    def test_cancellation_returns_fallback(self):
        cancelled = threading.Event()
        cancelled.set()
        self.assertIn(choose_action(initial_state(), cancel=cancelled), actions(initial_state()))

    def test_terminal_has_no_action(self):
        state = almost_won(P1)
        state = apply_action(state, ((4, 9), (5, 9)))
        self.assertIsNone(choose_action(state))

    def test_parameters_are_validated(self):
        for depth in (0, -1, 1.5, True):
            with self.assertRaises(ValueError):
                choose_action(initial_state(), depth=depth)
        for seconds in (0, -1, 31, float("nan"), float("inf")):
            with self.assertRaises(ValueError):
                choose_action(initial_state(), time_limit=seconds)


if __name__ == "__main__":
    unittest.main()
