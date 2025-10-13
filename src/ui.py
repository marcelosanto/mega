import os
import logging
from datetime import datetime
import json
import threading
from utils import get_resource_path
from config import LOTTERY_CONFIG, VERSION, UPDATE_BASE_URL
from updates import UpdateManager
from flet.matplotlib_chart import MatplotlibChart
import matplotlib.pyplot as plt
import flet as ft
import pandas as pd
import numpy as np
from math import comb
import matplotlib

matplotlib.use("svg")


class LoteriaUI:
    def __init__(self, app):
        self.app = app
        self.config_loteria = LOTTERY_CONFIG
        self.page = None
        self.logger = logging.getLogger(__name__)

    # MÉTODOS DE LÓGICA E DADOS
    # ===================================================================

    def carregar_dados(self):
        loteria = self.app.loteria.current.value
        config = self.config_loteria[loteria]
        try:
            xlsx_path = get_resource_path(config["caminho_xlsx"])
            if not os.path.exists(xlsx_path):
                raise FileNotFoundError(f"Arquivo {xlsx_path} não encontrado.")
            df = pd.read_excel(xlsx_path, sheet_name=0, skiprows=6)
            if not all(col in df.columns for col in config["colunas_numeros"]):
                raise ValueError("Colunas de números não encontradas.")
            self.app.numeros_flat = df[config["colunas_numeros"]].values.flatten()
            self.app.freq = np.bincount(
                self.app.numeros_flat, minlength=config["num_total"] + 1
            )[1:]
        except Exception as e:
            self.logger.error(f"Erro ao carregar dados: {e}")
            self.show_snackbar(f"❌ Erro ao carregar dados: {e}", "#ef4444")
            self.app.freq = np.zeros(config["num_total"], dtype=int)

    def calcular_preco(self, num_dezenas):
        loteria = self.app.loteria.current.value
        config = self.config_loteria[loteria]
        num_combs = 0
        if loteria == "Mega-Sena" and 6 <= num_dezenas <= 20:
            num_combs = comb(num_dezenas, 6)
        elif loteria == "Loto Fácil" and 15 <= num_dezenas <= 20:
            num_combs = comb(num_dezenas, 15)
        return num_combs * config["preco_base"]

    def gerar_numeros(self, metodo, num_dezenas):
        loteria = self.app.loteria.current.value
        config = self.config_loteria[loteria]
        try:
            if len(self.app.freq) == 0 or np.all(self.app.freq == 0):
                return sorted(
                    np.random.choice(
                        range(1, config["num_total"] + 1),
                        size=num_dezenas,
                        replace=False,
                    ).tolist()
                )
            numeros_ordenados = np.argsort(self.app.freq)[::-1] + 1
            if metodo == "top_frequentes":
                top_n = 40 if loteria == "Mega-Sena" else 25
                top = numeros_ordenados[:top_n]
                if len(top) < num_dezenas:
                    raise ValueError("Não há números suficientes.")
                numeros_selecionados = np.random.choice(
                    top, size=num_dezenas, replace=False
                )
            elif metodo == "probabilistico":
                probs = self.app.freq / self.app.freq.sum()
                numeros_selecionados = np.random.choice(
                    range(1, config["num_total"] + 1),
                    size=num_dezenas,
                    replace=False,
                    p=probs,
                )
            else:
                raise ValueError("Método inválido.")
            return sorted([int(x) for x in numeros_selecionados])
        except Exception as e:
            self.logger.error(f"Erro ao gerar números: {e}")
            self.show_snackbar(f"❌ Erro: {e}", "#ef4444")
            return []

    # MÉTODOS DE UI (EVENT HANDLERS E HELPERS)
    # ===================================================================

    def show_snackbar(self, message, color="#333333", duration=4000):
        if not self.page:
            return
        self.page.open(
            ft.SnackBar(
                content=ft.Text(message, color="white"),
                bgcolor=color,
                duration=duration,
            )
        )
        # self.page.snack_bar.open = True
        self.page.update()

    def close_dialog(self, e=None):
        if self.page and self.page.dialog:
            self.page.dialog.open = False
            self.page.update()

    def atualizar_dezenas(self, e):
        loteria = self.app.loteria.current.value
        config = self.config_loteria[loteria]
        self.dezenas_slider.min = config["min_dezenas"]
        self.dezenas_slider.max = config["max_dezenas"]
        self.dezenas_slider.value = config["min_dezenas"]
        self.atualizar_label_dezenas()
        self.info_content.controls.clear()
        self.info_content.controls.extend(self.build_info_cards(config))
        self.carregar_dados()
        self.page.update()

    def atualizar_label_dezenas(self, e=None):
        preco = self.calcular_preco(int(self.app.num_dezenas.current.value))
        self.dezenas_info.value = f"R$ {preco:.2f}"
        if self.page:
            self.page.update()

    def toggle_bolao(self, e):
        self.bolao_container.visible = self.app.is_bolao.current.value
        if not self.app.is_bolao.current.value:
            self.app.num_jogos.current.value = "1"
            self.app.num_participantes.current.value = "1"
        self.page.update()

    def gerar_jogos(self, e):
        self.gerar_btn.disabled = True
        self.gerar_btn.text = "Gerando..."
        self.page.update()
        self.numeros_container.controls.clear()
        self.resumo_content.controls.clear()
        self.app.jogos_atuais = []
        try:
            num_jogos = (
                int(self.app.num_jogos.current.value)
                if self.app.is_bolao.current.value
                else 1
            )
            num_dezenas = int(self.app.num_dezenas.current.value)
            metodo = self.app.metodo.current.value.lower().replace(" ", "_")
            loteria = self.app.loteria.current.value
            config = self.config_loteria[loteria]
            total_preco = 0
            for i in range(num_jogos):
                numeros = self.gerar_numeros(metodo, num_dezenas)
                if not numeros:
                    continue
                self.app.jogos_atuais.append(numeros)
                bola_row = ft.Row(
                    [
                        ft.Container(
                            content=ft.Text(f"{num:02d}", color="white", weight="bold"),
                            bgcolor=config["cor_bola"],
                            width=40,
                            height=40,
                            border_radius=20,
                            alignment=ft.alignment.center,
                        )
                        for num in numeros
                    ],
                    wrap=True,
                )
                self.numeros_container.controls.append(
                    ft.Container(
                        ft.Column(
                            [
                                ft.Text(f"Jogo {i+1}", weight="bold", color="black"),
                                bola_row,
                            ]
                        ),
                        padding=15,
                        border_radius=8,
                        border=ft.border.all(1, "#e0e0e0"),
                    )
                )
                total_preco += self.calcular_preco(num_dezenas)

            num_participantes = (
                int(self.app.num_participantes.current.value)
                if self.app.is_bolao.current.value
                else 1
            )
            preco_por_participante = total_preco / max(num_participantes, 1)

            self.resumo_content.controls.append(
                ft.Column(
                    [
                        ft.Row(
                            [
                                ft.Text("Custo Total:", color="black"),
                                ft.Text(
                                    f"R$ {total_preco:.2f}",
                                    weight="bold",
                                    size=16,
                                    color="#059669",
                                ),
                            ]
                        ),
                        ft.Row(
                            [
                                ft.Text("Participantes:", color="black"),
                                ft.Text(
                                    f"{num_participantes}", weight="bold", color="black"
                                ),
                            ]
                        ),
                        ft.Row(
                            [
                                ft.Text("Por Participante:", color="black"),
                                ft.Text(
                                    f"R$ {preco_por_participante:.2f}",
                                    weight="bold",
                                    size=16,
                                    color="#059669",
                                ),
                            ]
                        ),
                    ]
                )
            )
            self.salvar_button.disabled = False
            self.show_snackbar("✅ Números gerados com sucesso!", color="#10b981")
        except Exception as ex:
            self.logger.error(f"Erro ao gerar jogos: {ex}")
            self.show_snackbar(f"❌ Erro: {ex}", "#ef4444")
        finally:
            self.gerar_btn.disabled = False
            self.gerar_btn.text = "🎲 Gerar Números"
            self.page.update()

    def criar_janela_salvar(self, e):
        if not self.app.jogos_atuais:
            return self.show_snackbar("⚠️ Nenhum jogo gerado para salvar!", "#f59e0b")
        try:
            if self.app.db_manager.salvar_no_banco(self.app, ""):
                self.salvar_button.disabled = True
                self.show_snackbar("✅ Jogo salvo com sucesso!", "#10b981")
            else:
                self.show_snackbar("❌ Erro ao salvar jogo.", "#ef4444")
        except Exception as ex:
            self.logger.error(f"Erro ao salvar jogo: {ex}")
            self.show_snackbar(f"❌ Erro: {ex}", "#ef4444")

    def mostrar_grafico(self, e):
        loteria = self.app.loteria.current.value
        config = self.config_loteria[loteria]
        if len(self.app.freq) == 0:
            return self.show_snackbar(
                "❌ Dados de frequência não disponíveis.", "#ef4444"
            )

        fig, ax = plt.subplots()
        ax.bar(
            range(1, config["num_total"] + 1), self.app.freq, color=config["cor_bola"]
        )
        ax.set_title(f"Frequência - {loteria}")
        chart = MatplotlibChart(fig, expand=True)

        dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text("Frequência de Números"),
            content=chart,
            actions=[ft.TextButton("Fechar", on_click=self.close_dialog)],
        )

        # APLICA A CORREÇÃO AQUI:
        self.page.dialog = dialog  # Atribuir o diálogo à página
        self.page.open(dialog)  # Abrir com page.open()

    def abrir_historico(self, e):
        try:
            jogos = self.app.db_manager.carregar_historico()
            if not jogos:
                return self.show_snackbar(
                    "ℹ️ Nenhum jogo encontrado no histórico.", "#3b82f6"
                )

            rows = []
            for jogo in jogos:
                (id, loteria, metodo, _, dezenas, preco, bolao, n_jogos, _, data, _) = (
                    jogo
                )
                rows.append(
                    ft.DataRow(
                        cells=[
                            ft.DataCell(ft.Text(id)),
                            ft.DataCell(ft.Text(loteria)),
                            ft.DataCell(ft.Text(metodo)),
                            ft.DataCell(ft.Text(f"R$ {preco:.2f}")),
                            ft.DataCell(
                                ft.Text(
                                    datetime.strptime(
                                        data, "%Y-%m-%d %H:%M:%S"
                                    ).strftime("%d/%m/%Y")
                                )
                            ),
                        ]
                    )
                )

            table = ft.DataTable(
                columns=[
                    ft.DataColumn(ft.Text(c))
                    for c in ["ID", "Loteria", "Método", "Preço", "Data"]
                ],
                rows=rows,
            )

            dialog = ft.AlertDialog(
                modal=True,
                title=ft.Text("Histórico de Jogos"),
                content=ft.Container(content=table, width=700, height=400),
                actions=[ft.TextButton("Fechar", on_click=self.close_dialog)],
            )

            # APLICA A CORREÇÃO AQUI:
            self.page.dialog = dialog  # Atribuir o diálogo à página
            self.page.open(dialog)  # Abrir com page.open()

        except Exception as ex:
            self.logger.error(f"Erro ao abrir histórico: {ex}")
            self.show_snackbar(f"❌ Erro ao abrir histórico: {ex}", "#ef4444")

    # MÉTODOS DE ATUALIZAÇÃO (UPDATE)
    # ===================================================================

    def on_check_updates_click(self, e):
        self.show_snackbar("🔎 Verificando atualizações...", color="#3b82f6")
        threading.Thread(target=self._check_updates_worker).start()

    def _check_updates_worker(self):
        manager = UpdateManager(current_version=VERSION, repo_url=UPDATE_BASE_URL)
        result = manager.check_for_updates()
        if result.get("update_available"):
            self.show_update_dialog(result, manager)
        elif result.get("error"):
            self.show_snackbar(f"❌ {result['error']}", "#ef4444")
        else:
            self.show_snackbar("✅ Você já está na versão mais recente.", "#10b981")

    def show_update_dialog(self, update_info, manager):
        def start_update(e):
            self.close_dialog(e)
            self.show_snackbar("📥 Baixando atualização...", duration=10000)

            def download_worker():
                install_result = manager.download_and_install(
                    update_info["download_url"]
                )
                if install_result["success"]:
                    self.show_restart_dialog()
                else:
                    self.show_snackbar(f"❌ Erro: {install_result['error']}", "#ef4444")

            threading.Thread(target=download_worker).start()

        dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text("Atualização Disponível"),
            content=ft.Text(f"Nova versão {update_info['version']} disponível."),
            actions=[
                ft.TextButton("Depois", on_click=self.close_dialog),
                ft.ElevatedButton("Atualizar", on_click=start_update),
            ],
        )
        self.page.dialog = dialog
        dialog.open = True
        self.page.update()

    def show_restart_dialog(self):
        dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text("Atualização Concluída"),
            content=ft.Text("Reinicie o aplicativo para usar a nova versão."),
            actions=[ft.ElevatedButton("OK", on_click=self.close_dialog)],
        )
        self.page.dialog = dialog
        dialog.open = True
        self.page.update()

    def build_info_cards(self, config):
        return [
            ft.Container(
                content=ft.Column(
                    [
                        ft.Row(
                            [
                                ft.Icon(ft.Icons.INFO_ROUNDED, color="#3b82f6"),
                                ft.Text("Informações", weight="bold", color="black"),
                            ],
                            spacing=10,
                        ),
                        ft.Divider(height=1),
                        ft.Row(
                            [
                                ft.Text("Sorteados:", color="black"),
                                ft.Text(
                                    f"{config['num_sorteados']}",
                                    weight="bold",
                                    color="black",
                                ),
                            ]
                        ),
                        ft.Row(
                            [
                                ft.Text("Preço Base:", color="black"),
                                ft.Text(
                                    f"R$ {config['preco_base']:.2f}",
                                    weight="bold",
                                    color="black",
                                ),
                            ]
                        ),
                    ],
                    spacing=8,
                ),
                bgcolor="white",
                border_radius=8,
                padding=15,
                border=ft.border.all(1, "#e5e7eb"),
            ),
            ft.Container(
                content=ft.Column(
                    [
                        ft.Row(
                            [
                                ft.Icon(ft.Icons.LIGHTBULB_ROUNDED, color="#f59e0b"),
                                ft.Text("Dicas", weight="bold", color="black"),
                            ],
                            spacing=10,
                        ),
                        ft.Divider(height=1),
                        ft.Text(
                            "• Mais números = maior custo e maior chance.",
                            color="black",
                        ),
                    ],
                    spacing=8,
                ),
                bgcolor="white",
                border_radius=8,
                padding=15,
                border=ft.border.all(1, "#e5e7eb"),
            ),
        ]

    # MÉTODO PRINCIPAL DE CONSTRUÇÃO DA UI
    # ===================================================================
    def main(self, page: ft.Page):
        self.page = page
        page.title = "Gerador jogos de Loterias"
        page.bgcolor = "#f8fafc"
        page.padding = 0
        page.window_width, page.window_height = 1200, 800
        page.window_min_width, page.window_min_height = 800, 600

        page.theme = ft.Theme(
            color_scheme=ft.ColorScheme(
                primary="#3b82f6",
                on_primary="white",
                secondary="#10b981",
                on_secondary="white",
                surface="white",
                on_surface="#1f2937",
                background="#f8fafc",
                on_background="#1f2937",
            ),
            use_material3=True,
        )

        page.window_minimizable = True
        page.window_maximizable = True

        self.app.loteria = ft.Ref[ft.Dropdown]()
        self.app.num_dezenas = ft.Ref[ft.Slider]()
        self.app.metodo = ft.Ref[ft.Dropdown]()
        self.app.is_bolao = ft.Ref[ft.Checkbox]()
        self.app.num_jogos = ft.Ref[ft.TextField]()
        self.app.num_participantes = ft.Ref[ft.TextField]()

        self.dezenas_slider = ft.Slider(
            ref=self.app.num_dezenas,
            min=6,
            max=20,
            divisions=14,
            value=6,
            on_change=self.atualizar_label_dezenas,
        )
        self.dezenas_info = ft.Text("R$ 5.00", color="#059669", weight="bold")
        self.info_content = ft.Column(
            spacing=15, scroll=ft.ScrollMode.AUTO, expand=True
        )
        self.resumo_content = ft.Column(
            spacing=15, scroll=ft.ScrollMode.AUTO, expand=True
        )
        self.numeros_container = ft.Column(
            spacing=15, scroll=ft.ScrollMode.AUTO, expand=True
        )
        self.gerar_btn = ft.ElevatedButton(
            "🎲 Gerar Números",
            bgcolor="#3b82f6",
            color="white",
            height=48,
            on_click=self.gerar_jogos,
        )
        self.salvar_button = ft.ElevatedButton(
            "💾 Salvar Jogo",
            bgcolor="#10b981",
            color="white",
            height=40,
            disabled=True,
            on_click=self.criar_janela_salvar,
        )
        self.bolao_container = ft.Row(
            [
                ft.TextField(
                    ref=self.app.num_jogos,
                    label="Nº Jogos",
                    label_style=ft.TextStyle(color="black"),
                    color="black",
                    value="1",
                    expand=True,
                ),
                ft.TextField(
                    ref=self.app.num_participantes,
                    label="Participantes",
                    label_style=ft.TextStyle(color="black"),
                    color="black",
                    value="1",
                    expand=True,
                ),
            ],
            visible=False,
        )

        header = ft.Container(
            content=ft.Row(
                [
                    ft.Row(
                        [
                            ft.Icon(ft.Icons.CASINO_ROUNDED, color="#3b82f6", size=32),
                            ft.Column(
                                [
                                    ft.Text(
                                        "Gerador de Números",
                                        size=24,
                                        weight="w700",
                                        color="#010103",
                                    ),
                                    ft.Text("Para Loterias", size=16, color="#6b7280"),
                                ],
                                spacing=0,
                            ),
                        ],
                        spacing=12,
                        expand=True,
                    ),
                    ft.Row(
                        [
                            ft.IconButton(
                                icon=ft.Icons.BAR_CHART_ROUNDED,
                                tooltip="Frequência",
                                on_click=self.mostrar_grafico,
                            ),
                            ft.IconButton(
                                icon=ft.Icons.HISTORY,
                                tooltip="Histórico",
                                on_click=self.abrir_historico,
                            ),
                            ft.IconButton(
                                icon=ft.Icons.UPDATE_ROUNDED,
                                tooltip="Verificar Atualizações",
                                on_click=self.on_check_updates_click,
                            ),
                        ]
                    ),
                ],
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            ),
            bgcolor="white",
            padding=20,
            border=ft.border.only(bottom=ft.BorderSide(1, "#e5e7eb")),
        )

        left_panel = ft.Container(
            content=ft.Column(
                [
                    ft.Dropdown(
                        ref=self.app.loteria,
                        label="Loteria",
                        label_style=ft.TextStyle(color="black"),
                        color="black",
                        bgcolor="white",
                        options=[
                            ft.dropdown.Option("Mega-Sena"),
                            ft.dropdown.Option("Loto Fácil"),
                        ],
                        value="Mega-Sena",
                        on_change=self.atualizar_dezenas,
                    ),
                    ft.Dropdown(
                        ref=self.app.metodo,
                        label="Método",
                        label_style=ft.TextStyle(color="black"),
                        color="black",
                        bgcolor="white",
                        options=[
                            ft.dropdown.Option("Top Frequentes"),
                            ft.dropdown.Option("Probabilistico"),
                        ],
                        value="Top Frequentes",
                    ),
                    ft.Row(
                        [ft.Text("Dezenas:", color="black"), self.dezenas_info],
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    ),
                    self.dezenas_slider,
                    ft.Checkbox(
                        ref=self.app.is_bolao,
                        label="É um Bolão?",
                        label_style=ft.TextStyle(color="black"),
                        on_change=self.toggle_bolao,
                    ),
                    self.bolao_container,
                    ft.Divider(height=10, color="transparent"),
                    self.gerar_btn,
                    self.salvar_button,
                ],
                spacing=15,
            ),
            padding=20,
            border_radius=10,
            bgcolor="white",
            col={"xs": 12, "md": 4, "lg": 3},
        )

        right_panel = ft.Column(
            [
                ft.ResponsiveRow(
                    [
                        ft.Container(
                            content=ft.Column(
                                [
                                    ft.Text(
                                        "ℹ️ Informações", weight="w600", color="black"
                                    ),
                                    self.info_content,
                                ]
                            ),
                            padding=20,
                            border_radius=8,
                            bgcolor="white",
                            col={"xs": 12, "lg": 6},
                            expand=True,
                        ),
                        ft.Container(
                            content=ft.Column(
                                [
                                    ft.Text("💰 Resumo", weight="w600", color="black"),
                                    self.resumo_content,
                                ]
                            ),
                            padding=20,
                            border_radius=8,
                            bgcolor="white",
                            col={"xs": 12, "lg": 6},
                            expand=True,
                        ),
                    ],
                    vertical_alignment=ft.CrossAxisAlignment.START,
                    spacing=20,
                ),
                ft.Container(
                    content=ft.Column(
                        [
                            ft.Text("🎯 Números Gerados", weight="w600", color="black"),
                            self.numeros_container,
                        ]
                    ),
                    padding=20,
                    border_radius=8,
                    bgcolor="white",
                    expand=True,
                ),
            ],
            spacing=20,
            col={"xs": 12, "md": 8, "lg": 9},
            expand=True,
        )

        page.add(
            ft.Column(
                [
                    header,
                    ft.Container(
                        content=ft.ResponsiveRow(
                            [left_panel, right_panel],
                            spacing=20,
                            vertical_alignment=ft.CrossAxisAlignment.START,
                        ),
                        padding=20,
                        expand=True,
                    ),
                ],
                expand=True,
            )
        )
        self.atualizar_dezenas(None)
