import flet as ft
from ui import LoteriaUI
from database import DatabaseManager
from updates import UpdateManager
from config import LOTTERY_CONFIG, VERSION, UPDATE_BASE_URL


class LoteriaApp:
    def __init__(self):
        self.loteria = ft.Ref[ft.Dropdown]()
        self.metodo = ft.Ref[ft.Dropdown]()
        self.num_dezenas = ft.Ref[ft.Slider]()
        self.is_bolao = ft.Ref[ft.Checkbox]()
        self.num_jogos = ft.Ref[ft.TextField]()
        self.num_participantes = ft.Ref[ft.TextField]()
        self.jogos_atuais = []
        self.numeros_flat = []
        self.freq = []
        self.db_manager = DatabaseManager()
        self.update_manager = UpdateManager(VERSION, UPDATE_BASE_URL)
        self.ui = LoteriaUI(self)

    def run(self):
        ft.app(target=self.ui.main)


if __name__ == "__main__":
    app = LoteriaApp()
    app.run()
