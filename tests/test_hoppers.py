import unittest

from hoppers import (
    CAMP_P1, CAMP_P2, P1, P2, State, actions, initial_state,
    player, result, terminal, utility, winner,
)


def position(pieces, turn=P1):
    """Tablero pequeño de prueba para aislar una regla a la vez."""
    board = [[0] * 10 for _ in range(10)]
    for (r, c), owner in pieces.items():
        board[r][c] = owner
    return State(tuple(tuple(row) for row in board), turn)


class GameTests(unittest.TestCase):
    def test_initial_board(self):
        state = initial_state()
        self.assertEqual(sum(row.count(P1) for row in state.board), 15)
        self.assertEqual(sum(row.count(P2) for row in state.board), 15)
        self.assertTrue(all(state.board[r][c] == P1 for r, c in CAMP_P1))
        self.assertTrue(all(state.board[r][c] == P2 for r, c in CAMP_P2))
        self.assertEqual(player(state), P1)
        self.assertFalse(terminal(state))
        self.assertEqual(utility(state), 0)

    def test_steps_in_all_eight_directions(self):
        state = position({(4, 4): P1})
        expected = {((4, 4), (r, c)) for r in range(3, 6) for c in range(3, 6)
                    if (r, c) != (4, 4)}
        self.assertEqual(actions(state), expected)

    def test_corner_does_not_wrap(self):
        self.assertEqual(actions(position({(0, 0): P1})), {
            ((0, 0), (0, 1)), ((0, 0), (1, 0)), ((0, 0), (1, 1)),
        })

    def test_chain_can_turn_and_stop_early(self):
        state = position({(2, 2): P1, (2, 3): P1, (3, 4): P2})
        legal = actions(state)
        self.assertIn(((2, 2), (2, 4)), legal)
        self.assertIn(((2, 2), (4, 4)), legal)
        moved = result(state, ((2, 2), (4, 4)))
        self.assertEqual(moved.board[2][3], P1)
        self.assertEqual(moved.board[3][4], P2)

    def test_diagonal_jump_and_occupied_landing(self):
        state = position({(1, 1): P1, (2, 2): P2})
        self.assertIn(((1, 1), (3, 3)), actions(state))
        blocked = position({(1, 1): P1, (2, 2): P2, (3, 3): P2})
        self.assertNotIn(((1, 1), (3, 3)), actions(blocked))

    def test_jump_cycle_finishes_without_null_move(self):
        state = position({(2, 2): P1, (2, 3): P2, (3, 4): P2,
                          (4, 3): P2, (3, 2): P2})
        destinations = {end for start, end in actions(state) if start == (2, 2)}
        self.assertTrue({(2, 4), (4, 4), (4, 2)} <= destinations)
        self.assertNotIn((2, 2), destinations)

    def test_result_preserves_parent_and_changes_turn(self):
        state = initial_state()
        before = initial_state()
        action = sorted(actions(state))[0]
        moved = result(state, action)
        self.assertEqual(state, before)
        self.assertEqual(player(moved), P2)
        self.assertEqual(sum(row.count(P1) for row in moved.board), 15)
        self.assertEqual(sum(row.count(P2) for row in moved.board), 15)

    def test_rejects_wrong_player_and_illegal_move(self):
        state = initial_state()
        for action in [((9, 9), (5, 5)), ((0, 0), (5, 5)), ((0, 0), (0, 1))]:
            with self.assertRaises(ValueError):
                result(state, action)

    def test_both_players_can_win(self):
        for owner, camp, value in [(P1, CAMP_P2, 1), (P2, CAMP_P1, -1)]:
            state = position({cell: owner for cell in camp})
            self.assertEqual(winner(state), owner)
            self.assertTrue(terminal(state))
            self.assertEqual(utility(state), value)
            self.assertEqual(actions(state), set())

    def test_mixed_camp_is_not_a_win(self):
        pieces = {cell: P1 for cell in CAMP_P2}
        pieces[(9, 9)] = P2
        self.assertIsNone(winner(position(pieces)))


if __name__ == "__main__":
    unittest.main()
