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
        # Explicitly initialize default loteria
        self.app.loteria.set("Mega-Sena")
        self.atualizar_dezenas()

    def configurar_estilo(self):
        style = ttk.Style()
        style.theme_use('clam')
        # Color scheme: Softer dark theme with high contrast
        bg_color = '#181825'  # Navy dark background
        fg_color = '#cdd6f4'  # Light text for readability
        accent_color = '#a6e3a1'  # Vibrant green for lottery theme
        secondary_color = '#313244'  # Blue-gray for cards
        style.configure('Title.TLabel', background=bg_color,
                        foreground='#fab387', font=('Segoe UI', 16, 'bold'))
        style.configure('Subtitle.TLabel', background=bg_color,
                        foreground=fg_color, font=('Segoe UI', 11, 'bold'))
        style.configure('Modern.TLabel', background=bg_color,
                        foreground=fg_color, font=('Segoe UI', 10))
        # Combobox: Lighter background and white text for contrast
        style.configure('Modern.TCombobox', fieldbackground='#45475a',
                        background=secondary_color, foreground='#ffffff',
                        selectbackground='#a6e3a1', selectforeground='#1e1e2e',
                        borderwidth=0, relief='flat')
        style.map('Modern.TCombobox', fieldbackground=[('readonly', '#45475a')],
                  background=[('readonly', '#45475a')],
                  foreground=[('readonly', '#ffffff')])
        # Primary button: Green for action
        style.configure('Modern.TButton', background=accent_color, foreground='#1e1e2e',
                        borderwidth=0, focuscolor='none', font=('Segoe UI', 10, 'bold'))
        style.map('Modern.TButton', background=[
                  ('active', '#b8e8b1'), ('pressed', '#a6e3a1')])
        # Secondary: Calm blue
        style.configure('Secondary.TButton', background='#89b4fa', foreground='#1e1e2e',
                        borderwidth=0, focuscolor='none', font=('Segoe UI', 10, 'bold'))
        style.map('Secondary.TButton', background=[
                  ('active', '#a4c1f9'), ('pressed', '#89b4fa')])
        # Success: Cyan for save actions
        style.configure('Success.TButton', background='#74c7ec', foreground='#1e1e2e',
                        borderwidth=0, focuscolor='none', font=('Segoe UI', 10, 'bold'))
        style.map('Success.TButton', background=[
                  ('active', '#89dceb'), ('pressed', '#74c7ec')])

    def carregar_dados(self):
        loteria = self.app.loteria.get()
        config = self.config_loteria[loteria]
        try:
            xlsx_path = get_resource_path(
                config['caminho_xlsx'])
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
                           bg='#181825', highlightthickness=0)
        canvas.create_oval(5, 5, tamanho*2-5, tamanho*2-5,
                           fill='#11111b', outline='')
        canvas.create_oval(2, 2, tamanho*2-8, tamanho*2-8,
                           fill=cor_base, outline='white', width=2)
        canvas.create_oval(8, 8, tamanho-5, tamanho-5,
                           fill='white', outline='', stipple='gray50')
        canvas.create_text(tamanho-3, tamanho-3, text=f"{numero:02d}",
                           fill='white', font=('Segoe UI', 12, 'bold'))
        return canvas

    def gerar_jogos(self):
        """Generate lottery numbers and update the UI."""
        try:
            # Clear previous results
            for widget in self.canvas_frame.winfo_children():
                widget.destroy()
            self.resultado_text.delete(1.0, tk.END)
            self.app.jogos_atuais = []

            num_jogos = self.app.num_jogos.get() if self.app.is_bolao.get() else 1
            num_dezenas = self.app.num_dezenas.get()
            metodo = self.app.metodo.get().lower().replace(" ", "_")
            loteria = self.app.loteria.get()
            config = self.config_loteria[loteria]
            total_preco = 0

            # Generate games
            for i in range(num_jogos):
                numeros = self.gerar_numeros(metodo, num_dezenas)
                if not numeros:
                    return
                self.app.jogos_atuais.append(numeros)
                # Display game in canvas
                jogo_frame = tk.Frame(self.canvas_frame, bg='#45475a')
                jogo_frame.pack(fill='x', padx=10, pady=(10, 5))
                ttk.Label(
                    jogo_frame, text=f"Jogo {i+1}", style='Modern.TLabel').pack(anchor='w')
                bolas_frame = tk.Frame(jogo_frame, bg='#45475a')
                bolas_frame.pack(fill='x', padx=10, pady=(0, 10))
                for num in numeros:
                    bola = self.criar_bola_canvas(
                        bolas_frame, num, config['cor_bola'], 25)
                    bola.pack(side='left', padx=2)
                total_preco += self.calcular_preco(num_dezenas)

            # Update result text
            num_participantes = self.app.num_participantes.get() if self.app.is_bolao.get() else 1
            preco_por_participante = total_preco / max(num_participantes, 1)
            resultado = f"""🎯 Resumo:
• Loteria: {loteria}
• Método: {self.app.metodo.get()}
• Dezenas por jogo: {num_dezenas}
• Total de jogos: {num_jogos}
• Custo total: R$ {total_preco:.2f}
• Participantes: {num_participantes}
• Custo por participante: R$ {preco_por_participante:.2f}
"""
            self.resultado_text.delete(1.0, tk.END)
            self.resultado_text.insert(tk.END, resultado)
            # Enable save button
            self.salvar_button.config(state='normal')
        except Exception as e:
            messagebox.showerror("❌ Erro", f"Erro ao gerar jogos: {e}")

    def criar_janela_salvar(self):
        """Placeholder for save window (implement if needed)."""
        try:
            if not self.app.jogos_atuais:
                messagebox.showwarning(
                    "⚠️ Atenção", "Nenhum jogo gerado para salvar!")
                return
            observacoes = ""
            if self.app.db_manager.salvar_no_banco(self.app, observacoes):
                self.salvar_button.config(state='disabled')
        except Exception as e:
            messagebox.showerror("❌ Erro", f"Erro ao salvar: {e}")

    def mostrar_grafico(self):
        """Placeholder for frequency graph (implement if needed)."""
        pass

    def abrir_historico(self):
        """Placeholder for history window (implement if needed)."""
        pass

    def criar_interface(self):
        main_container = tk.Frame(self.app.root, bg='#181825')
        main_container.pack(fill='both', expand=True, padx=20, pady=20)
        title_label = ttk.Label(
            main_container, text="🎯 Gerador de Números para Loterias", style='Title.TLabel')
        title_label.pack(pady=(0, 20))
        content_frame = tk.Frame(main_container, bg='#181825')
        content_frame.pack(fill='both', expand=True)
        left_frame = tk.Frame(content_frame, bg='#181825')
        left_frame.pack(side='left', fill='y', padx=(0, 20))
        loteria_card = tk.LabelFrame(
            left_frame, text="🎲 Loteria", bg='#313244', fg='#fab387', font=('Segoe UI', 11, 'bold'))
        loteria_card.pack(fill='x', pady=(0, 15))
        ttk.Label(loteria_card, text="Escolha a loteria:", style='Modern.TLabel').pack(
            anchor='w', padx=15, pady=(15, 5))
        loteria_combo = ttk.Combobox(loteria_card, textvariable=self.app.loteria, values=[
                                     'Mega-Sena', 'Loto Fácil'], state='readonly', style='Modern.TCombobox')
        loteria_combo.pack(fill='x', padx=15, pady=(0, 15))
        loteria_combo.bind('<<ComboboxSelected>>', self.atualizar_dezenas)
        loteria_combo.current(0)  # Selects "Mega-Sena"

        config_card = tk.LabelFrame(left_frame, text="⚙️ Configurações",
                                    bg='#313244', fg='#fab387', font=('Segoe UI', 11, 'bold'))
        config_card.pack(fill='x', pady=(0, 15))
        ttk.Label(config_card, text="Método de geração:", style='Modern.TLabel').pack(
            anchor='w', padx=15, pady=(15, 5))
        metodo_combo = ttk.Combobox(config_card, textvariable=self.app.metodo, values=[
                                    'Top Frequentes', 'Probabilistico'], state='readonly', style='Modern.TCombobox')
        metodo_combo.pack(fill='x', padx=15, pady=(0, 15))
        ttk.Label(config_card, text="Número de dezenas:", style='Modern.TLabel').pack(
            anchor='w', padx=15, pady=(0, 5))
        dezenas_frame = tk.Frame(config_card, bg='#313244')
        dezenas_frame.pack(fill='x', padx=15, pady=(0, 15))
        self.dezenas_scale = tk.Scale(dezenas_frame, from_=6, to=20, orient=tk.HORIZONTAL, variable=self.app.num_dezenas, bg='#313244',
                                      fg='#cdd6f4', highlightthickness=0, troughcolor='#45475a', activebackground='#a6e3a1', command=self.atualizar_label_dezenas)
        self.dezenas_scale.pack(side='left', fill='x', expand=True)
        self.dezenas_value_label = ttk.Label(
            dezenas_frame, text="6 dezenas", style='Modern.TLabel')
        self.dezenas_value_label.pack(side='right', padx=(10, 0))
        bolao_check = tk.Checkbutton(config_card, text="🤝 Gerar Bolão?", variable=self.app.is_bolao, command=self.toggle_bolao, bg='#313244',
                                     fg='#cdd6f4', selectcolor='#45475a', activebackground='#313244', activeforeground='#a6e3a1', font=('Segoe UI', 10, 'bold'))
        bolao_check.pack(anchor='w', padx=15, pady=(0, 15))
        self.bolao_frame = tk.Frame(config_card, bg='#313244')
        tk.Label(self.bolao_frame, text="Jogos no bolão:", bg='#313244', fg='#cdd6f4', font=(
            'Segoe UI', 10)).pack(anchor='w', padx=15, pady=(0, 5))
        jogos_entry = tk.Entry(self.bolao_frame, textvariable=self.app.num_jogos, bg='#45475a',
                               fg='#cdd6f4', insertbackground='#cdd6f4', relief='flat', font=('Segoe UI', 10))
        jogos_entry.pack(fill='x', padx=15, pady=(0, 10))
        tk.Label(self.bolao_frame, text="Participantes:", bg='#313244', fg='#cdd6f4', font=(
            'Segoe UI', 10)).pack(anchor='w', padx=15, pady=(0, 5))
        participantes_entry = tk.Entry(self.bolao_frame, textvariable=self.app.num_participantes,
                                       bg='#45475a', fg='#cdd6f4', insertbackground='#cdd6f4', relief='flat', font=('Segoe UI', 10))
        participantes_entry.pack(fill='x', padx=15, pady=(0, 15))
        buttons_frame = tk.Frame(left_frame, bg='#181825')
        buttons_frame.pack(fill='x', pady=(0, 15))
        ttk.Button(buttons_frame, text="🎲 Gerar Números", command=self.gerar_jogos,
                   style='Modern.TButton').pack(fill='x', pady=(0, 10))
        self.salvar_button = ttk.Button(
            buttons_frame, text="💾 Salvar Jogo", command=self.criar_janela_salvar, style='Success.TButton')
        self.salvar_button.pack(fill='x', pady=(10, 0))
        ttk.Button(buttons_frame, text="📊 Ver Frequências", command=self.mostrar_grafico,
                   style='Secondary.TButton').pack(fill='x', pady=(10, 0))
        ttk.Button(buttons_frame, text="📚 Ver Histórico", command=self.abrir_historico,
                   style='Secondary.TButton').pack(fill='x', pady=(10, 0))
        ttk.Button(buttons_frame, text="🔄 Verificar Atualizações", command=lambda: self.app.update_manager.check_for_updates(
            True), style='Secondary.TButton').pack(fill='x', pady=(10, 0))
        right_frame = tk.Frame(content_frame, bg='#181825')
        right_frame.pack(side='right', fill='both', expand=True)
        info_card = tk.LabelFrame(right_frame, text="ℹ️ Informações",
                                  bg='#313244', fg='#fab387', font=('Segoe UI', 11, 'bold'))
        info_card.pack(fill='x', pady=(0, 15))
        self.info_text = tk.Text(info_card, height=12, width=50, bg='#45475a', fg='#cdd6f4', font=(
            'Segoe UI', 9), relief='flat', wrap='word', insertbackground='#cdd6f4')
        self.info_text.pack(fill='x', padx=15, pady=15)
        resultado_card = tk.LabelFrame(
            right_frame, text="💰 Custos e Resumo", bg='#313244', fg='#fab387', font=('Segoe UI', 11, 'bold'))
        resultado_card.pack(fill='x', pady=(0, 15))
        self.resultado_text = tk.Text(resultado_card, height=8, width=50, bg='#45475a', fg='#cdd6f4', font=(
            'Consolas', 10), relief='flat', wrap='word', insertbackground='#cdd6f4')
        self.resultado_text.pack(fill='x', padx=15, pady=15)
        numeros_card = tk.LabelFrame(right_frame, text="🎯 Números Gerados",
                                     bg='#313244', fg='#fab387', font=('Segoe UI', 11, 'bold'))
        numeros_card.pack(fill='both', expand=True)
        canvas_container = tk.Frame(numeros_card, bg='#313244')
        canvas_container.pack(fill='both', expand=True, padx=15, pady=15)
        self.canvas_scroll = tk.Canvas(
            canvas_container, bg='#45475a', highlightthickness=0)
        scrollbar = ttk.Scrollbar(
            canvas_container, orient="vertical", command=self.canvas_scroll.yview)
        self.canvas_frame = tk.Frame(self.canvas_scroll, bg='#45475a')
        self.canvas_frame.bind("<Configure>", lambda e: self.canvas_scroll.configure(
            scrollregion=self.canvas_scroll.bbox("all")))
        self.canvas_scroll.create_window(
            (0, 0), window=self.canvas_frame, anchor="nw")
        self.canvas_scroll.configure(yscrollcommand=scrollbar.set)
        self.canvas_scroll.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
