import unittest

from game import Game
from hoppers import initial_state


class SessionTests(unittest.TestCase):
    def test_third_repetition_closes_session(self):
        game = Game()
        cycle = [((0, 3), (0, 5)), ((9, 6), (9, 4)),
                 ((0, 5), (0, 3)), ((9, 4), (9, 6))]
        for action in cycle * 2:
            game.play(action)
        self.assertEqual(game.state, initial_state())
        self.assertIn("tres veces", game.outcome())
        with self.assertRaises(ValueError):
            game.play(cycle[0])

    def test_turn_limit(self):
        game = Game(max_turns=1)
        game.play(((0, 3), (0, 5)))
        self.assertIn("límite de 1 turnos", game.outcome())


if __name__ == "__main__":
    unittest.main()
