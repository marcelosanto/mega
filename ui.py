import tkinter as tk
from tkinter import ttk, messagebox
import pandas as pd
import numpy as np
from math import comb
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import json
from config import LOTTERY_CONFIG
from utils import get_resource_path


class LoteriaUI:
    def __init__(self, app):
        self.app = app
        self.config_loteria = LOTTERY_CONFIG
        self.configurar_estilo()
        self.criar_interface()

    def configurar_estilo(self):
        style = ttk.Style()
        style.theme_use('clam')

        # Paleta de cores Black Theme melhorada
        colors = {
            'bg_primary': '#0a0a0a',        # Preto principal mais profundo
            'bg_secondary': '#1a1a1a',      # Preto secundário
            'bg_card': '#2d2d2d',           # Cards/painéis
            'bg_input': '#3d3d3d',          # Inputs e campos
            'bg_hover': '#4d4d4d',          # Hover states
            'text_primary': '#ffffff',       # Texto principal (branco)
            'text_secondary': '#b0b0b0',    # Texto secundário
            'text_accent': '#e0e0e0',       # Texto de destaque
            'accent_primary': '#00d4aa',    # Verde-azulado vibrante
            'accent_secondary': '#ff6b6b',  # Vermelho coral
            'accent_tertiary': '#4ecdc4',   # Azul-verde suave
            'accent_warning': '#ffd93d',    # Amarelo dourado
            'accent_info': '#74b9ff',       # Azul suave
            'border_light': '#5a5a5a',      # Bordas claras
            'border_dark': '#2a2a2a',       # Bordas escuras
        }

        # Estilos para labels
        style.configure('Title.TLabel',
                        background=colors['bg_primary'],
                        foreground=colors['accent_primary'],
                        font=('Segoe UI', 18, 'bold'))

        style.configure('Subtitle.TLabel',
                        background=colors['bg_primary'],
                        foreground=colors['text_accent'],
                        font=('Segoe UI', 12, 'bold'))

        style.configure('Modern.TLabel',
                        background=colors['bg_card'],
                        foreground=colors['text_secondary'],
                        font=('Segoe UI', 10))

        style.configure('Card.TLabel',
                        background=colors['bg_card'],
                        foreground=colors['text_primary'],
                        font=('Segoe UI', 11, 'bold'))

        # Estilos para combobox
        style.configure('Modern.TCombobox',
                        fieldbackground=colors['bg_input'],
                        background=colors['bg_input'],
                        foreground=colors['text_primary'],
                        borderwidth=1,
                        relief='solid',
                        insertcolor=colors['text_primary'])
        style.map('Modern.TCombobox',
                  focuscolor=[('!focus', colors['border_light'])],
                  bordercolor=[('focus', colors['accent_primary'])])

        # Botões primários
        style.configure('Modern.TButton',
                        background=colors['accent_primary'],
                        foreground=colors['bg_primary'],
                        borderwidth=0,
                        focuscolor='none',
                        font=('Segoe UI', 10, 'bold'),
                        padding=(15, 8))
        style.map('Modern.TButton',
                  background=[('active', colors['accent_tertiary']),
                              ('pressed', '#00c49a')])

        # Botões secundários
        style.configure('Secondary.TButton',
                        background=colors['accent_info'],
                        foreground='white',
                        borderwidth=0,
                        focuscolor='none',
                        font=('Segoe UI', 10, 'bold'),
                        padding=(15, 8))
        style.map('Secondary.TButton',
                  background=[('active', '#5aa3ff'),
                              ('pressed', colors['accent_info'])])

        # Botões de sucesso
        style.configure('Success.TButton',
                        background=colors['accent_tertiary'],
                        foreground=colors['bg_primary'],
                        borderwidth=0,
                        focuscolor='none',
                        font=('Segoe UI', 10, 'bold'),
                        padding=(15, 8))
        style.map('Success.TButton',
                  background=[('active', '#3fb8b0'),
                              ('pressed', colors['accent_tertiary'])])

        # Botões de perigo
        style.configure('Danger.TButton',
                        background=colors['accent_secondary'],
                        foreground='white',
                        borderwidth=0,
                        focuscolor='none',
                        font=('Segoe UI', 10, 'bold'),
                        padding=(15, 8))
        style.map('Danger.TButton',
                  background=[('active', '#ff5252'),
                              ('pressed', colors['accent_secondary'])])

        # Guardar cores para uso posterior
        self.colors = colors

    def carregar_dados(self):
        loteria = self.app.loteria.get()
        config = self.config_loteria[loteria]
        try:
            xlsx_path = get_resource_path(config['caminho_xlsx'])
            df = pd.read_excel(xlsx_path, sheet_name=0, skiprows=6)
            if not all(col in df.columns for col in config['colunas_numeros']):
                raise ValueError(
                    "Colunas de bolas não encontradas. Verifique o arquivo XLSX.")
            self.app.numeros_flat = df[config['colunas_numeros']].values.flatten(
            )
            self.app.freq = np.bincount(
                self.app.numeros_flat, minlength=config['num_total'] + 1)[1:]
            if len(self.app.freq) == 0:
                raise ValueError("Frequências não calculadas corretamente.")
        except Exception as e:
            messagebox.showerror("❌ Erro", f"Erro ao carregar dados: {e}")
            self.app.root.quit()

    def calcular_preco(self, num_dezenas):
        loteria = self.app.loteria.get()
        config = self.config_loteria[loteria]
        if loteria == 'Mega-Sena':
            if num_dezenas < 6 or num_dezenas > 20:
                return 0
            num_combs = comb(num_dezenas, 6)
        elif loteria == 'Loto Fácil':
            if num_dezenas < 15 or num_dezenas > 20:
                return 0
            num_combs = comb(num_dezenas, 15)
        return num_combs * config['preco_base']

    def gerar_numeros(self, metodo, num_dezenas):
        loteria = self.app.loteria.get()
        config = self.config_loteria[loteria]
        top_n = min(len(self.app.freq), config['num_total'])
        if loteria == 'Mega-Sena':
            top_n = 40
        elif loteria == 'Loto Fácil':
            top_n = 25
        try:
            numeros_ordenados = np.argsort(self.app.freq)[::-1] + 1
            top = numeros_ordenados[:top_n]
            if metodo == 'top_frequentes':
                if len(top) < num_dezenas:
                    raise ValueError(
                        f"Não há números suficientes nos top para selecionar {num_dezenas} dezenas.")
                numeros_selecionados = np.random.choice(
                    top, size=num_dezenas, replace=False)
                return [int(x) for x in sorted(numeros_selecionados)]
            elif metodo == 'probabilistico':
                probs = self.app.freq / self.app.freq.sum()
                if len(probs) != config['num_total']:
                    raise ValueError(
                        "Probabilidades não calculadas corretamente.")
                numeros_selecionados = np.random.choice(
                    range(1, config['num_total'] + 1), size=num_dezenas, replace=False, p=probs)
                return [int(x) for x in sorted(numeros_selecionados)]
            else:
                raise ValueError(f"Método inválido: {metodo}")
        except Exception as e:
            messagebox.showerror("❌ Erro", f"Erro ao gerar números: {e}")
            return []

    def atualizar_dezenas(self, *args):
        loteria = self.app.loteria.get()
        config = self.config_loteria[loteria]
        self.app.num_dezenas.set(config['min_dezenas'])
        if hasattr(self, 'dezenas_scale'):
            self.dezenas_scale.config(
                from_=config['min_dezenas'], to=config['max_dezenas'])
        if hasattr(self, 'dezenas_value_label'):
            self.atualizar_label_dezenas()
        if hasattr(self, 'info_text'):
            self.info_text.delete(1.0, tk.END)
            info = f"""📊 INFORMAÇÕES DA {loteria.upper()}

🎯 Números disponíveis: 1 a {config['num_total']}
🎲 Números sorteados: {config['num_sorteados']}
💰 Preço base: R$ {config['preco_base']:.2f}
📈 Dezenas: {config['min_dezenas']} a {config['max_dezenas']}

💡 DICAS:
• Apostas com mais números = mais combinações = maior custo
• Use o bolão para dividir custos entre amigos
• Métodos baseados em histórico de sorteios
• Lembre-se: loteria é totalmente aleatória!"""
            self.info_text.insert(tk.END, info)
        self.carregar_dados()

    def atualizar_label_dezenas(self, *args):
        if hasattr(self, 'dezenas_value_label'):
            preco = self.calcular_preco(self.app.num_dezenas.get())
            self.dezenas_value_label.config(
                text=f"{self.app.num_dezenas.get()} dezenas (R$ {preco:.2f})")

    def toggle_bolao(self):
        if self.app.is_bolao.get():
            self.bolao_frame.pack(fill='x', pady=(10, 0))
        else:
            self.bolao_frame.pack_forget()
            self.app.num_jogos.set(1)
            self.app.num_participantes.set(1)

    def criar_bola_canvas(self, parent, numero, cor_base, tamanho=35):
        canvas = tk.Canvas(parent, width=tamanho*2, height=tamanho*2,
                           bg=self.colors['bg_input'], highlightthickness=0)

        # Sombra da bola
        canvas.create_oval(7, 7, tamanho*2-3, tamanho*2-3,
                           fill='#000000', outline='', stipple='gray25')

        # Bola principal
        canvas.create_oval(2, 2, tamanho*2-8, tamanho*2-8,
                           fill=cor_base, outline=self.colors['border_light'], width=2)

        # Reflexo na bola
        canvas.create_oval(8, 8, tamanho-5, tamanho-5,
                           fill='white', outline='', stipple='gray75')

        # Número
        canvas.create_text(tamanho-3, tamanho-3, text=f"{numero:02d}",
                           fill='white', font=('Segoe UI', 12, 'bold'))
        return canvas

    def gerar_jogos(self):
        for widget in self.canvas_frame.winfo_children():
            widget.destroy()
        self.resultado_text.delete(1.0, tk.END)

        loteria = self.app.loteria.get()
        config = self.config_loteria[loteria]
        metodo = self.app.metodo.get().lower().replace(" ", "_")
        num_dezenas = self.app.num_dezenas.get()
        num_jogos = self.app.num_jogos.get()
        num_participantes = self.app.num_participantes.get()

        jogos = []
        for _ in range(num_jogos):
            nums = self.gerar_numeros(metodo, num_dezenas)
            if nums:
                jogos.append(nums)

        if not jogos:
            messagebox.showerror(
                "❌ Erro", "Nenhum jogo foi gerado. Verifique os dados e tente novamente.")
            return

        self.app.jogos_atuais = jogos.copy()
        preco_unitario = self.calcular_preco(num_dezenas)
        preco_total = preco_unitario * num_jogos
        preco_por_pessoa = preco_total / num_participantes if num_participantes > 0 else 0

        if hasattr(self, 'salvar_button'):
            self.salvar_button.pack(fill='x', pady=(5, 0))

        self.resultado_text.insert(tk.END, f"💰 CUSTOS\n")
        self.resultado_text.insert(
            tk.END, f"Preço por jogo: R$ {preco_unitario:.2f}\n")
        if self.app.is_bolao.get():
            self.resultado_text.insert(
                tk.END, f"Total do bolão: R$ {preco_total:.2f}\n")
            self.resultado_text.insert(
                tk.END, f"Por participante: R$ {preco_por_pessoa:.2f}\n")
        self.resultado_text.insert(tk.END, "\n🎲 NÚMEROS GERADOS:\n\n")

        for idx, nums in enumerate(jogos, 1):
            jogo_frame = tk.Frame(self.canvas_frame, bg=self.colors['bg_card'],
                                  relief='solid', bd=1)
            jogo_frame.pack(fill='x', padx=10, pady=5)

            # Header do jogo com gradiente visual
            header_frame = tk.Frame(
                jogo_frame, bg=self.colors['bg_hover'], height=5)
            header_frame.pack(fill='x')

            tk.Label(jogo_frame, text=f"🎯 Jogo {idx}",
                     bg=self.colors['bg_card'], fg=self.colors['accent_primary'],
                     font=('Segoe UI', 12, 'bold')).pack(anchor='w', padx=15, pady=(15, 5))

            bolas_frame = tk.Frame(jogo_frame, bg=self.colors['bg_card'])
            bolas_frame.pack(fill='x', padx=15, pady=(0, 15))

            for num in nums:
                bola = self.criar_bola_canvas(
                    bolas_frame, num, config['cor_bola'])
                bola.pack(side='left', padx=3)

            numeros_str = ' - '.join([f"{num:02d}" for num in nums])
            self.resultado_text.insert(tk.END, f"Jogo {idx}: {numeros_str}\n")

        self.canvas_frame.update_idletasks()
        self.canvas_scroll.configure(
            scrollregion=self.canvas_scroll.bbox("all"))

    def mostrar_grafico(self):
        loteria_config = self.config_loteria[self.app.loteria.get()]

        # Configurar estilo dark para matplotlib
        plt.style.use('dark_background')
        fig, ax = plt.subplots(figsize=(12, 7))
        fig.patch.set_facecolor(self.colors['bg_primary'])
        ax.set_facecolor(self.colors['bg_secondary'])

        # Criar barras com gradiente de cores
        bars = ax.bar(range(1, loteria_config['num_total'] + 1), self.app.freq,
                      color=self.colors['accent_info'], alpha=0.8, edgecolor=self.colors['border_light'])

        # Destacar os top 5 números
        top_5_indices = np.argsort(self.app.freq)[-5:]
        for idx in top_5_indices:
            bars[idx].set_color(self.colors['accent_primary'])
            bars[idx].set_edgecolor(self.colors['accent_tertiary'])
            bars[idx].set_linewidth(2)

        ax.set_xlabel(
            "Números", color=self.colors['text_primary'], fontsize=12, fontweight='bold')
        ax.set_ylabel(
            "Frequência", color=self.colors['text_primary'], fontsize=12, fontweight='bold')
        ax.set_title(f"📊 Frequência dos Números - {self.app.loteria.get()}",
                     color=self.colors['accent_primary'], fontsize=16, fontweight='bold', pad=20)

        ax.tick_params(colors=self.colors['text_secondary'], labelsize=10)
        ax.grid(True, alpha=0.2, color=self.colors['border_light'])
        ax.spines['bottom'].set_color(self.colors['border_light'])
        ax.spines['top'].set_color(self.colors['border_light'])
        ax.spines['right'].set_color(self.colors['border_light'])
        ax.spines['left'].set_color(self.colors['border_light'])

        plt.tight_layout()

        grafico_window = tk.Toplevel(self.app.root)
        grafico_window.title("📊 Gráfico de Frequências")
        grafico_window.configure(bg=self.colors['bg_primary'])
        grafico_window.geometry("1200x800")

        canvas = FigureCanvasTkAgg(fig, master=grafico_window)
        canvas.draw()
        canvas.get_tk_widget().pack(fill='both', expand=True, padx=10, pady=10)

        plt.close(fig)

    def criar_janela_salvar(self):
        save_window = tk.Toplevel(self.app.root)
        save_window.title("💾 Salvar Jogo")
        save_window.geometry("350x450")
        save_window.configure(bg=self.colors['bg_primary'])
        save_window.transient(self.app.root)
        save_window.grab_set()
        save_window.geometry(
            "+%d+%d" % (self.app.root.winfo_rootx() + 50, self.app.root.winfo_rooty() + 50))

        # Header
        header_frame = tk.Frame(
            save_window, bg=self.colors['bg_card'], height=80)
        header_frame.pack(fill='x', padx=1, pady=(1, 20))
        header_frame.pack_propagate(False)

        title_label = tk.Label(header_frame, text="💾 Salvar Jogo",
                               bg=self.colors['bg_card'], fg=self.colors['accent_primary'],
                               font=('Segoe UI', 16, 'bold'))
        title_label.pack(expand=True)

        # Info card
        info_frame = tk.Frame(
            save_window, bg=self.colors['bg_card'], relief='solid', bd=1)
        info_frame.pack(fill='x', padx=20, pady=(0, 20))

        info_text = f"""🎲 {self.app.loteria.get()}
📊 {len(self.app.jogos_atuais)} jogo(s) gerado(s)
🎯 {self.app.num_dezenas.get()} dezenas cada
💰 R$ {self.calcular_preco(self.app.num_dezenas.get()) * len(self.app.jogos_atuais):.2f}"""

        tk.Label(info_frame, text=info_text, bg=self.colors['bg_card'], fg=self.colors['text_primary'],
                 font=('Segoe UI', 11), justify='left').pack(padx=20, pady=20)

        # Observações
        tk.Label(save_window, text="📝 Observações (opcional):", bg=self.colors['bg_primary'],
                 fg=self.colors['text_accent'], font=('Segoe UI', 11, 'bold')).pack(anchor='w', padx=20)

        obs_text = tk.Text(save_window, height=4, width=40, bg=self.colors['bg_input'],
                           fg=self.colors['text_primary'], font=(
                               'Segoe UI', 10),
                           relief='solid', wrap='word', insertbackground=self.colors['text_primary'],
                           bd=1, highlightthickness=1, highlightcolor=self.colors['accent_primary'])
        obs_text.pack(fill='x', padx=20, pady=(10, 20))

        # Botões
        buttons_frame = tk.Frame(save_window, bg=self.colors['bg_primary'])
        buttons_frame.pack(fill='x', padx=20, pady=(0, 20))

        def confirmar_save():
            observacoes = obs_text.get("1.0", tk.END).strip()
            if self.app.db_manager.salvar_no_banco(self.app, observacoes):
                save_window.destroy()

        save_btn = tk.Button(buttons_frame, text="💾 Salvar", command=confirmar_save,
                             bg=self.colors['accent_primary'], fg=self.colors['bg_primary'],
                             font=('Segoe UI', 11, 'bold'), relief='flat', cursor='hand2',
                             activebackground=self.colors['accent_tertiary'], bd=0, pady=12)
        save_btn.pack(side='left', fill='x', expand=True, padx=(0, 10))

        cancel_btn = tk.Button(buttons_frame, text="❌ Cancelar", command=save_window.destroy,
                               bg=self.colors['accent_secondary'], fg='white',
                               font=('Segoe UI', 11, 'bold'), relief='flat', cursor='hand2',
                               activebackground='#ff5252', bd=0, pady=12)
        cancel_btn.pack(side='right', fill='x', expand=True)

    def abrir_historico(self):
        hist_window = tk.Toplevel(self.app.root)
        hist_window.title("📚 Histórico de Jogos")
        hist_window.geometry("1200x700")
        hist_window.configure(bg=self.colors['bg_primary'])

        # Header
        header_frame = tk.Frame(
            hist_window, bg=self.colors['bg_card'], height=80)
        header_frame.pack(fill='x', padx=1, pady=(1, 20))
        header_frame.pack_propagate(False)

        title_label = tk.Label(header_frame, text="📚 Histórico de Jogos Salvos",
                               bg=self.colors['bg_card'], fg=self.colors['accent_primary'],
                               font=('Segoe UI', 18, 'bold'))
        title_label.pack(expand=True)

        # Filtros
        filter_frame = tk.Frame(hist_window, bg=self.colors['bg_card'])
        filter_frame.pack(fill='x', padx=20, pady=(0, 20))

        tk.Label(filter_frame, text="Filtrar por loteria:", bg=self.colors['bg_card'],
                 fg=self.colors['text_secondary'], font=('Segoe UI', 10)).pack(side='left', padx=(20, 10), pady=20)

        filter_var = tk.StringVar(value="Todas")
        filter_combo = ttk.Combobox(filter_frame, textvariable=filter_var, values=['Todas', 'Mega-Sena', 'Loto Fácil'],
                                    state='readonly', width=15, style='Modern.TCombobox')
        filter_combo.pack(side='left', padx=(0, 20), pady=20)

        def atualizar_lista():
            self.app.db_manager.carregar_historico(tree, filter_var.get())

        filter_combo.bind('<<ComboboxSelected>>', lambda e: atualizar_lista())

        refresh_btn = tk.Button(filter_frame, text="🔄 Atualizar", command=atualizar_lista,
                                bg=self.colors['accent_info'], fg='white',
                                font=('Segoe UI', 10, 'bold'), relief='flat', cursor='hand2',
                                activebackground='#5aa3ff', bd=0, pady=8, padx=15)
        refresh_btn.pack(side='left', padx=(10, 20), pady=20)

        # TreeView
        tree_frame = tk.Frame(hist_window, bg=self.colors['bg_primary'])
        tree_frame.pack(fill='both', expand=True, padx=20, pady=(0, 20))

        tree_scroll_y = ttk.Scrollbar(tree_frame, orient="vertical")
        tree_scroll_x = ttk.Scrollbar(tree_frame, orient="horizontal")

        tree = ttk.Treeview(tree_frame, yscrollcommand=tree_scroll_y.set,
                            xscrollcommand=tree_scroll_x.set, height=15)
        tree['columns'] = ("ID", "Loteria", "Método",
                           "Dezenas", "Jogos", "Preço", "Data", "Obs")
        tree['show'] = 'headings'

        # Headers da tabela
        for col in tree['columns']:
            tree.heading(col, text=col)

        tree.column("ID", width=50)
        tree.column("Loteria", width=100)
        tree.column("Método", width=120)
        tree.column("Dezenas", width=80)
        tree.column("Jogos", width=60)
        tree.column("Preço", width=100)
        tree.column("Data", width=150)
        tree.column("Obs", width=200)

        tree.pack(side='left', fill='both', expand=True)
        tree_scroll_y.pack(side='right', fill='y')
        tree_scroll_x.pack(side='bottom', fill='x')
        tree_scroll_y.config(command=tree.yview)
        tree_scroll_x.config(command=tree.xview)

        # Botões de ação
        buttons_frame = tk.Frame(hist_window, bg=self.colors['bg_primary'])
        buttons_frame.pack(fill='x', padx=20, pady=(0, 20))

        def ver_detalhes():
            selected = tree.selection()
            if not selected:
                messagebox.showwarning(
                    "⚠️ Atenção", "Selecione um jogo para ver detalhes!")
                return
            item = tree.item(selected[0])
            jogo_id = item['values'][0]
            self.app.db_manager.mostrar_detalhes_jogo(self.app, jogo_id)

        def excluir_jogo():
            selected = tree.selection()
            if not selected:
                messagebox.showwarning(
                    "⚠️ Atenção", "Selecione um jogo para excluir!")
                return
            if messagebox.askyesno("❓ Confirmar", "Deseja realmente excluir este jogo do histórico?"):
                item = tree.item(selected[0])
                jogo_id = item['values'][0]
                self.app.db_manager.excluir_jogo(jogo_id)
                atualizar_lista()

        details_btn = tk.Button(buttons_frame, text="👁️ Ver Detalhes", command=ver_detalhes,
                                bg=self.colors['accent_info'], fg='white',
                                font=('Segoe UI', 11, 'bold'), relief='flat', cursor='hand2',
                                activebackground='#5aa3ff', bd=0, pady=10, padx=20)
        details_btn.pack(side='left', padx=(0, 15))

        delete_btn = tk.Button(buttons_frame, text="🗑️ Excluir", command=excluir_jogo,
                               bg=self.colors['accent_secondary'], fg='white',
                               font=('Segoe UI', 11, 'bold'), relief='flat', cursor='hand2',
                               activebackground='#ff5252', bd=0, pady=10, padx=20)
        delete_btn.pack(side='left')

        self.app.db_manager.carregar_historico(tree, "Todas")

    def mostrar_detalhes_jogo(self, jogo_id, jogo):
        det_window = tk.Toplevel(self.app.root)
        det_window.title(f"🔍 Detalhes do Jogo #{jogo_id}")
        det_window.geometry("700x600")
        det_window.configure(bg=self.colors['bg_primary'])

        # Header
        header_frame = tk.Frame(
            det_window, bg=self.colors['bg_card'], height=80)
        header_frame.pack(fill='x', padx=1, pady=(1, 20))
        header_frame.pack_propagate(False)

        title_label = tk.Label(header_frame, text=f"🔍 Jogo #{jogo_id} - {jogo[1]}",
                               bg=self.colors['bg_card'], fg=self.colors['accent_primary'],
                               font=('Segoe UI', 16, 'bold'))
        title_label.pack(expand=True)

        # Container principal
        main_container = tk.Frame(det_window, bg=self.colors['bg_primary'])
        main_container.pack(fill='both', expand=True, padx=20, pady=(0, 20))

        # Info card
        info_frame = tk.Frame(
            main_container, bg=self.colors['bg_card'], relief='solid', bd=1)
        info_frame.pack(fill='x', pady=(0, 20))

        info_text = f"""📊 INFORMAÇÕES GERAIS
🎲 Loteria: {jogo[1]}
🧮 Método: {jogo[2]}
🎯 Dezenas por jogo: {jogo[4]}
💰 Preço total: R$ {jogo[5]:.2f}
🤝 Bolão: {'Sim' if jogo[6] else 'Não'}
🎮 Quantidade de jogos: {jogo[7]}
👥 Participantes: {jogo[8]}
📅 Data de criação: {jogo[9]}

📝 OBSERVAÇÕES:
{jogo[10] if jogo[10] else 'Nenhuma observação'}"""

        info_label = tk.Label(info_frame, text=info_text, bg=self.colors['bg_card'],
                              fg=self.colors['text_primary'], font=('Segoe UI', 11), justify='left')
        info_label.pack(anchor='w', padx=25, pady=25)

        # Números jogados
        numeros_label = tk.Label(main_container, text="🎯 NÚMEROS JOGADOS:",
                                 bg=self.colors['bg_primary'], fg=self.colors['accent_primary'],
                                 font=('Segoe UI', 14, 'bold'))
        numeros_label.pack(anchor='w', pady=(0, 15))

        # Container com scroll para os números
        numeros_container = tk.Frame(
            main_container, bg=self.colors['bg_primary'])
        numeros_container.pack(fill='both', expand=True)

        canvas_scroll = tk.Canvas(numeros_container, bg=self.colors['bg_secondary'],
                                  highlightthickness=0)
        scrollbar = ttk.Scrollbar(
            numeros_container, orient="vertical", command=canvas_scroll.yview)
        numeros_frame = tk.Frame(canvas_scroll, bg=self.colors['bg_secondary'])

        numeros_frame.bind("<Configure>", lambda e: canvas_scroll.configure(
            scrollregion=canvas_scroll.bbox("all")))
        canvas_scroll.create_window((0, 0), window=numeros_frame, anchor="nw")
        canvas_scroll.configure(yscrollcommand=scrollbar.set)

        try:
            numeros_jogos = json.loads(jogo[3])
            config = self.config_loteria[jogo[1]]

            for idx, numeros in enumerate(numeros_jogos, 1):
                jogo_frame = tk.Frame(numeros_frame, bg=self.colors['bg_card'],
                                      relief='solid', bd=1)
                jogo_frame.pack(fill='x', pady=8, padx=10)

                # Header do jogo
                header_jogo = tk.Frame(
                    jogo_frame, bg=self.colors['bg_hover'], height=8)
                header_jogo.pack(fill='x')

                tk.Label(jogo_frame, text=f"Jogo {idx}:", bg=self.colors['bg_card'],
                         fg=self.colors['accent_primary'], font=('Segoe UI', 12, 'bold')).pack(
                    anchor='w', padx=15, pady=(15, 8))

                bolas_frame = tk.Frame(jogo_frame, bg=self.colors['bg_card'])
                bolas_frame.pack(fill='x', padx=15, pady=(0, 15))

                for num in numeros:
                    bola = self.criar_bola_canvas(
                        bolas_frame, num, config['cor_bola'], 28)
                    bola.pack(side='left', padx=3)

        except Exception as e:
            error_label = tk.Label(numeros_frame, text=f"❌ Erro ao carregar números: {e}",
                                   bg=self.colors['bg_secondary'], fg=self.colors['accent_secondary'],
                                   font=('Segoe UI', 12))
            error_label.pack(pady=20)

        canvas_scroll.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

    def criar_interface(self):
        main_container = tk.Frame(self.app.root, bg=self.colors['bg_primary'])
        main_container.pack(fill='both', expand=True, padx=25, pady=25)

        # Header principal
        header_frame = tk.Frame(
            main_container, bg=self.colors['bg_card'], height=100)
        header_frame.pack(fill='x', pady=(0, 25))
        header_frame.pack_propagate(False)

        title_label = ttk.Label(header_frame, text="🎯 Gerador de Números para Loterias",
                                style='Title.TLabel')
        title_label.pack(expand=True)

        # Container principal de conteúdo
        content_frame = tk.Frame(main_container, bg=self.colors['bg_primary'])
        content_frame.pack(fill='both', expand=True)

        # Painel esquerdo
        left_frame = tk.Frame(content_frame, bg=self.colors['bg_primary'])
        left_frame.pack(side='left', fill='y', padx=(0, 25))

        # Card de seleção de loteria
        loteria_card = tk.LabelFrame(left_frame, text="🎲 Loteria",
                                     bg=self.colors['bg_card'], fg=self.colors['accent_primary'],
                                     font=('Segoe UI', 12, 'bold'), relief='solid', bd=1)
        loteria_card.pack(fill='x', pady=(0, 20))

        tk.Label(loteria_card, text="Escolha a loteria:", bg=self.colors['bg_card'],
                 fg=self.colors['text_secondary'], font=('Segoe UI', 10)).pack(
            anchor='w', padx=20, pady=(20, 8))

        loteria_combo = ttk.Combobox(loteria_card, textvariable=self.app.loteria,
                                     values=['Mega-Sena', 'Loto Fácil'], state='readonly',
                                     style='Modern.TCombobox')
        loteria_combo.pack(fill='x', padx=20, pady=(0, 20))
        loteria_combo.bind('<<ComboboxSelected>>', self.atualizar_dezenas)

        # Card de configurações
        config_card = tk.LabelFrame(left_frame, text="⚙️ Configurações",
                                    bg=self.colors['bg_card'], fg=self.colors['accent_primary'],
                                    font=('Segoe UI', 12, 'bold'), relief='solid', bd=1)
        config_card.pack(fill='x', pady=(0, 20))

        # Método de geração
        tk.Label(config_card, text="Método de geração:", bg=self.colors['bg_card'],
                 fg=self.colors['text_secondary'], font=('Segoe UI', 10)).pack(
            anchor='w', padx=20, pady=(20, 8))

        metodo_combo = ttk.Combobox(config_card, textvariable=self.app.metodo,
                                    values=['Top Frequentes',
                                            'Probabilistico'],
                                    state='readonly', style='Modern.TCombobox')
        metodo_combo.pack(fill='x', padx=20, pady=(0, 20))

        # Número de dezenas
        tk.Label(config_card, text="Número de dezenas:", bg=self.colors['bg_card'],
                 fg=self.colors['text_secondary'], font=('Segoe UI', 10)).pack(
            anchor='w', padx=20, pady=(0, 8))

        dezenas_frame = tk.Frame(config_card, bg=self.colors['bg_card'])
        dezenas_frame.pack(fill='x', padx=20, pady=(0, 20))

        self.dezenas_scale = tk.Scale(dezenas_frame, from_=6, to=20, orient=tk.HORIZONTAL,
                                      variable=self.app.num_dezenas, bg=self.colors['bg_card'],
                                      fg=self.colors['text_primary'], highlightthickness=0,
                                      troughcolor=self.colors['bg_input'],
                                      activebackground=self.colors['accent_primary'],
                                      command=self.atualizar_label_dezenas,
                                      font=('Segoe UI', 9))
        self.dezenas_scale.pack(side='left', fill='x', expand=True)

        self.dezenas_value_label = tk.Label(dezenas_frame, text="6 dezenas",
                                            bg=self.colors['bg_card'], fg=self.colors['text_accent'],
                                            font=('Segoe UI', 10, 'bold'))
        self.dezenas_value_label.pack(side='right', padx=(15, 0))

        # Checkbox de bolão
        bolao_check = tk.Checkbutton(config_card, text="🤝 Gerar Bolão?",
                                     variable=self.app.is_bolao, command=self.toggle_bolao,
                                     bg=self.colors['bg_card'], fg=self.colors['text_primary'],
                                     selectcolor=self.colors['bg_input'],
                                     activebackground=self.colors['bg_card'],
                                     activeforeground=self.colors['accent_primary'],
                                     font=('Segoe UI', 10, 'bold'),
                                     highlightthickness=0, bd=0)
        bolao_check.pack(anchor='w', padx=20, pady=(0, 20))

        # Frame do bolão (inicialmente oculto)
        self.bolao_frame = tk.Frame(config_card, bg=self.colors['bg_card'])

        tk.Label(self.bolao_frame, text="Jogos no bolão:", bg=self.colors['bg_card'],
                 fg=self.colors['text_secondary'], font=('Segoe UI', 10)).pack(
            anchor='w', padx=20, pady=(0, 8))

        jogos_entry = tk.Entry(self.bolao_frame, textvariable=self.app.num_jogos,
                               bg=self.colors['bg_input'], fg=self.colors['text_primary'],
                               insertbackground=self.colors['text_primary'], relief='solid',
                               font=('Segoe UI', 10), bd=1,
                               highlightthickness=1, highlightcolor=self.colors['accent_primary'])
        jogos_entry.pack(fill='x', padx=20, pady=(0, 15))

        tk.Label(self.bolao_frame, text="Participantes:", bg=self.colors['bg_card'],
                 fg=self.colors['text_secondary'], font=('Segoe UI', 10)).pack(
            anchor='w', padx=20, pady=(0, 8))

        participantes_entry = tk.Entry(self.bolao_frame, textvariable=self.app.num_participantes,
                                       bg=self.colors['bg_input'], fg=self.colors['text_primary'],
                                       insertbackground=self.colors['text_primary'], relief='solid',
                                       font=('Segoe UI', 10), bd=1,
                                       highlightthickness=1, highlightcolor=self.colors['accent_primary'])
        participantes_entry.pack(fill='x', padx=20, pady=(0, 20))

        # Botões de ação
        buttons_frame = tk.Frame(left_frame, bg=self.colors['bg_primary'])
        buttons_frame.pack(fill='x', pady=(0, 20))

        # Botão principal de gerar
        generate_btn = tk.Button(buttons_frame, text="🎲 Gerar Números",
                                 command=self.gerar_jogos, bg=self.colors['accent_primary'],
                                 fg=self.colors['bg_primary'], font=(
                                     'Segoe UI', 12, 'bold'),
                                 relief='flat', cursor='hand2', bd=0, pady=15,
                                 activebackground=self.colors['accent_tertiary'])
        generate_btn.pack(fill='x', pady=(0, 15))

        # Botão de salvar (inicialmente oculto)
        self.salvar_button = tk.Button(buttons_frame, text="💾 Salvar Jogo",
                                       command=self.criar_janela_salvar,
                                       bg=self.colors['accent_tertiary'],
                                       fg=self.colors['bg_primary'],
                                       font=('Segoe UI', 11, 'bold'), relief='flat',
                                       cursor='hand2', bd=0, pady=12,
                                       activebackground='#3fb8b0')

        # Botões secundários
        freq_btn = tk.Button(buttons_frame, text="📊 Ver Frequências",
                             command=self.mostrar_grafico, bg=self.colors['accent_info'],
                             fg='white', font=('Segoe UI', 11, 'bold'),
                             relief='flat', cursor='hand2', bd=0, pady=12,
                             activebackground='#5aa3ff')
        freq_btn.pack(fill='x', pady=(15, 0))

        hist_btn = tk.Button(buttons_frame, text="📚 Ver Histórico",
                             command=self.abrir_historico, bg=self.colors['accent_info'],
                             fg='white', font=('Segoe UI', 11, 'bold'),
                             relief='flat', cursor='hand2', bd=0, pady=12,
                             activebackground='#5aa3ff')
        hist_btn.pack(fill='x', pady=(15, 0))

        update_btn = tk.Button(buttons_frame, text="🔄 Verificar Atualizações",
                               command=lambda: self.app.update_manager.check_for_updates(
                                   True),
                               bg=self.colors['accent_info'], fg='white',
                               font=('Segoe UI', 11, 'bold'), relief='flat',
                               cursor='hand2', bd=0, pady=12,
                               activebackground='#5aa3ff')
        update_btn.pack(fill='x', pady=(15, 0))

        # Painel direito
        right_frame = tk.Frame(content_frame, bg=self.colors['bg_primary'])
        right_frame.pack(side='right', fill='both', expand=True)

        # Card de informações
        info_card = tk.LabelFrame(right_frame, text="ℹ️ Informações",
                                  bg=self.colors['bg_card'], fg=self.colors['accent_primary'],
                                  font=('Segoe UI', 12, 'bold'), relief='solid', bd=1)
        info_card.pack(fill='x', pady=(0, 20))

        self.info_text = tk.Text(info_card, height=10, width=55, bg=self.colors['bg_input'],
                                 fg=self.colors['text_primary'], font=(
                                     'Segoe UI', 10),
                                 relief='flat', wrap='word', insertbackground=self.colors['text_primary'],
                                 highlightthickness=0)
        self.info_text.pack(fill='x', padx=20, pady=20)

        # Card de custos e resumo
        resultado_card = tk.LabelFrame(right_frame, text="💰 Custos e Resumo",
                                       bg=self.colors['bg_card'], fg=self.colors['accent_primary'],
                                       font=('Segoe UI', 12, 'bold'), relief='solid', bd=1)
        resultado_card.pack(fill='x', pady=(0, 20))

        self.resultado_text = tk.Text(resultado_card, height=8, width=55, bg=self.colors['bg_input'],
                                      fg=self.colors['text_primary'], font=(
                                          'Consolas', 10),
                                      relief='flat', wrap='word',
                                      insertbackground=self.colors['text_primary'],
                                      highlightthickness=0)
        self.resultado_text.pack(fill='x', padx=20, pady=20)

        # Card de números gerados
        numeros_card = tk.LabelFrame(right_frame, text="🎯 Números Gerados",
                                     bg=self.colors['bg_card'], fg=self.colors['accent_primary'],
                                     font=('Segoe UI', 12, 'bold'), relief='solid', bd=1)
        numeros_card.pack(fill='both', expand=True)

        canvas_container = tk.Frame(numeros_card, bg=self.colors['bg_card'])
        canvas_container.pack(fill='both', expand=True, padx=20, pady=20)

        self.canvas_scroll = tk.Canvas(canvas_container, bg=self.colors['bg_secondary'],
                                       highlightthickness=0)
        scrollbar = ttk.Scrollbar(canvas_container, orient="vertical",
                                  command=self.canvas_scroll.yview)

        self.canvas_frame = tk.Frame(
            self.canvas_scroll, bg=self.colors['bg_secondary'])
        self.canvas_frame.bind("<Configure>", lambda e: self.canvas_scroll.configure(
            scrollregion=self.canvas_scroll.bbox("all")))

        self.canvas_scroll.create_window(
            (0, 0), window=self.canvas_frame, anchor="nw")
        self.canvas_scroll.configure(yscrollcommand=scrollbar.set)

        self.canvas_scroll.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
