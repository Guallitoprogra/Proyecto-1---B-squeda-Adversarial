import contextlib
import io
import unittest
from unittest.mock import patch

from hoppers import CAMP_P2, P1, State
from main import main, parse_action


class ConsoleTests(unittest.TestCase):
    def test_parse_action(self):
        self.assertEqual(parse_action("0 3 0 5"), ((0, 3), (0, 5)))
        for text in ("hola", "1 2 3", "1 2 3 4 5"):
            with self.assertRaises(ValueError):
                parse_action(text)

    def test_invalid_input_help_move_and_exit(self):
        output = io.StringIO()
        with patch("builtins.input", side_effect=["hola", "ayuda", "0 3 0 5", "salir"]), \
                contextlib.redirect_stdout(output):
            main()
        self.assertIn("Escribe cuatro números", output.getvalue())
        self.assertIn("0 3 0 5", output.getvalue())
        self.assertIn("Partida cerrada", output.getvalue())

    def test_winning_move_closes_game(self):
        board = [[0] * 10 for _ in range(10)]
        for r, c in CAMP_P2:
            board[r][c] = P1
        board[5][9] = 0
        board[4][9] = P1
        state = State(tuple(tuple(row) for row in board))
        output = io.StringIO()
        with patch("main.initial_state", return_value=state), \
                patch("builtins.input", return_value="4 9 5 9") as read, \
                contextlib.redirect_stdout(output):
            main()
        read.assert_called_once()
        self.assertIn("Ganó el jugador 1", output.getvalue())


if __name__ == "__main__":
    unittest.main()
