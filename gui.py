"""Ventana de Hoppers. Ejecutar con python gui.py."""

import queue
import threading
import tkinter as tk
from tkinter import ttk

from agent import SearchStats, choose_action
from game import Game
from hoppers import CAMP_P1, CAMP_P2, actions


CELL = 46
MARGIN = 28
BG = "#10191b"
PANEL = "#1a282b"
TEXT = "#edf5ee"
MUTED = "#a4b8b2"
MINT = "#8cdeb0"
CORAL = "#f4a28e"
MODES = ("Humano contra agente", "Agente contra agente", "Humano contra humano")


class HoppersApp:
    def __init__(self, root):
        self.root = root
        root.title("Hoppers | Juego de estrategia")
        root.configure(bg=BG)
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
        self.detail = tk.StringVar(value="Selecciona una ficha menta y luego un destino marcado.")
        self.summary = tk.StringVar(value="Todavía no hay jugadas del agente.")
        self.active_settings = (MODES[0], 3, 2.0, 1)

        style = ttk.Style(root)
        style.theme_use("clam")
        style.configure("TCombobox", fieldbackground=PANEL, background="#304448",
                        foreground=TEXT, arrowcolor=MINT, bordercolor="#405653", padding=6)
        style.map("TCombobox", fieldbackground=[("readonly", PANEL)],
                  foreground=[("readonly", TEXT)], selectbackground=[("readonly", PANEL)],
                  selectforeground=[("readonly", TEXT)])
        style.configure("TSpinbox", fieldbackground=PANEL, background="#304448",
                        foreground=TEXT, arrowcolor=MINT, bordercolor="#405653", padding=6)
        root.option_add("*TCombobox*Listbox.background", PANEL)
        root.option_add("*TCombobox*Listbox.foreground", TEXT)
        root.option_add("*TCombobox*Listbox.selectBackground", "#355849")

        header = tk.Frame(root, bg=BG)
        header.pack(fill="x", padx=26, pady=(20, 18))
        tk.Label(header, text="HOPPERS", font=("Segoe UI", 28, "bold"),
                 bg=BG, fg=TEXT).pack(side="left")
        tk.Label(header, text="ESTRATEGIA / 01", font=("Segoe UI", 10, "bold"),
                 bg=BG, fg=MINT).pack(side="right")
        content = tk.Frame(root, bg=BG)
        content.pack(padx=24, pady=(0, 24), fill="both")
        board_panel = tk.Frame(content, bg=PANEL, padx=12, pady=12)
        board_panel.pack(side="left", anchor="n")
        legend = tk.Frame(board_panel, bg=PANEL)
        legend.pack(fill="x", padx=16, pady=(2, 8))
        tk.Label(legend, text="●  JUGADOR 1", fg=MINT, bg=PANEL,
                 font=("Segoe UI", 10, "bold")).pack(side="left")
        tk.Label(legend, text="JUGADOR 2  ●", fg=CORAL, bg=PANEL,
                 font=("Segoe UI", 10, "bold")).pack(side="right")
        self.canvas = tk.Canvas(board_panel, width=516, height=516,
                                bg=PANEL, highlightthickness=0, cursor="hand2")
        self.canvas.pack()
        self.canvas.bind("<Button-1>", self.on_click)
        tk.Label(board_panel, text="15 fichas · 2 campamentos · una estrategia",
                 bg=PANEL, fg=MUTED, font=("Segoe UI", 10)).pack(pady=(5, 4))

        sidebar = tk.Frame(content, bg=BG, width=290)
        sidebar.pack(side="left", fill="y", padx=(22, 0))
        tk.Label(sidebar, text="Tu próxima jugada", font=("Segoe UI", 18, "bold"),
                 fg=TEXT, bg=BG).pack(anchor="w")
        tk.Label(sidebar, text="Cruza el tablero y ocupa el\ncampamento contrario.",
                 fg=MUTED, bg=BG, justify="left", font=("Segoe UI", 10)).pack(anchor="w", pady=(4, 16))
        controls = tk.Frame(sidebar, bg=PANEL, padx=16, pady=14)
        controls.pack(fill="x")

        def caption(text):
            tk.Label(controls, text=text, bg=PANEL, fg=MUTED,
                     font=("Segoe UI", 9, "bold")).pack(anchor="w", pady=(8, 5))

        caption("MODO DE JUEGO")
        ttk.Combobox(controls, textvariable=self.mode, values=MODES,
                     state="readonly", width=25).pack(fill="x")
        settings = tk.Frame(controls, bg=PANEL)
        settings.pack(fill="x", pady=(14, 0))
        for column, (label, variable) in enumerate((("Profundidad", self.depth), ("Segundos", self.seconds))):
            tk.Label(settings, text=label, bg=PANEL, fg=MUTED).grid(row=0, column=column, sticky="w", padx=(0, 14))
            ttk.Spinbox(settings, from_=1 if column == 0 else 0.1,
                        to=20 if column == 0 else 30, increment=1 if column == 0 else 0.5,
                        textvariable=variable, width=8).grid(row=1, column=column, sticky="w", pady=5, padx=(0, 14))
        caption("TU JUGADOR")
        ttk.Combobox(controls, textvariable=self.human, values=("1", "2"),
                     state="readonly", width=5).pack(fill="x")
        tk.Button(controls, text="Nueva partida  →", command=self.new_game,
                  bg=MINT, fg=BG, activebackground="#b1edc9", activeforeground=BG,
                  relief="flat", bd=0, cursor="hand2", font=("Segoe UI", 11, "bold"),
                  pady=10).pack(fill="x", pady=(18, 8))
        tk.Label(controls, text="Aplica los ajustes al iniciar otra partida.",
                 bg=PANEL, fg=MUTED, font=("Segoe UI", 9), wraplength=265,
                 justify="left").pack(anchor="w")
        tk.Label(sidebar, textvariable=self.status, bg=BG, fg=MINT,
                 font=("Segoe UI", 12, "bold"), wraplength=290,
                 justify="left").pack(anchor="w", pady=(18, 6))
        tk.Label(sidebar, textvariable=self.detail, bg=BG, fg=TEXT,
                 wraplength=290, justify="left").pack(anchor="w", pady=(0, 12))
        tk.Label(sidebar, textvariable=self.summary, bg=BG, fg=MUTED,
                 wraplength=290, justify="left").pack(anchor="w")
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
            self.canvas.create_text(center, 14, text=str(i), fill=MUTED)
            self.canvas.create_text(14, center, text=str(i), fill=MUTED)
        for r, row in enumerate(self.game.state.board):
            for c, piece in enumerate(row):
                cell = (r, c)
                x, y = MARGIN + c * CELL, MARGIN + r * CELL
                color = "#294c40" if cell in CAMP_P1 else "#503c38" if cell in CAMP_P2 else ("#263639" if (r + c) % 2 == 0 else "#213033")
                self.canvas.create_rectangle(x, y, x + CELL, y + CELL, fill=color, outline=PANEL, width=2)
                if cell == self.selected:
                    self.canvas.create_rectangle(x + 2, y + 2, x + CELL - 2, y + CELL - 2,
                                                 outline="#f5df99", width=3)
                if piece:
                    self.canvas.create_oval(x + 8, y + 11, x + CELL - 6, y + CELL - 5,
                                            fill="#10191b", outline="")
                    self.canvas.create_oval(x + 7, y + 6, x + CELL - 7, y + CELL - 8,
                                            fill=MINT if piece == 1 else CORAL,
                                            outline="#c6f5d9" if piece == 1 else "#ffccbd", width=2)
                    self.canvas.create_text(x + CELL / 2, y + CELL / 2, text=str(piece),
                                            fill=BG, font=("Segoe UI", 12, "bold"))
                elif cell in destinations:
                    self.canvas.create_oval(x + CELL / 2 - 6, y + CELL / 2 - 6,
                                            x + CELL / 2 + 6, y + CELL / 2 + 6,
                                            fill="#f5df99", outline="")
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
            self.detail.set(f"Ficha {cell}: los puntos dorados son destinos legales, incluidos saltos múltiples.")
            self.draw()
        else:
            self.detail.set("Selecciona una ficha de tu color o uno de sus destinos dorados.")

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
