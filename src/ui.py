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
        # Captura os números do Sorteio Principal
        nums = df[config["colunas_numeros"]].values.flatten()

        # Se for Dupla Sena, combina estatísticas do Sorteio 1 e Sorteio 2
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
                # CORREÇÃO PARA A LOTO MANIA E DEMAIS JOGOS
                if loteria == "Loto Mania":
                    limite = 75  # Tem que ser maior que 50 para poder gerar
                elif loteria in ["Mega-Sena", "Quina", "Dupla Sena"]:
                    limite = 40
                else:
                    limite = 20  # Loto Fácil

                # Garante que o limite seja sempre maior que a qtde de dezenas pedidas
                limite = max(limite, num_dezenas + 5)

                top = numeros_ordenados[:limite]
                selecionados = np.random.choice(top, size=num_dezenas, replace=False)
            else:
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
        self.show_snackbar("📋 Copiado!", "#3b82f6")

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
            self.show_snackbar("✅ Salvo!", "#10b981")
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

        self.info_content.controls.clear()
        self.info_content.controls.append(
            ft.Column(
                [
                    ft.Text(
                        f"Loteria: {loteria}", color="black", weight="bold", size=18
                    ),
                    ft.Text(
                        f"• Preço Base: R$ {config['preco_base']:.2f}",
                        color="black",
                        size=16,
                    ),
                    ft.Text(
                        f"• Dezenas Sorteadas: {config['num_sorteados']}",
                        color="black",
                        size=16,
                    ),
                ],
                spacing=8,
            )
        )
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
                                        ft.IconButton(
                                            ft.Icons.SAVE,
                                            icon_color="#10b981",
                                            on_click=lambda _, n=nums: self.salvar_jogo_individual(
                                                n
                                            ),
                                            tooltip="Salvar Jogo",
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
            self.resumo_content.controls.append(
                ft.Column(
                    [
                        ft.Text(
                            f"Custo Total: R$ {custo:.2f}",
                            color="black",
                            weight="bold",
                            size=18,
                        ),
                        ft.Text(
                            f"Custo por Pessoa: R$ {custo/part:.2f}",
                            color="#059669",
                            weight="bold",
                            size=20,
                        ),
                        ft.Divider(),
                        ft.ElevatedButton(
                            "📊 Exportar Resumo para Excel",
                            icon=ft.Icons.FILE_DOWNLOAD,
                            on_click=self.exportar_excel,
                            bgcolor="#1e7145",
                            color="white",
                            height=50,
                        ),
                    ],
                    spacing=10,
                )
            )
            self.copiar_btn.visible = True
        finally:
            self.gerar_btn.disabled = False
            self.page.update()

    # CORREÇÃO DEFINITIVA NO MANEJO DOS DIÁLOGOS NO FLET NOVO
    # ===================================================================
    def abrir_historico(self, e):
        try:
            jogos = self.app.db_manager.carregar_historico()
            stats = self.app.db_manager.get_estatisticas()
            lista = ft.Column(spacing=12, scroll=ft.ScrollMode.AUTO, expand=True)

            dlg = ft.AlertDialog(
                title=ft.Text("Meu Histórico", size=20, weight="bold", color="black"),
                content=ft.Container(
                    content=ft.Column(
                        [
                            ft.Row(
                                [
                                    ft.Text(
                                        f"Total Gasto: R$ {stats.get('total_gasto', 0):.2f}",
                                        weight="bold",
                                        color="#059669",
                                        size=18,
                                    )
                                ],
                                alignment="center",
                            ),
                            ft.Divider(),
                            lista,
                        ]
                    ),
                    width=550,
                    height=600,
                ),
            )
            # Para o flet novo: lambda do fechar precisa de referencia da instancia do dialógo
            dlg.actions = [
                ft.TextButton("Fechar", on_click=lambda e: self.page.close(dlg))
            ]

            for j in jogos:
                # O banco devolve a string [1, 2, 3] num array encadeado ou direto. Resolvemos:
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
                                                    ft.Icons.DELETE,
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
                        bgcolor="white",
                        border=ft.border.all(1, "#e2e8f0"),
                    )
                )
            self.page.open(dlg)
        except Exception as ex:
            self.show_snackbar(f"Erro ao abrir histórico: {ex}", "#ef4444")

    def mostrar_grafico(self, e):
        if self.df_atual is None:
            return
        config = self.config_loteria[self.app.loteria.current.value]

        def up_plot(n):
            df_f = self.df_atual.head(n) if n > 0 else self.df_atual
            nums = df_f[config["colunas_numeros"]].values.flatten()
            if "colunas_numeros_2" in config:
                nums2 = df_f[config["colunas_numeros_2"]].values.flatten()
                nums = np.concatenate([nums, nums2])
            nums = nums[~np.isnan(nums)].astype(int)
            freq = np.bincount(nums, minlength=config["num_total"] + 1)[1:]

            fig, ax = plt.subplots(figsize=(10, 5))
            ax.bar(range(1, config["num_total"] + 1), freq, color="#cbd5e1")

            if self.app.jogos_atuais:
                curr = [n for j in self.app.jogos_atuais for n in j]
                f_curr = np.bincount(curr, minlength=config["num_total"] + 1)[1:]
                idx = [i for i, v in enumerate(f_curr) if v > 0]
                ax.bar(
                    [i + 1 for i in idx],
                    [freq[i] for i in idx],
                    color=config["cor_bola"],
                )
            ax.set_title(
                f"Frequência - {self.app.loteria.current.value}", color="black"
            )
            chart_box.content = MatplotlibChart(fig, expand=True)
            self.page.update()

        chart_box = ft.Container(height=400)
        dlg = ft.AlertDialog(
            title=ft.Text("Análise Estatística", color="black", weight="bold"),
            content=ft.Column(
                [
                    ft.Text("Filtro dos últimos concursos:", color="black", size=14),
                    ft.Slider(
                        min=0,
                        max=200,
                        divisions=20,
                        label="{value} concursos",
                        on_change=lambda e: up_plot(int(e.control.value)),
                    ),
                    chart_box,
                ],
                width=850,
                height=500,
            ),
        )
        dlg.actions = [ft.TextButton("Fechar", on_click=lambda e: self.page.close(dlg))]
        self.page.open(dlg)
        up_plot(0)

    def verificar_atualizacao_auto(self):
        threading.Thread(target=self._check_updates_worker, daemon=True).start()

    def _check_updates_worker(self):
        try:
            res = self.app.update_manager.check_for_updates()
            if res.get("update_available"):
                dlg = ft.AlertDialog(
                    title=ft.Text(
                        "Novo Update Disponível", color="black", weight="bold"
                    ),
                    content=ft.Text(
                        f"A versão {res['version']} está pronta para instalar.",
                        color="black",
                    ),
                )
                dlg.actions = [
                    ft.TextButton("Depois", on_click=lambda e: self.page.close(dlg)),
                    ft.ElevatedButton(
                        "Instalar",
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
        self.info_content, self.resumo_content = ft.Column(), ft.Column()

        lbl_style = ft.TextStyle(color="black", weight="bold", size=16)

        self.gerar_btn = ft.ElevatedButton(
            "🎲 Gerar", bgcolor="#2563eb", color="white", expand=True, height=50
        )
        self.gerar_btn.on_click = self.gerar_jogos

        self.limpar_btn = ft.ElevatedButton(
            "🧹 Limpar", bgcolor="#cbd5e1", color="black", expand=True, height=50
        )
        self.limpar_btn.on_click = lambda _: (
            self.numeros_grid.controls.clear(),
            page.update(),
        )

        self.copiar_btn = ft.IconButton(
            icon=ft.Icons.COPY,
            on_click=self.copiar_jogos,
            visible=False,
            icon_color="black",
        )

        header = ft.Container(
            content=ft.Row(
                [
                    ft.Row(
                        [
                            ft.Icon(ft.Icons.CASINO_OUTLINED, color="#2563eb", size=30),
                            ft.Text(
                                "Loterias Pro", size=26, weight="bold", color="black"
                            ),
                        ]
                    ),
                    ft.Row(
                        [
                            self.copiar_btn,
                            ft.IconButton(
                                ft.Icons.BAR_CHART,
                                on_click=self.mostrar_grafico,
                                icon_color="black",
                                tooltip="Gráficos",
                            ),
                            ft.IconButton(
                                ft.Icons.HISTORY,
                                on_click=self.abrir_historico,
                                icon_color="black",
                                tooltip="Histórico",
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
                    label="Jogos",
                    value="1",
                    expand=True,
                    color="black",
                    label_style=lbl_style,
                ),
                ft.TextField(
                    ref=self.app.num_participantes,
                    label="Pessoas",
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
                        "Configuração da Aposta", size=20, weight="bold", color="black"
                    ),
                    ft.Divider(),
                    ft.Dropdown(
                        ref=self.app.loteria,
                        label="Loteria",
                        label_style=lbl_style,
                        options=[
                            ft.dropdown.Option(k) for k in self.config_loteria.keys()
                        ],
                        value="Mega-Sena",
                        on_change=self.atualizar_dezenas,
                        color="black",
                    ),
                    ft.Dropdown(
                        ref=self.app.metodo,
                        label="Método Estatístico",
                        label_style=lbl_style,
                        options=[
                            ft.dropdown.Option("Top Frequentes"),
                            ft.dropdown.Option("Probabilistico"),
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
                        label="Ativar Modo Bolão",
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
                                        "Painel de Jogos Gerados",
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
                    height=500,
                    shadow=ft.BoxShadow(blur_radius=10, color="#0D000000"),
                ),
                ft.Container(
                    content=ft.Tabs(
                        tabs=[
                            ft.Tab(
                                text="Resumo Financeiro",
                                icon=ft.Icons.MONETIZATION_ON_OUTLINED,
                                content=ft.Container(self.resumo_content, padding=25),
                            ),
                            ft.Tab(
                                text="Informações da Loteria",
                                icon=ft.Icons.INFO_OUTLINE,
                                content=ft.Container(self.info_content, padding=25),
                            ),
                        ],
                        label_color="#2563eb",
                        unselected_label_color="#64748b",
                    ),
                    bgcolor="white",
                    border_radius=16,
                    expand=True,
                    shadow=ft.BoxShadow(blur_radius=10, color="#0D000000"),
                ),
            ],
            spacing=25,
            col={"md": 7, "lg": 9},
        )

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
