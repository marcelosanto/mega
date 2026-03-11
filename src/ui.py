import os
import logging
from datetime import datetime
import threading
import json
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

# Configuração para renderização de gráficos
matplotlib.use("svg")


class LoteriaUI:
    def __init__(self, app):
        self.app = app
        self.config_loteria = LOTTERY_CONFIG
        self.page = None
        self.logger = logging.getLogger(__name__)
        self.df_atual = None

    # MÉTODOS DE LÓGICA E DADOS
    # ===================================================================

    def carregar_dados(self):
        loteria = self.app.loteria.current.value
        config = self.config_loteria[loteria]
        try:
            xlsx_path = get_resource_path(config["caminho_xlsx"])
            if not os.path.exists(xlsx_path):
                raise FileNotFoundError(f"Arquivo {xlsx_path} não encontrado.")
            self.df_atual = pd.read_excel(xlsx_path, sheet_name=0, skiprows=6)
            self._atualizar_frequencia_app(self.df_atual, config)
        except Exception as e:
            self.logger.error(f"Erro ao carregar dados: {e}")
            self.app.freq = np.zeros(config["num_total"], dtype=int)

    def _atualizar_frequencia_app(self, df, config):
        nums = df[config["colunas_numeros"]].values.flatten()
        if "colunas_numeros_2" in config:
            nums2 = df[config["colunas_numeros_2"]].values.flatten()
            nums = np.concatenate([nums, nums2])

        nums = nums[~np.isnan(nums)].astype(int)
        self.app.freq = np.bincount(nums, minlength=config["num_total"] + 1)[1:]

    def calcular_preco(self, num_dezenas):
        loteria = self.app.loteria.current.value
        config = self.config_loteria[loteria]
        try:
            if loteria == "Mega-Sena":
                num_combs = comb(num_dezenas, 6)
            elif loteria == "Loto Fácil":
                num_combs = comb(num_dezenas, 15)
            elif loteria == "Quina":
                num_combs = comb(num_dezenas, 5)
            elif loteria == "Dupla Sena":
                num_combs = comb(num_dezenas, 6)
            elif loteria == "Loto Mania":
                return config["preco_base"]
            return num_combs * config["preco_base"]
        except:
            return 0

    def gerar_numeros(self, metodo, num_dezenas):
        loteria = self.app.loteria.current.value
        config = self.config_loteria[loteria]
        try:
            # Se for Surpresinha ou não tiver dados, faz sorteio 100% aleatório
            if (
                metodo == "surpresinha"
                or len(self.app.freq) == 0
                or np.all(self.app.freq == 0)
            ):
                return sorted(
                    np.random.choice(
                        range(1, config["num_total"] + 1),
                        size=num_dezenas,
                        replace=False,
                    ).tolist()
                )

            numeros_ordenados = (
                np.argsort(self.app.freq)[::-1] + 1
            )  # Mais frequentes no início

            # Define o tamanho do "pote" de números a considerar
            if loteria == "Loto Mania":
                limite = 75
            elif loteria in ["Mega-Sena", "Quina", "Dupla Sena"]:
                limite = 40
            else:
                limite = 20
            limite = max(
                limite, num_dezenas + 5
            )  # Garante que haja números suficientes

            if metodo == "top_frequentes":
                # Pega os primeiros do ranking (os que mais saem)
                top = numeros_ordenados[:limite]
                selecionados = np.random.choice(top, size=num_dezenas, replace=False)

            elif metodo == "menos_frequentes":
                # Pega os últimos do ranking (os que menos saem / mais atrasados)
                frias = numeros_ordenados[-limite:]
                selecionados = np.random.choice(frias, size=num_dezenas, replace=False)

            elif metodo == "probabilistico":
                # Sorteio viciado: quem sai mais tem maior probabilidade de ser escolhido
                probs = self.app.freq / self.app.freq.sum()
                selecionados = np.random.choice(
                    range(1, config["num_total"] + 1),
                    size=num_dezenas,
                    replace=False,
                    p=probs,
                )

            return sorted([int(x) for x in selecionados])
        except Exception as ex:
            self.logger.error(f"Erro gerar_numeros: {ex}")
            return []

    # MÉTODOS DE UI E UTILITÁRIOS
    # ===================================================================

    def show_snackbar(self, message, color="#333333"):
        if self.page:
            self.page.open(
                ft.SnackBar(content=ft.Text(message, color="white"), bgcolor=color)
            )

    def copiar_jogos(self, e):
        if not self.app.jogos_atuais:
            return
        texto = f"--- JOGOS {self.app.loteria.current.value.upper()} ---\n"
        for i, jogo in enumerate(self.app.jogos_atuais, 1):
            texto += f"Jogo {i:02d}: {' - '.join(f'{n:02d}' for n in jogo)}\n"
        self.page.set_clipboard(texto)
        self.show_snackbar("📋 Copiado para área de transferência!", "#3b82f6")

    def exportar_excel(self, e):
        if not self.app.jogos_atuais:
            return
        try:
            filename = f"Bolao_{self.app.loteria.current.value}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
            pd.DataFrame(self.app.jogos_atuais).to_excel(filename)
            self.show_snackbar(f"✅ Exportado: {filename}", "#10b981")
        except Exception as ex:
            self.show_snackbar(f"❌ Erro: {ex}", "#ef4444")

    def salvar_jogo_individual(self, numeros):
        backup = self.app.jogos_atuais
        self.app.jogos_atuais = [numeros]
        if self.app.db_manager.salvar_no_banco(self.app, "Manual"):
            self.show_snackbar("✅ Jogo salvo no Histórico!", "#10b981")
        self.app.jogos_atuais = backup

    def atualizar_dezenas(self, e):
        loteria = self.app.loteria.current.value
        config = self.config_loteria[loteria]
        min_v, max_v = config["min_dezenas"], config["max_dezenas"]

        self.dezenas_slider.min = min_v
        self.dezenas_slider.max = max_v
        self.dezenas_slider.divisions = max(1, max_v - min_v)
        self.dezenas_slider.value = min_v
        self.dezenas_slider.disabled = min_v == max_v
        self.dezenas_slider.label = "{value} dezenas"

        self.atualizar_label_dezenas()
        self.carregar_dados()
        self.page.update()

    def atualizar_label_dezenas(self, e=None):
        self.dezenas_info.value = (
            f"R$ {self.calcular_preco(int(self.dezenas_slider.value)):.2f}"
        )
        if self.page:
            self.page.update()

    def gerar_jogos(self, e):
        self.gerar_btn.disabled = True
        self.page.update()
        self.numeros_grid.controls.clear()
        self.resumo_content.controls.clear()
        self.app.jogos_atuais = []
        try:
            num_jogos = (
                int(self.app.num_jogos.current.value)
                if self.app.is_bolao.current.value
                else 1
            )
            config = self.config_loteria[self.app.loteria.current.value]
            for i in range(num_jogos):
                nums = self.gerar_numeros(
                    self.app.metodo.current.value.lower().replace(" ", "_"),
                    int(self.dezenas_slider.value),
                )
                if not nums:
                    continue
                self.app.jogos_atuais.append(nums)

                self.numeros_grid.controls.append(
                    ft.Container(
                        content=ft.Column(
                            [
                                ft.Row(
                                    [
                                        ft.Text(
                                            f"Jogo {i+1}",
                                            weight="bold",
                                            size=18,
                                            color="black",
                                        ),
                                        ft.Row(
                                            [
                                                ft.IconButton(
                                                    ft.Icons.INSERT_CHART_OUTLINED,
                                                    icon_color="#3b82f6",
                                                    tooltip="Analisar Força do Jogo",
                                                    on_click=lambda _, n=nums: self.analisar_jogo(
                                                        n
                                                    ),
                                                ),
                                                ft.IconButton(
                                                    ft.Icons.SAVE_OUTLINED,
                                                    icon_color="#10b981",
                                                    tooltip="Salvar no Histórico",
                                                    on_click=lambda _, n=nums: self.salvar_jogo_individual(
                                                        n
                                                    ),
                                                ),
                                            ],
                                            spacing=0,
                                        ),
                                    ],
                                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                                ),
                                ft.Row(
                                    [
                                        ft.Container(
                                            content=ft.Text(
                                                f"{n:02d}",
                                                color="white",
                                                weight="bold",
                                                size=16,
                                            ),
                                            bgcolor=config["cor_bola"],
                                            width=42,
                                            height=42,
                                            border_radius=21,
                                            alignment=ft.alignment.center,
                                            shadow=ft.BoxShadow(
                                                blur_radius=4, color="#4D000000"
                                            ),
                                        )
                                        for n in nums
                                    ],
                                    wrap=True,
                                    spacing=8,
                                ),
                            ]
                        ),
                        padding=15,
                        border_radius=12,
                        bgcolor="#ffffff",
                        col={"sm": 12, "md": 12, "lg": 6, "xl": 4},
                        border=ft.border.all(1, "#e2e8f0"),
                        shadow=ft.BoxShadow(blur_radius=8, color="#0D000000"),
                    )
                )

            custo = self.calcular_preco(int(self.dezenas_slider.value)) * num_jogos
            part = int(self.app.num_participantes.current.value or 1)

            # Resumo Financeiro mais limpo
            self.resumo_content.controls.append(
                ft.Row(
                    [
                        ft.Column(
                            [
                                ft.Text(f"Custo Total", color="#475569", size=14),
                                ft.Text(
                                    f"R$ {custo:.2f}",
                                    color="black",
                                    weight="bold",
                                    size=22,
                                ),
                            ],
                            expand=True,
                        ),
                        ft.Column(
                            [
                                ft.Text(f"Custo por Pessoa", color="#475569", size=14),
                                ft.Text(
                                    f"R$ {custo/part:.2f}",
                                    color="#059669",
                                    weight="bold",
                                    size=22,
                                ),
                            ],
                            expand=True,
                        ),
                        ft.ElevatedButton(
                            "📊 Exportar Excel",
                            on_click=self.exportar_excel,
                            bgcolor="#1e7145",
                            color="white",
                            height=50,
                        ),
                    ],
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                )
            )
            self.copiar_btn.visible = True
        finally:
            self.gerar_btn.disabled = False
            self.page.update()

    # ANÁLISE DE JOGO (GRÁFICO)
    # ===================================================================
    def analisar_jogo(self, jogo):
        if self.df_atual is None:
            self.show_snackbar("Aguarde o carregamento dos dados.", "#ef4444")
            return

        config = self.config_loteria[self.app.loteria.current.value]
        fig, ax = plt.subplots(figsize=(10, 4.5))
        fig.patch.set_facecolor("white")
        ax.set_facecolor("white")

        cores = ["#e2e8f0"] * config["num_total"]
        for n in jogo:
            if 1 <= n <= config["num_total"]:
                cores[n - 1] = config["cor_bola"]

        ax.bar(range(1, config["num_total"] + 1), self.app.freq, color=cores, width=0.8)

        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)
        ax.spines["left"].set_color("#cbd5e1")
        ax.spines["bottom"].set_color("#cbd5e1")
        ax.set_xlabel("Dezenas", fontsize=11, color="#475569")
        ax.set_ylabel("Frequência (Vezes Sorteado)", fontsize=11, color="#475569")
        ax.tick_params(colors="#475569")

        chart_box = ft.Container(
            content=MatplotlibChart(fig, expand=True, transparent=True),
            height=350,
            padding=10,
        )

        legenda = ft.Row(
            [
                ft.Container(
                    width=16, height=16, bgcolor=config["cor_bola"], border_radius=4
                ),
                ft.Text(
                    "Dezenas do Jogo Selecionado", color="black", size=14, weight="bold"
                ),
                ft.Container(
                    width=16,
                    height=16,
                    bgcolor="#e2e8f0",
                    border_radius=4,
                    margin=ft.margin.only(left=20),
                ),
                ft.Text("Histórico da Loteria", color="#475569", size=14),
            ],
            alignment=ft.MainAxisAlignment.CENTER,
        )

        dlg = ft.AlertDialog(
            title=ft.Text(
                f"Análise de Força do Jogo", weight="bold", color="black", size=22
            ),
            content=ft.Column([legenda, chart_box], width=900, height=420, spacing=15),
            bgcolor="#ffffff",
            shape=ft.RoundedRectangleBorder(radius=16),
        )
        dlg.actions = [
            ft.TextButton("Fechar Gráfico", on_click=lambda e: self.page.close(dlg))
        ]
        self.page.open(dlg)

    # HISTÓRICO E UPDATES
    # ===================================================================
    def abrir_historico(self, e):
        try:
            jogos = self.app.db_manager.carregar_historico()
            stats = self.app.db_manager.get_estatisticas()
            lista = ft.Column(spacing=12, scroll=ft.ScrollMode.AUTO, expand=True)

            dlg = ft.AlertDialog(
                title=ft.Text(
                    "Meus Jogos Registrados", size=22, weight="bold", color="black"
                ),
                content=ft.Container(
                    content=ft.Column(
                        [
                            ft.Row(
                                [
                                    ft.Icon(ft.Icons.MONETIZATION_ON, color="#059669"),
                                    ft.Text(
                                        f"Total Investido: R$ {stats.get('total_gasto', 0):.2f}",
                                        weight="bold",
                                        color="#059669",
                                        size=18,
                                    ),
                                ],
                                alignment=ft.MainAxisAlignment.CENTER,
                            ),
                            ft.Divider(),
                            lista,
                        ]
                    ),
                    width=550,
                    height=600,
                ),
                bgcolor="#ffffff",
                shape=ft.RoundedRectangleBorder(radius=16),
            )
            dlg.actions = [
                ft.TextButton("Fechar", on_click=lambda e: self.page.close(dlg))
            ]

            for j in jogos:
                nums_raw = json.loads(j[3])
                nums = (
                    nums_raw[0]
                    if len(nums_raw) > 0 and isinstance(nums_raw[0], list)
                    else nums_raw
                )
                cor_loto = self.config_loteria.get(j[1], {}).get("cor_bola", "#333333")

                lista.controls.append(
                    ft.Container(
                        content=ft.Column(
                            [
                                ft.Row(
                                    [
                                        ft.Text(
                                            f"{j[1]} - {j[9][:10]}",
                                            weight="bold",
                                            color="black",
                                            size=16,
                                        ),
                                        ft.Row(
                                            [
                                                ft.Text(
                                                    f"R$ {j[5]:.2f}",
                                                    color="#059669",
                                                    weight="bold",
                                                    size=16,
                                                ),
                                                ft.IconButton(
                                                    ft.Icons.DELETE_OUTLINE,
                                                    icon_color="#ef4444",
                                                    on_click=lambda _, id=j[0]: (
                                                        self.app.db_manager.excluir_jogo(
                                                            id
                                                        ),
                                                        self.page.close(dlg),
                                                        self.abrir_historico(None),
                                                    ),
                                                ),
                                            ]
                                        ),
                                    ],
                                    alignment="spaceBetween",
                                ),
                                ft.Row(
                                    [
                                        ft.Container(
                                            content=ft.Text(
                                                f"{n:02d}",
                                                color="white",
                                                size=12,
                                                weight="bold",
                                            ),
                                            bgcolor=cor_loto,
                                            width=28,
                                            height=28,
                                            border_radius=14,
                                            alignment=ft.alignment.center,
                                        )
                                        for n in nums
                                    ],
                                    wrap=True,
                                    spacing=5,
                                ),
                            ]
                        ),
                        padding=15,
                        border_radius=12,
                        bgcolor="#f8fafc",
                        border=ft.border.all(1, "#e2e8f0"),
                    )
                )
            self.page.open(dlg)
        except Exception as ex:
            self.show_snackbar(f"Erro ao abrir histórico: {ex}", "#ef4444")

    def verificar_atualizacao_auto(self):
        threading.Thread(target=self._check_updates_worker, daemon=True).start()

    def _check_updates_worker(self):
        try:
            res = self.app.update_manager.check_for_updates()
            if res.get("update_available"):
                dlg = ft.AlertDialog(
                    title=ft.Text(
                        "Atualização Disponível", color="black", weight="bold"
                    ),
                    content=ft.Text(
                        f"A versão {res['version']} do Loterias Pro já pode ser instalada.",
                        color="black",
                        size=16,
                    ),
                    bgcolor="#ffffff",
                    shape=ft.RoundedRectangleBorder(radius=16),
                )
                dlg.actions = [
                    ft.TextButton(
                        "Lembrar mais tarde", on_click=lambda e: self.page.close(dlg)
                    ),
                    ft.ElevatedButton(
                        "Atualizar Agora",
                        bgcolor="#3b82f6",
                        color="white",
                        on_click=lambda e: (
                            self.page.close(dlg),
                            self.app.update_manager.download_and_install(
                                res["download_url"]
                            ),
                        ),
                    ),
                ]
                self.page.open(dlg)
        except:
            pass

    # MÉTODO PRINCIPAL
    # ===================================================================
    def main(self, page: ft.Page):
        self.page = page
        page.title = "Loterias Pro"
        page.window.maximized = True
        page.theme = ft.Theme(color_scheme_seed="#2563eb")
        page.bgcolor = "#f1f5f9"

        self.app.loteria, self.app.metodo = ft.Ref[ft.Dropdown](), ft.Ref[ft.Dropdown]()
        self.app.is_bolao, self.app.num_jogos, self.app.num_participantes = (
            ft.Ref[ft.Checkbox](),
            ft.Ref[ft.TextField](),
            ft.Ref[ft.TextField](),
        )

        self.dezenas_slider = ft.Slider(
            min=6,
            max=20,
            value=6,
            label="{value} dezenas",
            on_change=self.atualizar_label_dezenas,
            active_color="#2563eb",
        )
        self.dezenas_info = ft.Text("R$ 5.00", color="#059669", weight="bold", size=18)
        self.numeros_grid = ft.ResponsiveRow(spacing=20, run_spacing=20)
        self.resumo_content = ft.Column()

        lbl_style = ft.TextStyle(color="black", weight="bold", size=16)

        self.gerar_btn = ft.ElevatedButton(
            "🎲 Gerar Números", bgcolor="#2563eb", color="white", expand=True, height=50
        )
        self.gerar_btn.on_click = self.gerar_jogos

        self.limpar_btn = ft.ElevatedButton(
            "🧹 Limpar Mesa", bgcolor="#cbd5e1", color="black", expand=True, height=50
        )
        self.limpar_btn.on_click = lambda _: (
            self.numeros_grid.controls.clear(),
            self.resumo_content.controls.clear(),
            page.update(),
        )

        self.copiar_btn = ft.IconButton(
            icon=ft.Icons.COPY,
            on_click=self.copiar_jogos,
            visible=False,
            icon_color="black",
            tooltip="Copiar todos os jogos",
        )

        header = ft.Container(
            content=ft.Row(
                [
                    ft.Row(
                        [
                            ft.Icon(ft.Icons.CASINO_OUTLINED, color="#2563eb", size=32),
                            ft.Text(
                                "Loterias Pro", size=28, weight="bold", color="black"
                            ),
                        ]
                    ),
                    ft.Row(
                        [
                            self.copiar_btn,
                            ft.ElevatedButton(
                                "Ver Histórico de Gastos",
                                icon=ft.Icons.HISTORY,
                                on_click=self.abrir_historico,
                                bgcolor="#e2e8f0",
                                color="black",
                            ),
                        ]
                    ),
                ],
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            ),
            padding=20,
            bgcolor="white",
            shadow=ft.BoxShadow(blur_radius=5, color="#1A000000"),
        )

        self.bolao_container = ft.Row(
            [
                ft.TextField(
                    ref=self.app.num_jogos,
                    label="Qtde de Jogos",
                    value="1",
                    expand=True,
                    color="black",
                    label_style=lbl_style,
                ),
                ft.TextField(
                    ref=self.app.num_participantes,
                    label="Pessoas no Bolão",
                    value="1",
                    expand=True,
                    color="black",
                    label_style=lbl_style,
                ),
            ],
            visible=False,
            spacing=15,
        )

        left = ft.Container(
            content=ft.Column(
                [
                    ft.Text(
                        "Configure a sua Aposta", size=22, weight="bold", color="black"
                    ),
                    ft.Divider(),
                    ft.Dropdown(
                        ref=self.app.loteria,
                        label="Escolha a Loteria",
                        label_style=lbl_style,
                        options=[
                            ft.dropdown.Option(k) for k in self.config_loteria.keys()
                        ],
                        value="Mega-Sena",
                        on_change=self.atualizar_dezenas,
                        color="black",
                    ),
                    # ADIÇÃO DOS NOVOS MÉTODOS AQUI NO DROPDOWN:
                    ft.Dropdown(
                        ref=self.app.metodo,
                        label="Método Estatístico",
                        label_style=lbl_style,
                        options=[
                            ft.dropdown.Option("Top Frequentes"),
                            ft.dropdown.Option(
                                "Menos Frequentes"
                            ),  # Algoritmo Novo (Frias)
                            ft.dropdown.Option("Probabilistico"),
                            ft.dropdown.Option(
                                "Surpresinha"
                            ),  # Algoritmo Novo (Aleatório)
                        ],
                        value="Top Frequentes",
                        color="black",
                    ),
                    ft.Row(
                        [
                            ft.Text(
                                "Custo por Aposta:",
                                color="black",
                                weight="bold",
                                size=16,
                            ),
                            self.dezenas_info,
                        ],
                        alignment="spaceBetween",
                    ),
                    self.dezenas_slider,
                    ft.Checkbox(
                        ref=self.app.is_bolao,
                        label="Ativar Múltiplos Jogos / Bolão",
                        on_change=lambda e: (
                            setattr(self.bolao_container, "visible", e.control.value),
                            page.update(),
                        ),
                        label_style=lbl_style,
                        check_color="white",
                        active_color="#2563eb",
                    ),
                    self.bolao_container,
                    ft.Row([self.gerar_btn, self.limpar_btn], spacing=15),
                ],
                spacing=20,
            ),
            padding=25,
            bgcolor="white",
            border_radius=16,
            col={"md": 5, "lg": 3},
            shadow=ft.BoxShadow(blur_radius=10, color="#0D000000"),
        )

        right = ft.Column(
            [
                ft.Container(
                    content=ft.Column(
                        [
                            ft.Row(
                                [
                                    ft.Icon(
                                        ft.Icons.GRID_VIEW_ROUNDED,
                                        color="#2563eb",
                                        size=24,
                                    ),
                                    ft.Text(
                                        "Painel de Visualização dos Jogos",
                                        weight="bold",
                                        color="black",
                                        size=22,
                                    ),
                                ]
                            ),
                            ft.Divider(),
                            ft.Column(
                                [self.numeros_grid],
                                scroll=ft.ScrollMode.AUTO,
                                expand=True,
                            ),
                        ]
                    ),
                    padding=25,
                    bgcolor="white",
                    border_radius=16,
                    expand=True,  # Ocupa o restante do espaço superior
                    shadow=ft.BoxShadow(blur_radius=10, color="#0D000000"),
                ),
                # CONTAINER DO RESUMO FINANCEIRO (Substituindo a aba técnica)
                ft.Container(
                    content=ft.Column(
                        [
                            ft.Row(
                                [
                                    ft.Icon(
                                        ft.Icons.MONETIZATION_ON_OUTLINED,
                                        color="#059669",
                                        size=24,
                                    ),
                                    ft.Text(
                                        "Resumo Financeiro da Aposta",
                                        weight="bold",
                                        color="black",
                                        size=20,
                                    ),
                                ]
                            ),
                            ft.Divider(),
                            self.resumo_content,
                        ]
                    ),
                    padding=25,
                    bgcolor="white",
                    border_radius=16,
                    height=150,  # Tamanho fixo e charmoso no fundo
                    shadow=ft.BoxShadow(blur_radius=10, color="#0D000000"),
                ),
            ],
            spacing=25,
            col={"md": 7, "lg": 9},
            expand=True,
        )  # expand=True garante que ocupe até o final da tela

        page.add(
            ft.Column(
                [
                    header,
                    ft.Container(
                        ft.ResponsiveRow([left, right], spacing=25),
                        padding=25,
                        expand=True,
                    ),
                ],
                expand=True,
            )
        )
        self.atualizar_dezenas(None)
        self.verificar_atualizacao_auto()
