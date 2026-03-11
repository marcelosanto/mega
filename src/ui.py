import os
import logging
from datetime import datetime
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
        self.page.update()

    def close_dialog(self, e=None):
        if self.page and self.page.dialog:
            self.page.dialog.open = False
            self.page.update()

    def copiar_jogos(self, e):
        if not self.app.jogos_atuais:
            self.show_snackbar("⚠️ Não há jogos para copiar!", "#f59e0b")
            return
        
        texto_copia = f"--- JOGOS GERADOS: {self.app.loteria.current.value} ---\n"
        texto_copia += f"Data: {datetime.now().strftime('%d/%m/%Y %H:%M')}\n\n"
        for i, jogo in enumerate(self.app.jogos_atuais, 1):
            texto_copia += f"Jogo {i:02d}: {' - '.join(f'{n:02d}' for n in jogo)}\n"
        
        self.page.set_clipboard(texto_copia)
        self.show_snackbar("📋 Jogos copiados! Pronto para colar e imprimir.", "#3b82f6")

    def atualizar_dezenas(self, e):
        loteria = self.app.loteria.current.value
        config = self.config_loteria[loteria]
        self.dezenas_slider.min = config["min_dezenas"]
        self.dezenas_slider.max = config["max_dezenas"]
        self.dezenas_slider.value = config["min_dezenas"]
        self.atualizar_label_dezenas()
        
        self.info_content.controls.clear()
        self.dicas_content.controls.clear()
        cards = self.build_info_cards(config)
        self.info_content.controls.append(cards[0])
        self.dicas_content.controls.append(cards[1])
        
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
        
        self.numeros_grid.controls.clear()
        self.resumo_content.controls.clear()
        self.app.jogos_atuais = []
        
        try:
            num_jogos = int(self.app.num_jogos.current.value) if self.app.is_bolao.current.value else 1
            num_dezenas = int(self.app.num_dezenas.current.value)
            metodo = self.app.metodo.current.value.lower().replace(" ", "_")
            loteria = self.app.loteria.current.value
            config = self.config_loteria[loteria]
            total_preco = 0
            
            for i in range(num_jogos):
                numeros = self.gerar_numeros(metodo, num_dezenas)
                if not numeros: continue
                self.app.jogos_atuais.append(numeros)
                
                bola_row = ft.Row(
                    [
                        ft.Container(
                            content=ft.Text(f"{num:02d}", color="white", weight="bold", size=12),
                            bgcolor=config["cor_bola"],
                            width=30, height=30,
                            border_radius=15,
                            alignment=ft.alignment.center,
                        )
                        for num in numeros
                    ],
                    wrap=True,
                    spacing=5,
                )
                
                # GRID RESPONSIVO: 1 coluna em mobile, 2 em tablet, 3 em desktop
                self.numeros_grid.controls.append(
                    ft.Container(
                        ft.Column([
                            ft.Text(f"Jogo {i+1}", weight="bold", size=13, color="#475569"),
                            bola_row,
                        ], spacing=8),
                        padding=12,
                        border_radius=8,
                        border=ft.border.all(1, "#f1f5f9"),
                        bgcolor="#f8fafc",
                        col={"sm": 12, "md": 6, "lg": 4},
                    )
                )
                total_preco += self.calcular_preco(num_dezenas)

            num_participantes = int(self.app.num_participantes.current.value) if self.app.is_bolao.current.value else 1
            preco_por_participante = total_preco / max(num_participantes, 1)

            self.resumo_content.controls.append(
                ft.Column([
                    ft.Row([ft.Text("Custo Total:"), ft.Text(f"R$ {total_preco:.2f}", weight="bold", size=16, color="#059669")]),
                    ft.Row([ft.Text("Participantes:"), ft.Text(f"{num_participantes}", weight="bold")]),
                    ft.Row([ft.Text("Por Participante:"), ft.Text(f"R$ {preco_por_participante:.2f}", weight="bold", size=16, color="#059669")]),
                ])
            )
            
            self.salvar_button.disabled = False
            self.copiar_btn.visible = True
            self.show_snackbar("🎲 Jogos gerados!", color="#10b981")
            
        except Exception as ex:
            self.show_snackbar(f"❌ Erro: {ex}", "#ef4444")
        finally:
            self.gerar_btn.disabled = False
            self.gerar_btn.text = "🎲 Gerar Números"
            self.page.update()

    def mostrar_grafico(self, e):
        loteria = self.app.loteria.current.value
        config = self.config_loteria[loteria]
        if len(self.app.freq) == 0:
            return self.show_snackbar("❌ Carregue os dados primeiro.", "#ef4444")

        fig, ax = plt.subplots(figsize=(8, 4))
        ax.bar(range(1, config["num_total"] + 1), self.app.freq, color=config["cor_bola"])
        ax.set_title(f"Frequência de Dezenas - {loteria}")
        chart = MatplotlibChart(fig, expand=True)

        dialog = ft.AlertDialog(
            title=ft.Text("Análise de Frequência"),
            content=ft.Container(chart, height=400),
            actions=[ft.TextButton("Fechar", on_click=self.close_dialog)],
        )
        self.page.dialog = dialog
        self.page.open(dialog)

    def abrir_historico(self, e):
        try:
            jogos = self.app.db_manager.carregar_historico()
            if not jogos: return self.show_snackbar("ℹ️ Histórico vazio.", "#3b82f6")

            rows = [
                ft.DataRow(cells=[
                    ft.DataCell(ft.Text(str(j[0]))), ft.DataCell(ft.Text(j[1])),
                    ft.DataCell(ft.Text(j[2])), ft.DataCell(ft.Text(f"R$ {j[5]:.2f}")),
                    ft.DataCell(ft.Text(j[9][:10])),
                ]) for j in jogos
            ]

            dialog = ft.AlertDialog(
                title=ft.Text("Histórico de Jogos"),
                content=ft.DataTable(
                    columns=[ft.DataColumn(ft.Text(c)) for c in ["ID", "Loteria", "Método", "Preço", "Data"]],
                    rows=rows,
                ),
                actions=[ft.TextButton("Fechar", on_click=self.close_dialog)],
            )
            self.page.dialog = dialog
            self.page.open(dialog)
        except Exception as ex:
            self.show_snackbar(f"❌ Erro ao ler histórico: {ex}", "#ef4444")

    def on_check_updates_click(self, e):
        self.show_snackbar("🔎 Verificando atualizações...", color="#3b82f6")
        threading.Thread(target=self._check_updates_worker).start()

    def _check_updates_worker(self):
        manager = UpdateManager(current_version=VERSION, repo_url=UPDATE_BASE_URL)
        result = manager.check_for_updates()
        if result.get("update_available"):
            self.show_update_dialog(result, manager)
        else:
            self.show_snackbar("✅ Versão mais recente instalada.", "#10b981")

    def show_update_dialog(self, update_info, manager):
        dialog = ft.AlertDialog(
            title=ft.Text("Nova Versão"),
            content=ft.Text(f"Versão {update_info['version']} disponível."),
            actions=[ft.TextButton("Depois", on_click=self.close_dialog), ft.ElevatedButton("Atualizar")],
        )
        self.page.dialog = dialog
        self.page.open(dialog)

    def build_info_cards(self, config):
        return [
            ft.Container(content=ft.Column([
                ft.Row([ft.Icon(ft.Icons.SETTINGS, size=20), ft.Text("Configuração", weight="bold")]),
                ft.Text(f"Sorteados: {config['num_sorteados']}"),
                ft.Text(f"Preço Unitário: R$ {config['preco_base']:.2f}"),
            ], spacing=5)),
            ft.Container(content=ft.Column([
                ft.Row([ft.Icon(ft.Icons.LIGHTBULB, size=20, color="orange"), ft.Text("Sugestão", weight="bold")]),
                ft.Text("O método Probabilístico usa estatística real do arquivo XLSX."),
            ], spacing=5))
        ]

    # MÉTODO PRINCIPAL
    # ===================================================================
    def main(self, page: ft.Page):
        self.page = page
        page.title = "Loteria Gerador Pro"
        page.theme_mode = ft.ThemeMode.LIGHT
        
        # CORREÇÃO PARA O ERRO: Iniciar Maximizado
        page.window_state = "maximized" 
        
        page.theme = ft.Theme(color_scheme_seed="#3b82f6", use_material3=True)

        # Referências de App
        self.app.loteria = ft.Ref[ft.Dropdown]()
        self.app.num_dezenas = ft.Ref[ft.Slider]()
        self.app.metodo = ft.Ref[ft.Dropdown]()
        self.app.is_bolao = ft.Ref[ft.Checkbox]()
        self.app.num_jogos = ft.Ref[ft.TextField]()
        self.app.num_participantes = ft.Ref[ft.TextField]()

        self.dezenas_slider = ft.Slider(ref=self.app.num_dezenas, min=6, max=20, value=6, on_change=self.atualizar_label_dezenas)
        self.dezenas_info = ft.Text("R$ 5.00", color="#059669", weight="bold")
        
        # Grid de Jogos (Responsivo)
        self.numeros_grid = ft.ResponsiveRow(spacing=10, run_spacing=10)
        
        self.info_content = ft.Column()
        self.dicas_content = ft.Column()
        self.resumo_content = ft.Column()
        
        self.gerar_btn = ft.ElevatedButton("🎲 Gerar Números", bgcolor="#3b82f6", color="white", height=45, expand=True, on_click=self.gerar_jogos)
        self.salvar_button = ft.ElevatedButton("💾 Salvar", bgcolor="#10b981", color="white", height=45, expand=True, disabled=True, on_click=lambda _: self.app.db_manager.salvar_no_banco(self.app, ""))
        
        self.copiar_btn = ft.IconButton(icon=ft.Icons.COPY_ALL_ROUNDED, tooltip="Copiar Jogos", on_click=self.copiar_jogos, visible=False)

        self.bolao_container = ft.Row([
            ft.TextField(ref=self.app.num_jogos, label="Nº Jogos", value="1", expand=True, keyboard_type=ft.KeyboardType.NUMBER),
            ft.TextField(ref=self.app.num_participantes, label="Participantes", value="1", expand=True, keyboard_type=ft.KeyboardType.NUMBER),
        ], visible=False)

        header = ft.Container(
            content=ft.Row([
                ft.Row([ft.Icon(ft.Icons.CASINO), ft.Text("Loterias Pro", size=22, weight="bold")]),
                ft.Row([
                    self.copiar_btn,
                    ft.IconButton(ft.Icons.PRINT_ROUNDED, tooltip="Imprimir (Copia p/ área de transf.)", on_click=self.copiar_jogos),
                    ft.IconButton(ft.Icons.BAR_CHART, on_click=self.mostrar_grafico, tooltip="Gráfico"),
                    ft.IconButton(ft.Icons.HISTORY, on_click=self.abrir_historico, tooltip="Histórico"),
                    ft.IconButton(ft.Icons.UPDATE, on_click=self.on_check_updates_click, tooltip="Atualizar"),
                ])
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
            padding=15, bgcolor="white", border=ft.border.only(bottom=ft.BorderSide(1, "#f1f5f9"))
        )

        left_panel = ft.Container(
            content=ft.Column([
                ft.Dropdown(ref=self.app.loteria, label="Selecione a Loteria", options=[ft.dropdown.Option("Mega-Sena"), ft.dropdown.Option("Loto Fácil")], value="Mega-Sena", on_change=self.atualizar_dezenas),
                ft.Dropdown(ref=self.app.metodo, label="Método de Geração", options=[ft.dropdown.Option("Top Frequentes"), ft.dropdown.Option("Probabilistico")], value="Top Frequentes"),
                ft.Row([ft.Text("Dezenas:"), self.dezenas_info], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                self.dezenas_slider,
                ft.Checkbox(ref=self.app.is_bolao, label="Ativar modo Bolão", on_change=self.toggle_bolao),
                self.bolao_container,
                ft.Row([self.gerar_btn, self.salvar_button], spacing=10),
            ], spacing=20),
            padding=20, bgcolor="white", border_radius=12, col={"xs": 12, "md": 4, "lg": 3}, border=ft.border.all(1, "#f1f5f9")
        )

        tabs_detalhes = ft.Tabs(
            selected_index=0,
            tabs=[
                ft.Tab(text="Informações", icon=ft.Icons.INFO_OUTLINE, content=ft.Container(self.info_content, padding=15)),
                ft.Tab(text="Dicas", icon=ft.Icons.LIGHTBULB_OUTLINE, content=ft.Container(self.dicas_content, padding=15)),
                ft.Tab(text="Resumo Financeiro", icon=ft.Icons.ATTACH_MONEY, content=ft.Container(self.resumo_content, padding=15)),
            ], expand=True
        )

        right_panel = ft.Column([
            # TOPO: NÚMEROS GERADOS COM GRID RESPONSIVO
            ft.Container(
                content=ft.Column([
                    ft.Row([
                        ft.Icon(ft.Icons.GRID_VIEW_ROUNDED, size=20), 
                        ft.Text("Painel de Jogos Gerados", weight="bold")
                    ]),
                    # CORREÇÃO AQUI: Usamos Column com scroll para envolver o grid
                    ft.Column(
                        [self.numeros_grid], 
                        scroll=ft.ScrollMode.AUTO, 
                        expand=True
                    )
                ]),
                padding=20, 
                bgcolor="white", 
                border_radius=12, 
                height=450, 
                border=ft.border.all(1, "#f1f5f9")
            ),
            # BASE: ABAS
            ft.Container(
                content=tabs_detalhes, 
                bgcolor="white", 
                border_radius=12, 
                expand=True, 
                border=ft.border.all(1, "#f1f5f9")
            )
        ], spacing=20, col={"xs": 12, "md": 8, "lg": 9}, expand=True)

        page.add(
            ft.Column([
                header, 
                ft.Container(ft.ResponsiveRow([left_panel, right_panel], spacing=20), padding=20, expand=True)
            ], expand=True)
        )
        self.atualizar_dezenas(None)