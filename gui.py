"""Ventana de Hoppers. Ejecutar con python gui.py."""

import queue
import threading
import tkinter as tk
from tkinter import ttk

from agent import SearchStats, choose_action
from game import Game
from hoppers import CAMP_P1, CAMP_P2, actions


CELL = 52
MARGIN = 30
MODES = ("Humano contra agente", "Agente contra agente", "Humano contra humano")


class HoppersApp:
    def __init__(self, root):
        self.root = root
        root.title("Hoppers | Búsqueda adversarial")
        root.configure(bg="#f4f2ec")
        root.resizable(False, False)
        self.game = Game()
        self.selected = None
        self.busy = False
        self.finished = False
        self.generation = 0
        self.cancel = threading.Event()
        self.messages = queue.Queue()
        self.mode = tk.StringVar(value=MODES[0])
        self.depth = tk.StringVar(value="3")
        self.seconds = tk.StringVar(value="2")
        self.human = tk.StringVar(value="1")
        self.status = tk.StringVar()
        self.detail = tk.StringVar(value="Selecciona una ficha azul y luego un destino marcado.")
        self.summary = tk.StringVar(value="Todavía no hay jugadas del agente.")
        self.active_settings = (MODES[0], 3, 2.0, 1)

        tk.Label(root, text="HOPPERS", font=("Segoe UI", 25, "bold"),
                 bg="#f4f2ec", fg="#183447").pack(anchor="w", padx=25, pady=(16, 0))
        tk.Label(root, text="Lleva tus 15 fichas al campamento contrario",
                 font=("Segoe UI", 11), bg="#f4f2ec", fg="#52616b").pack(anchor="w", padx=26)
        controls = ttk.Frame(root, padding=(22, 12))
        controls.pack(fill="x")
        ttk.Combobox(controls, textvariable=self.mode, values=MODES, state="readonly", width=25).grid(row=0, column=0, columnspan=2, padx=4)
        ttk.Label(controls, text="Profundidad").grid(row=1, column=0, pady=(10, 0))
        ttk.Spinbox(controls, from_=1, to=20, textvariable=self.depth, width=5).grid(row=1, column=1, pady=(10, 0))
        ttk.Label(controls, text="Segundos").grid(row=1, column=2, padx=6, pady=(10, 0))
        ttk.Spinbox(controls, from_=0.1, to=30, increment=0.5, textvariable=self.seconds, width=5).grid(row=1, column=3, pady=(10, 0))
        ttk.Label(controls, text="Tu jugador").grid(row=0, column=2, padx=6)
        ttk.Combobox(controls, textvariable=self.human, values=("1", "2"), state="readonly", width=3).grid(row=0, column=3)
        ttk.Button(controls, text="Nueva partida", command=self.new_game).grid(row=0, column=4, padx=(16, 0))
        ttk.Label(controls, text="Los ajustes se aplican con Nueva partida.").grid(row=2, column=0, columnspan=5, sticky="w", padx=4, pady=(8, 0))

        self.canvas = tk.Canvas(root, width=580, height=565, bg="#f4f2ec", highlightthickness=0)
        self.canvas.pack(padx=15)
        self.canvas.bind("<Button-1>", self.on_click)
        tk.Label(root, textvariable=self.status, bg="#f4f2ec", fg="#183447",
                 font=("Segoe UI", 13, "bold")).pack(anchor="w", padx=27)
        tk.Label(root, textvariable=self.detail, bg="#f4f2ec", fg="#52616b",
                 wraplength=550, justify="left").pack(anchor="w", padx=27, pady=4)
        tk.Label(root, textvariable=self.summary, bg="#f4f2ec", fg="#52616b",
                 wraplength=550, justify="left").pack(anchor="w", padx=27, pady=(0, 18))
        root.protocol("WM_DELETE_WINDOW", self.close)
        self.draw()
        self.root.after(50, self.poll)

    def new_game(self):
        try:
            depth, seconds = int(self.depth.get()), float(self.seconds.get())
            if depth < 1 or not 0 < seconds <= 30:
                raise ValueError
        except ValueError:
            self.detail.set("Usa profundidad positiva y un tiempo mayor que 0 y hasta 30 segundos.")
            return
        self.cancel.set()
        self.cancel = threading.Event()
        self.generation += 1
        self.active_settings = (self.mode.get(), depth, seconds, int(self.human.get()))
        self.game = Game()
        self.selected = None
        self.busy = self.finished = False
        self.summary.set("Todavía no hay jugadas del agente.")
        self.detail.set("Selecciona una ficha y luego un destino marcado.")
        self.draw()
        self.maybe_agent()

    def is_agent_turn(self):
        mode, _, _, human = self.active_settings
        return mode == MODES[1] or (mode == MODES[0] and self.game.state.turn != human)

    def draw(self):
        self.canvas.delete("all")
        destinations = {end for start, end in actions(self.game.state) if start == self.selected}
        for i in range(10):
            center = MARGIN + i * CELL + CELL / 2
            self.canvas.create_text(center, 14, text=str(i), fill="#52616b")
            self.canvas.create_text(14, center, text=str(i), fill="#52616b")
        for r, row in enumerate(self.game.state.board):
            for c, piece in enumerate(row):
                cell = (r, c)
                x, y = MARGIN + c * CELL, MARGIN + r * CELL
                color = "#e1ecf1" if cell in CAMP_P1 else "#f6e4cd" if cell in CAMP_P2 else "#fffdf8"
                self.canvas.create_rectangle(x, y, x + CELL, y + CELL, fill=color, outline="#d6d5cd")
                if cell == self.selected:
                    self.canvas.create_rectangle(x + 2, y + 2, x + CELL - 2, y + CELL - 2,
                                                 outline="#237b68", width=3)
                if piece:
                    self.canvas.create_oval(x + 8, y + 8, x + CELL - 8, y + CELL - 8,
                                            fill="#28759b" if piece == 1 else "#c77629", outline="")
                    self.canvas.create_text(x + CELL / 2, y + CELL / 2, text=str(piece),
                                            fill="white", font=("Segoe UI", 12, "bold"))
                elif cell in destinations:
                    self.canvas.create_oval(x + 19, y + 19, x + 33, y + 33, fill="#237b68", outline="")
        self.status.set(f"Turno del jugador {self.game.state.turn} · {self.game.turns} jugadas")

    def on_click(self, event):
        if self.busy or self.finished or self.is_agent_turn():
            return
        r, c = (event.y - MARGIN) // CELL, (event.x - MARGIN) // CELL
        if not (0 <= r < 10 and 0 <= c < 10):
            return
        cell = (r, c)
        if self.selected is not None and (self.selected, cell) in actions(self.game.state):
            self.play((self.selected, cell))
        elif self.game.state.board[r][c] == self.game.state.turn:
            self.selected = cell
            self.detail.set(f"Ficha {cell}: los puntos verdes son destinos legales, incluidos saltos múltiples.")
            self.draw()
        else:
            self.detail.set("Selecciona una ficha de tu color o uno de sus destinos verdes.")

    def play(self, action):
        self.game.play(action)
        self.selected = None
        self.draw()
        outcome = self.game.outcome()
        if outcome:
            self.finished = True
            self.status.set(outcome)
            self.detail.set("La partida terminó. Puedes iniciar otra con Nueva partida.")
        else:
            self.detail.set(f"Última jugada: {action[0]} → {action[1]}.")
            self.maybe_agent()

    def maybe_agent(self):
        if self.busy or self.finished or not self.is_agent_turn():
            return
        self.busy = True
        self.status.set(f"El agente {self.game.state.turn} está pensando…")
        _, depth, seconds, _ = self.active_settings
        state, history = self.game.state, self.game.history.copy()
        generation, cancel = self.generation, self.cancel

        def work():
            stats = SearchStats()
            try:
                action = choose_action(state, depth, seconds, stats=stats, history=history, cancel=cancel)
                self.messages.put((generation, action, stats, None))
            except Exception as error:
                self.messages.put((generation, None, stats, str(error)))

        # La búsqueda no toca Tkinter: la ventana sigue respondiendo mientras piensa.
        threading.Thread(target=work, daemon=True).start()

    def poll(self):
        try:
            while True:
                generation, action, stats, error = self.messages.get_nowait()
                if generation != self.generation:
                    continue
                self.busy = False
                if error or action is None:
                    self.finished = True
                    self.status.set("La partida se detuvo.")
                    self.detail.set(error or self.game.outcome() or "No se recibió una jugada.")
                    continue
                self.summary.set(f"Agente: profundidad {stats.depth} · {stats.nodes} nodos · "
                                 f"{stats.cutoffs} podas · {stats.elapsed:.3f} s")
                self.play(action)
        except queue.Empty:
            pass
        self.root.after(50, self.poll)

    def close(self):
        self.cancel.set()
        self.root.destroy()


if __name__ == "__main__":
    root = tk.Tk()
    app = HoppersApp(root)
    root.mainloop()
