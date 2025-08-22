import tkinter as tk
from tkinter import ttk
from ui import LoteriaUI
from database import DatabaseManager
from updates import UpdateManager
from config import LOTTERY_CONFIG, VERSION, UPDATE_BASE_URL


class LoteriaApp:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Gerador de Números para Loterias")
        self.root.geometry("1000x700")
        self.root.configure(bg='#1e1e2e')

        # Initialize variables
        self.loteria = tk.StringVar(value="Mega-Sena")
        self.metodo = tk.StringVar(value="Top Frequentes")
        self.num_dezenas = tk.IntVar(value=6)
        self.is_bolao = tk.BooleanVar(value=False)
        self.num_jogos = tk.IntVar(value=1)
        self.num_participantes = tk.IntVar(value=1)
        self.jogos_atuais = []
        self.numeros_flat = []
        self.freq = []

        # Initialize managers
        self.db_manager = DatabaseManager()
        self.update_manager = UpdateManager(
            VERSION, UPDATE_BASE_URL)

        # Initialize UI
        self.ui = LoteriaUI(self)

        # Check for updates on startup
        self.update_manager.check_for_updates(show_message=False)

    def run(self):
        self.root.mainloop()


if __name__ == "__main__":
    app = LoteriaApp()
    app.run()
