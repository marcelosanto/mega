import tkinter as tk
from tkinter import messagebox
from ui import LoteriaUI
from database import DatabaseManager
from updates import UpdateManager
from config import LOTTERY_CONFIG, VERSION, UPDATE_BASE_URL


class LoteriaApp:
    def __init__(self, root):
        self.root = root
        self.root.title("🎯 Gerador Avançado de Números para Loterias")
        self.root.geometry("1200x800")
        self.root.configure(bg='#1e1e2e')

        # Initialize variables
        self.loteria = tk.StringVar(value="Mega-Sena")
        self.metodo = tk.StringVar(value="Top Frequentes")
        self.num_dezenas = tk.IntVar(value=6)
        self.is_bolao = tk.BooleanVar(value=False)
        self.num_jogos = tk.IntVar(value=1)
        self.num_participantes = tk.IntVar(value=1)
        self.jogos_atuais = []

        # Initialize components
        self.config_loteria = LOTTERY_CONFIG
        self.db_manager = DatabaseManager()
        self.update_manager = UpdateManager(
            VERSION, UPDATE_BASE_URL, self.root)
        self.ui = LoteriaUI(self)

        # Load initial data and setup
        self.ui.carregar_dados()
        self.ui.atualizar_dezenas()
        self.root.after(1000, self.update_manager.check_for_updates, False)

    def __del__(self):
        self.db_manager.close()


if __name__ == "__main__":
    try:
        root = tk.Tk()
        app = LoteriaApp(root)
        root.mainloop()
    except Exception as e:
        print(f"Erro ao iniciar a aplicação: {e}")
