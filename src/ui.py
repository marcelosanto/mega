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
            self.show_snackbar(f"❌ Erro ao carregar dados: {e}", "#ef4444")
            self.app.freq = np.zeros(config["num_total"], dtype=int)

    def _atualizar_frequencia_app(self, df, config):
        numeros_flat = df[config["colunas_numeros"]].values.flatten()
        numeros_flat = numeros_flat[~np.isnan(numeros_flat)].astype(int)
        self.app.freq = np.bincount(numeros_flat, minlength=config["num_total"] + 1)[1:]

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
                return sorted(np.random.choice(range(1, config["num_total"] + 1), size=num_dezenas, replace=False).tolist())
            
            numeros_ordenados = np.argsort(self.app.freq)[::-1] + 1
            if metodo == "top_frequentes":
                top_n = 40 if loteria == "Mega-Sena" else 25
                top = numeros_ordenados[:top_n]
                numeros_selecionados = np.random.choice(top, size=num_dezenas, replace=False)
            elif metodo == "probabilistico":
                probs = self.app.freq / self.app.freq.sum()
                numeros_selecionados = np.random.choice(range(1, config["num_total"] + 1), size=num_dezenas, replace=False, p=probs)
            else:
                raise ValueError("Método inválido.")
            return sorted([int(x) for x in numeros_selecionados])
        except Exception as e:
            self.logger.error(f"Erro ao gerar: {e}")
            return []

    # MÉTODOS DE UI E UTILITÁRIOS
    # ===================================================================

    def show_snackbar(self, message, color="#333333"):
        if self.page:
            self.page.open(ft.SnackBar(content=ft.Text(message, color="white"), bgcolor=color))
            self.page.update()

    def close_dialog(self, e=None):
        if self.page and self.page.dialog:
            self.page.dialog.open = False
            self.page.update()

    def copiar_jogos(self, e):
        if not self.app.jogos_atuais:
            return self.show_snackbar("⚠️ Não há jogos para copiar!", "#f59e0b")
        
        texto = f"--- JOGOS {self.app.loteria.current.value.upper()} ---\n"
        texto += f"Data: {datetime.now().strftime('%d/%m/%Y %H:%M')}\n\n"
        for i, jogo in enumerate(self.app.jogos_atuais, 1):
            texto += f"Jogo {i:02d}: {' - '.join(f'{n:02d}' for n in jogo)}\n"
        
        self.page.set_clipboard(texto)
        self.show_snackbar("📋 Jogos copiados com sucesso!", "#3b82f6")

    def atualizar_dezenas(self, e):
        loteria = self.app.loteria.current.value
        config = self.config_loteria[loteria]
        self.dezenas_slider.min, self.dezenas_slider.max = config["min_dezenas"], config["max_dezenas"]
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
        if self.page: self.page.update()

    def toggle_bolao(self, e):
        self.bolao_container.visible = self.app.is_bolao.current.value
        self.page.update()

    def gerar_jogos(self, e):
        self.gerar_btn.disabled = True
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
            
            for i in range(num_jogos):
                numeros = self.gerar_numeros(metodo, num_dezenas)
                if not numeros: continue
                self.app.jogos_atuais.append(numeros)
                
                self.numeros_grid.controls.append(
                    ft.Container(
                        ft.Column([
                            ft.Text(f"Jogo {i+1}", weight="bold", size=14, color="black"),
                            ft.Row([ft.Container(content=ft.Text(f"{n:02d}", color="white", weight="bold", size=11), bgcolor=config["cor_bola"], width=28, height=28, border_radius=14, alignment=ft.alignment.center) for n in numeros], wrap=True, spacing=4)
                        ], spacing=5),
                        padding=12, border_radius=8, border=ft.border.all(1, "#f1f5f9"), bgcolor="#f8fafc", col={"sm": 12, "md": 6, "lg": 4}
                    )
                )

            total_preco = self.calcular_preco(num_dezenas) * num_jogos
            num_part = int(self.app.num_participantes.current.value) if self.app.is_bolao.current.value else 1
            
            self.resumo_content.controls.append(
                ft.Column([
                    ft.Row([ft.Text("Custo Total:", color="black", weight="w500"), ft.Text(f"R$ {total_preco:.2f}", weight="bold", color="#059669", size=16)]),
                    ft.Row([ft.Text("Por Participante:", color="black", weight="w500"), ft.Text(f"R$ {total_preco/max(num_part,1):.2f}", weight="bold", color="#059669", size=16)])
                ], spacing=10)
            )
            self.salvar_button.disabled = False
            self.copiar_btn.visible = True
        except Exception as ex:
            self.show_snackbar(f"❌ Erro: {ex}", "#ef4444")
        finally:
            self.gerar_btn.disabled = False
            self.page.update()

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
        def start_update(e):
            self.close_dialog(e)
            self.show_snackbar("📥 Baixando... O app reiniciará em breve.", duration=10000)
            threading.Thread(target=lambda: manager.download_and_install(update_info["download_url"])).start()

        dialog = ft.AlertDialog(
            title=ft.Text("Atualização Disponível"),
            content=ft.Text(f"Nova versão {update_info['version']} encontrada."),
            actions=[
                ft.TextButton("Depois", on_click=self.close_dialog),
                ft.ElevatedButton("Atualizar", on_click=start_update, bgcolor="#3b82f6", color="white"),
            ],
        )
        self.page.dialog = dialog
        self.page.open(dialog)

    def mostrar_grafico(self, e):
        if self.df_atual is None: return self.show_snackbar("❌ Carregue os dados primeiro.", "#ef4444")
        loteria = self.app.loteria.current.value
        config = self.config_loteria[loteria]

        def update_plot(n_concursos):
            df_filtro = self.df_atual.head(n_concursos) if n_concursos > 0 else self.df_atual
            nums = df_filtro[config["colunas_numeros"]].values.flatten()
            nums = nums[~np.isnan(nums)].astype(int)
            freq_f = np.bincount(nums, minlength=config["num_total"] + 1)[1:]

            fig, ax = plt.subplots(figsize=(10, 5))
            ax.bar(range(1, config["num_total"] + 1), freq_f, color="#cbd5e1", label="Histórico")

            if self.app.jogos_atuais:
                nums_bolao = [n for j in self.app.jogos_atuais for n in j]
                freq_b = np.bincount(nums_bolao, minlength=config["num_total"] + 1)[1:]
                idx = [i for i, v in enumerate(freq_b) if v > 0]
                ax.bar([i+1 for i in idx], [freq_f[i] for i in idx], color=config["cor_bola"], label="Sua Cobertura")
            
            ax.set_title(f"Análise de Tendência ({n_concursos if n_concursos > 0 else 'Total'})")
            ax.legend()
            chart_container.content = MatplotlibChart(fig, expand=True)
            self.page.update()

        chart_container = ft.Container(height=400)
        filter_slider = ft.Slider(min=0, max=200, divisions=20, label="{value} concursos", on_change=lambda e: update_plot(int(e.control.value)))
        
        dialog = ft.AlertDialog(
            title=ft.Text("📊 Inteligência de Tendências"),
            content=ft.Column([ft.Text("Filtrar últimos concursos (0 = Histórico Completo):", color="black"), filter_slider, chart_container], height=500, width=800, spacing=15),
            actions=[ft.TextButton("Fechar", on_click=self.close_dialog)]
        )
        self.page.dialog = dialog
        self.page.open(dialog)
        update_plot(0)

    def abrir_historico(self, e):
        try:
            jogos = self.app.db_manager.carregar_historico()
            if not jogos: return self.show_snackbar("ℹ️ Histórico vazio.")
            rows = [ft.DataRow(cells=[ft.DataCell(ft.Text(str(j[0]), color="black")), ft.DataCell(ft.Text(j[1], color="black")), ft.DataCell(ft.Text(f"R$ {j[5]:.2f}", color="black")), ft.DataCell(ft.Text(j[9][:10], color="black"))]) for j in jogos]
            dialog = ft.AlertDialog(title=ft.Text("Histórico de Jogos"), content=ft.DataTable(columns=[ft.DataColumn(ft.Text(c, color="black", weight="bold")) for c in ["ID", "Loteria", "Preço", "Data"]], rows=rows), actions=[ft.TextButton("Fechar", on_click=self.close_dialog)])
            self.page.dialog = dialog
            self.page.open(dialog)
        except: self.show_snackbar("❌ Erro ao ler histórico")

    def build_info_cards(self, config):
        return [
            ft.Container(content=ft.Column([
                ft.Row([ft.Icon(ft.Icons.SETTINGS, size=20, color="black"), ft.Text("Configuração da Loteria", weight="bold", color="black")]),
                ft.Text(f"• Dezenas Sorteados: {config['num_sorteados']}", color="black"),
                ft.Text(f"• Preço por Aposta: R$ {config['preco_base']:.2f}", color="black"),
            ], spacing=8)),
            ft.Container(content=ft.Column([
                ft.Row([ft.Icon(ft.Icons.LIGHTBULB_ROUNDED, size=20, color="#f59e0b"), ft.Text("Dica de Estratégia", weight="bold", color="black")]),
                ft.Text("Utilize o slider no gráfico para focar em números que saíram recentemente.", color="black"),
            ], spacing=8))
        ]

    # MÉTODO PRINCIPAL
    # ===================================================================
    def main(self, page: ft.Page):
        self.page = page
        page.title = "Loterias Pro - Inteligência Estatística"
        page.window_state = "maximized" 
        page.theme = ft.Theme(color_scheme_seed="#3b82f6")

        self.app.loteria, self.app.num_dezenas, self.app.metodo = ft.Ref[ft.Dropdown](), ft.Ref[ft.Slider](), ft.Ref[ft.Dropdown]()
        self.app.is_bolao, self.app.num_jogos, self.app.num_participantes = ft.Ref[ft.Checkbox](), ft.Ref[ft.TextField](), ft.Ref[ft.TextField]()

        self.dezenas_slider = ft.Slider(ref=self.app.num_dezenas, min=6, max=20, value=6, on_change=self.atualizar_label_dezenas)
        self.dezenas_info = ft.Text("R$ 5.00", color="#059669", weight="bold", size=16)
        self.numeros_grid = ft.ResponsiveRow(spacing=15, run_spacing=15)
        
        self.info_content, self.dicas_content, self.resumo_content = ft.Column(spacing=10), ft.Column(spacing=10), ft.Column(spacing=10)
        self.gerar_btn = ft.ElevatedButton("🎲 Gerar Números", bgcolor="#3b82f6", color="white", expand=True, height=45, on_click=self.gerar_jogos)
        self.salvar_button = ft.ElevatedButton("💾 Salvar no Banco", bgcolor="#10b981", color="white", expand=True, height=45, disabled=True, on_click=lambda _: self.app.db_manager.salvar_no_banco(self.app, ""))
        self.copiar_btn = ft.IconButton(icon=ft.Icons.COPY_ALL_ROUNDED, on_click=self.copiar_jogos, visible=False, tooltip="Copiar Jogos")

        self.bolao_container = ft.Row([
            ft.TextField(ref=self.app.num_jogos, label="Nº de Jogos", value="1", expand=True, color="black", border_color="#cbd5e1"),
            ft.TextField(ref=self.app.num_participantes, label="Nº de Pessoas", value="1", expand=True, color="black", border_color="#cbd5e1"),
        ], visible=False)

        header = ft.Container(
            content=ft.Row([
                ft.Row([ft.Icon(ft.Icons.AUTO_GRAPH, color="#3b82f6"), ft.Text("Loterias Inteligentes", size=22, weight="bold", color="black")]),
                ft.Row([
                    self.copiar_btn, 
                    ft.IconButton(ft.Icons.BAR_CHART_ROUNDED, on_click=self.mostrar_grafico, tooltip="Ver Estatísticas", icon_color="black"), 
                    ft.IconButton(ft.Icons.HISTORY_ROUNDED, on_click=self.abrir_historico, tooltip="Ver Histórico", icon_color="black"),
                    ft.IconButton(ft.Icons.UPDATE_ROUNDED, on_click=self.on_check_updates_click, tooltip="Verificar Versão", icon_color="black")
                ], spacing=10)
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
            padding=15, bgcolor="white", border=ft.border.only(bottom=ft.BorderSide(1, "#f1f5f9"))
        )

        left_panel = ft.Container(
            content=ft.Column([
                ft.Dropdown(ref=self.app.loteria, label="Escolha a Loteria", options=[ft.dropdown.Option("Mega-Sena"), ft.dropdown.Option("Loto Fácil")], value="Mega-Sena", on_change=self.atualizar_dezenas, color="black"),
                ft.Dropdown(ref=self.app.metodo, label="Método Estatístico", options=[ft.dropdown.Option("Top Frequentes"), ft.dropdown.Option("Probabilistico")], value="Top Frequentes", color="black"),
                ft.Row([ft.Text("Custo por Jogo:", color="black", weight="bold"), self.dezenas_info], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                self.dezenas_slider,
                ft.Checkbox(ref=self.app.is_bolao, label="Ativar Modo Bolão", on_change=self.toggle_bolao, label_style=ft.TextStyle(color="black", weight="bold")),
                self.bolao_container,
                ft.Row([self.gerar_btn, self.salvar_button], spacing=10),
            ], spacing=20),
            padding=20, bgcolor="white", border_radius=12, col={"xs": 12, "md": 4, "lg": 3}, border=ft.border.all(1, "#f1f5f9")
        )

        tabs_detalhes = ft.Tabs(
            selected_index=0,
            tabs=[
                ft.Tab(text="Informações", icon=ft.Icons.INFO_OUTLINE, content=ft.Container(self.info_content, padding=20)),
                ft.Tab(text="Dicas de Uso", icon=ft.Icons.LIGHTBULB_OUTLINE, content=ft.Container(self.dicas_content, padding=20)),
                ft.Tab(text="Resumo Financeiro", icon=ft.Icons.MONETIZATION_ON_OUTLINED, content=ft.Container(self.resumo_content, padding=20)),
            ], expand=True
        )

        right_panel = ft.Column([
            ft.Container(
                content=ft.Column([
                    ft.Row([ft.Icon(ft.Icons.GRID_VIEW_ROUNDED, color="black"), ft.Text("Painel de Jogos Gerados", weight="bold", color="black", size=16)]),
                    ft.Column([self.numeros_grid], scroll=ft.ScrollMode.AUTO, expand=True)
                ]),
                padding=20, bgcolor="white", border_radius=12, height=450, border=ft.border.all(1, "#f1f5f9")
            ),
            ft.Container(content=tabs_detalhes, bgcolor="white", border_radius=12, expand=True, border=ft.border.all(1, "#f1f5f9"))
        ], spacing=20, col={"xs": 12, "md": 8, "lg": 9}, expand=True)

        page.add(ft.Column([header, ft.Container(ft.ResponsiveRow([left_panel, right_panel], spacing=20), padding=20, expand=True)], expand=True))
        self.atualizar_dezenas(None)