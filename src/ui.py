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
                top = numeros_ordenados[:40 if loteria == "Mega-Sena" else 25]
                numeros_selecionados = np.random.choice(top, size=num_dezenas, replace=False)
            elif metodo == "probabilistico":
                probs = self.app.freq / self.app.freq.sum()
                numeros_selecionados = np.random.choice(range(1, config["num_total"] + 1), size=num_dezenas, replace=False, p=probs)
            return sorted([int(x) for x in numeros_selecionados])
        except: return []

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

    def toggle_bolao(self, e):
        self.bolao_container.visible = self.app.is_bolao.current.value
        self.page.update()

    def copiar_jogos(self, e):
        if not self.app.jogos_atuais: return
        texto = f"--- JOGOS {self.app.loteria.current.value.upper()} ---\n"
        for i, jogo in enumerate(self.app.jogos_atuais, 1):
            texto += f"Jogo {i:02d}: {' - '.join(f'{n:02d}' for n in jogo)}\n"
        self.page.set_clipboard(texto)
        self.show_snackbar("📋 Copiado!", "#3b82f6")

    def exportar_excel(self, e):
        """Exporta o resumo dos jogos atuais para um arquivo Excel."""
        if not self.app.jogos_atuais:
            return self.show_snackbar("⚠️ Gere jogos antes de exportar!", "#f59e0b")
        
        try:
            filename = f"Bolao_{self.app.loteria.current.value}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
            df_export = pd.DataFrame(self.app.jogos_atuais)
            df_export.index = [f"Jogo {i+1}" for i in range(len(df_export))]
            df_export.to_excel(filename)
            self.show_snackbar(f"✅ Exportado: {filename}", "#10b981")
        except Exception as ex:
            self.show_snackbar(f"❌ Erro ao exportar: {ex}", "#ef4444")

    def salvar_jogo_individual(self, numeros):
        try:
            backup_jogos = self.app.jogos_atuais
            self.app.jogos_atuais = [numeros]
            if self.app.db_manager.salvar_no_banco(self.app, "Manual"):
                self.show_snackbar("✅ Jogo salvo!", "#10b981")
            self.app.jogos_atuais = backup_jogos
        except: self.show_snackbar("❌ Erro ao salvar", "#ef4444")

    def atualizar_dezenas(self, e):
        loteria = self.app.loteria.current.value
        config = self.config_loteria[loteria]
        self.dezenas_slider.min, self.dezenas_slider.max = config["min_dezenas"], config["max_dezenas"]
        self.dezenas_slider.value = config["min_dezenas"]
        
        self.info_content.controls.clear()
        self.info_content.controls.append(
            ft.Column([
                ft.Text(f"Configuração: {loteria}", weight="bold", color="black", size=16),
                ft.Text(f"• Dezenas totais: {config['num_total']}", color="black"),
                ft.Text(f"• Sorteio: {config['num_sorteados']} números", color="black"),
                ft.Text(f"• Preço unitário: R$ {config['preco_base']:.2f}", color="black", weight="bold"),
            ], spacing=10)
        )
        self.atualizar_label_dezenas()
        self.carregar_dados()
        self.page.update()

    def atualizar_label_dezenas(self, e=None):
        preco = self.calcular_preco(int(self.app.num_dezenas.current.value))
        self.dezenas_info.value = f"R$ {preco:.2f}"
        if self.page: self.page.update()

    def gerar_jogos(self, e):
        self.gerar_btn.disabled = True
        self.page.update()
        self.numeros_grid.controls.clear()
        self.resumo_content.controls.clear()
        self.app.jogos_atuais = []
        try:
            num_jogos = int(self.app.num_jogos.current.value) if self.app.is_bolao.current.value else 1
            num_dezenas = int(self.app.num_dezenas.current.value)
            loteria = self.app.loteria.current.value
            config = self.config_loteria[loteria]
            
            for i in range(num_jogos):
                numeros = self.gerar_numeros(self.app.metodo.current.value.lower().replace(" ", "_"), num_dezenas)
                if not numeros: continue
                self.app.jogos_atuais.append(numeros)
                self.numeros_grid.controls.append(
                    ft.Container(
                        ft.Column([
                            ft.Row([ft.Text(f"Jogo {i+1}", weight="bold", color="black"),
                                    ft.IconButton(ft.Icons.SAVE_AS_ROUNDED, icon_color="#10b981", on_click=lambda _, n=numeros: self.salvar_jogo_individual(n))], alignment="spaceBetween"),
                            ft.Row([ft.Container(content=ft.Text(f"{n:02d}", color="white", weight="bold"), bgcolor=config["cor_bola"], width=28, height=28, border_radius=14, alignment=ft.alignment.center) for n in numeros], wrap=True)
                        ]), padding=12, border_radius=8, bgcolor="#f8fafc", col={"sm": 12, "md": 6, "lg": 4}
                    )
                )
            
            custo_total = self.calcular_preco(num_dezenas) * num_jogos
            num_pessoas = int(self.app.num_participantes.current.value) if self.app.is_bolao.current.value else 1
            
            self.resumo_content.controls.append(
                ft.Column([
                    ft.Text("Resumo Financeiro", weight="bold", color="black", size=16),
                    ft.Divider(),
                    ft.Row([ft.Text("Total:", color="black"), ft.Text(f"R$ {custo_total:.2f}", weight="bold", color="#059669")]),
                    ft.Row([ft.Text("Por Pessoa:", color="black"), ft.Text(f"R$ {custo_total/num_pessoas:.2f}", weight="bold", color="#059669")]),
                    ft.ElevatedButton("📊 Exportar para Excel", icon=ft.Icons.FILE_DOWNLOAD, on_click=self.exportar_excel, color="white", bgcolor="#1e7145")
                ], spacing=10)
            )
            self.copiar_btn.visible = True
        finally:
            self.gerar_btn.disabled = False
            self.page.update()

    # ATUALIZAÇÃO AUTOMÁTICA
    # ===================================================================
    def verificar_atualizacao_auto(self):
        threading.Thread(target=self._check_updates_worker, daemon=True).start()

    def _check_updates_worker(self):
        try:
            manager = UpdateManager(current_version=VERSION, repo_url=UPDATE_BASE_URL)
            result = manager.check_for_updates()
            if result.get("update_available"):
                self.show_update_dialog(result, manager)
        except: pass

    def show_update_dialog(self, update_info, manager):
        def start_update(e):
            self.close_dialog(e)
            self.show_snackbar("📥 Atualizando...")
            threading.Thread(target=lambda: manager.download_and_install(update_info["download_url"]), daemon=True).start()

        dialog = ft.AlertDialog(
            title=ft.Text("Versão Disponível"),
            content=ft.Text(f"Instalar versão {update_info['version']}?"),
            actions=[
                ft.TextButton("Depois", on_click=self.close_dialog),
                ft.ElevatedButton("Instalar", on_click=start_update, bgcolor="#3b82f6", color="white"),
            ],
        )
        self.page.dialog = dialog
        self.page.open(dialog)

    # HISTÓRICO E GRÁFICOS
    # ===================================================================

    def abrir_historico(self, e):
        try:
            jogos = self.app.db_manager.carregar_historico()
            stats = self.app.db_manager.get_estatisticas()
            lista_jogos = ft.Column(spacing=10, scroll=ft.ScrollMode.AUTO, expand=True)
            for j in jogos:
                nums = json.loads(j[3])[0]
                lista_jogos.controls.append(
                    ft.Container(
                        content=ft.Column([
                            ft.Row([ft.Text(f"{j[1]} - {j[9][:10]}", weight="bold", color="black"),
                                    ft.Row([ft.Text(f"R$ {j[5]:.2f}", color="#059669", weight="bold"),
                                            ft.IconButton(ft.Icons.DELETE_OUTLINE, icon_color="#ef4444", on_click=lambda _, id=j[0]: (self.app.db_manager.excluir_jogo(id), self.abrir_historico(None)))])], alignment="spaceBetween"),
                            ft.Row([ft.Container(content=ft.Text(f"{n:02d}", color="white", size=10, weight="bold"), bgcolor=self.config_loteria[j[1]]["cor_bola"], width=22, height=22, border_radius=11, alignment=ft.alignment.center) for n in nums], wrap=True)
                        ]), padding=12, border_radius=10, border=ft.border.all(1, "#e2e8f0"), bgcolor="white"
                    )
                )
            dialog = ft.AlertDialog(
                title=ft.Text("Histórico"),
                content=ft.Container(content=ft.Column([
                    ft.Container(content=ft.Row([
                        ft.Column([ft.Text("Total Gasto", size=11, color="black"), ft.Text(f"R$ {stats.get('total_gasto', 0):.2f}", size=18, weight="bold", color="#059669")]),
                        ft.Column([ft.Text("Registros", size=11, color="black"), ft.Text(f"{stats.get('total_jogos', 0)}", size=18, weight="bold", color="black")]),
                    ], alignment="center", spacing=40), padding=15, bgcolor="#f1f5f9", border_radius=10),
                    ft.Divider(), lista_jogos
                ]), width=500, height=550),
                actions=[ft.TextButton("Fechar", on_click=self.close_dialog)]
            )
            self.page.dialog = dialog
            self.page.open(dialog)
        except: pass

    def mostrar_grafico(self, e):
        if self.df_atual is None: return
        config = self.config_loteria[self.app.loteria.current.value]
        def update_plot(n):
            df_f = self.df_atual.head(n) if n > 0 else self.df_atual
            nums = df_f[config["colunas_numeros"]].values.flatten()
            nums = nums[~np.isnan(nums)].astype(int)
            freq = np.bincount(nums, minlength=config["num_total"] + 1)[1:]
            fig, ax = plt.subplots(figsize=(10, 4))
            ax.bar(range(1, config["num_total"] + 1), freq, color="#cbd5e1")
            if self.app.jogos_atuais:
                curr = [n for j in self.app.jogos_atuais for n in j]
                f_curr = np.bincount(curr, minlength=config["num_total"]+1)[1:]
                idx = [i for i, v in enumerate(f_curr) if v > 0]
                ax.bar([i+1 for i in idx], [freq[i] for i in idx], color=config["cor_bola"])
            chart_box.content = MatplotlibChart(fig, expand=True)
            self.page.update()

        chart_box = ft.Container(height=350)
        dialog = ft.AlertDialog(
            title=ft.Text("📊 Tendências"),
            content=ft.Column([ft.Slider(min=0, max=200, divisions=20, on_change=lambda e: update_plot(int(e.control.value))), chart_box], width=800, height=450),
            actions=[ft.TextButton("Fechar", on_click=self.close_dialog)]
        )
        self.page.dialog = dialog
        self.page.open(dialog)
        update_plot(0)

    # MÉTODO PRINCIPAL
    # ===================================================================
    def main(self, page: ft.Page):
        self.page = page
        page.title = "Loterias Pro"
        page.window.maximized = True
        page.theme = ft.Theme(color_scheme_seed="#3b82f6")

        # Refs
        self.app.loteria, self.app.num_dezenas, self.app.metodo = ft.Ref[ft.Dropdown](), ft.Ref[ft.Slider](), ft.Ref[ft.Dropdown]()
        self.app.is_bolao, self.app.num_jogos, self.app.num_participantes = ft.Ref[ft.Checkbox](), ft.Ref[ft.TextField](), ft.Ref[ft.TextField]()

        self.dezenas_slider = ft.Slider(ref=self.app.num_dezenas, min=6, max=20, value=6, on_change=self.atualizar_label_dezenas)
        self.dezenas_info = ft.Text("R$ 5.00", color="#059669", weight="bold", size=16)
        self.numeros_grid = ft.ResponsiveRow(spacing=15, run_spacing=15)
        
        lbl_style = ft.TextStyle(color="black", weight="bold")

        self.gerar_btn = ft.ElevatedButton("🎲 Gerar", bgcolor="#3b82f6", color="white", expand=True, height=45, on_click=self.gerar_jogos)
        self.limpar_btn = ft.ElevatedButton("🧹 Limpar", bgcolor="#cbd5e1", color="black", expand=True, height=45, on_click=lambda _: self.numeros_grid.controls.clear() or self.page.update())
        self.copiar_btn = ft.IconButton(icon=ft.Icons.COPY_ALL_ROUNDED, on_click=self.copiar_jogos, visible=False)

        self.info_content = ft.Column()
        self.resumo_content = ft.Column()

        self.bolao_container = ft.Row([
            ft.TextField(ref=self.app.num_jogos, label="Nº de Jogos", value="1", expand=True, color="black", label_style=lbl_style),
            ft.TextField(ref=self.app.num_participantes, label="Nº Pessoas", value="1", expand=True, color="black", label_style=lbl_style),
        ], visible=False)

        header = ft.Container(
            content=ft.Row([
                ft.Row([ft.Icon(ft.Icons.AUTO_GRAPH, color="#3b82f6"), ft.Text("Loterias Pro", size=22, weight="bold", color="black")]),
                ft.Row([self.copiar_btn, ft.IconButton(ft.Icons.BAR_CHART_ROUNDED, on_click=self.mostrar_grafico, icon_color="black"), 
                        ft.IconButton(ft.Icons.HISTORY_ROUNDED, on_click=self.abrir_historico, icon_color="black")])
            ], alignment="spaceBetween"),
            padding=15, bgcolor="white", border=ft.border.only(bottom=ft.BorderSide(1, "#f1f5f9"))
        )

        left_panel = ft.Container(
            content=ft.Column([
                ft.Dropdown(ref=self.app.loteria, label="Selecione a Loteria", label_style=lbl_style, options=[ft.dropdown.Option("Mega-Sena"), ft.dropdown.Option("Loto Fácil")], value="Mega-Sena", on_change=self.atualizar_dezenas, color="black"),
                ft.Dropdown(ref=self.app.metodo, label="Método de Geração", label_style=lbl_style, options=[ft.dropdown.Option("Top Frequentes"), ft.dropdown.Option("Probabilistico")], value="Top Frequentes", color="black"),
                ft.Row([ft.Text("Custo Unitário:", color="black", weight="bold"), self.dezenas_info], alignment="spaceBetween"),
                self.dezenas_slider,
                ft.Checkbox(ref=self.app.is_bolao, label="Modo Bolão", on_change=self.toggle_bolao, label_style=lbl_style),
                self.bolao_container,
                ft.Row([self.gerar_btn, self.limpar_btn], spacing=10),
            ], spacing=20),
            padding=20, bgcolor="white", border_radius=12, col={"xs": 12, "md": 4, "lg": 3}, border=ft.border.all(1, "#f1f5f9")
        )

        right_panel = ft.Column([
            ft.Container(
                content=ft.Column([
                    ft.Row([ft.Icon(ft.Icons.GRID_VIEW_ROUNDED, color="black"), ft.Text("Painel de Geração", weight="bold", color="black")]),
                    ft.Column([self.numeros_grid], scroll=ft.ScrollMode.AUTO, expand=True)
                ]),
                padding=20, bgcolor="white", border_radius=12, height=450, border=ft.border.all(1, "#f1f5f9")
            ),
            ft.Container(
                content=ft.Tabs(tabs=[
                    ft.Tab(text="Informações", icon=ft.Icons.INFO_OUTLINE, content=ft.Container(self.info_content, padding=20)),
                    ft.Tab(text="Resumo Financeiro", icon=ft.Icons.ATTACH_MONEY, content=ft.Container(self.resumo_content, padding=20))
                ], label_color="black", unselected_label_color="black"), bgcolor="white", border_radius=12, expand=True, border=ft.border.all(1, "#f1f5f9")
            )
        ], spacing=20, col={"xs": 12, "md": 8, "lg": 9}, expand=True)

        page.add(ft.Column([header, ft.Container(ft.ResponsiveRow([left_panel, right_panel], spacing=20), padding=20, expand=True)], expand=True))
        
        # INICIALIZAÇÃO DE DADOS
        self.atualizar_dezenas(None)
        
        # FORÇAR ATUALIZAÇÃO DA PÁGINA ANTES DE MAXIMIZAR
        page.update() 

        # Checa update em segundo plano
        self.verificar_atualizacao_auto()