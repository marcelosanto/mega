import tkinter as tk
from tkinter import ttk, messagebox
import pandas as pd
import numpy as np
from math import comb
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import json
from config import LOTTERY_CONFIG


class LoteriaUI:
    def __init__(self, app):
        self.app = app
        self.config_loteria = LOTTERY_CONFIG
        self.configurar_estilo()
        self.criar_interface()

    def configurar_estilo(self):
        style = ttk.Style()
        style.theme_use('clam')
        bg_color = '#1e1e2e'
        fg_color = '#cdd6f4'
        accent_color = '#f38ba8'
        secondary_color = '#313244'
        style.configure('Title.TLabel', background=bg_color,
                        foreground='#fab387', font=('Segoe UI', 16, 'bold'))
        style.configure('Subtitle.TLabel', background=bg_color,
                        foreground=fg_color, font=('Segoe UI', 11, 'bold'))
        style.configure('Modern.TLabel', background=bg_color,
                        foreground=fg_color, font=('Segoe UI', 10))
        style.configure('Modern.TCombobox', fieldbackground=secondary_color,
                        background=secondary_color, foreground=fg_color, borderwidth=0, relief='flat')
        style.configure('Modern.TButton', background=accent_color, foreground='white',
                        borderwidth=0, focuscolor='none', font=('Segoe UI', 10, 'bold'))
        style.map('Modern.TButton', background=[
                  ('active', '#f5c2e7'), ('pressed', '#f38ba8')])
        style.configure('Secondary.TButton', background='#74c0fc', foreground='white',
                        borderwidth=0, focuscolor='none', font=('Segoe UI', 10, 'bold'))
        style.map('Secondary.TButton', background=[
                  ('active', '#91d5ff'), ('pressed', '#74c0fc')])
        style.configure('Success.TButton', background='#a6e3a1', foreground='#1e1e2e',
                        borderwidth=0, focuscolor='none', font=('Segoe UI', 10, 'bold'))
        style.map('Success.TButton', background=[
                  ('active', '#b8e8b1'), ('pressed', '#a6e3a1')])

    def carregar_dados(self):
        loteria = self.app.loteria.get()
        config = self.config_loteria[loteria]
        try:
            xlsx_path = self.app.update_manager.get_resource_path(
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
                           bg='#1e1e2e', highlightthickness=0)
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
            jogo_frame = tk.Frame(
                self.canvas_frame, bg='#313244', relief='raised', bd=2)
            jogo_frame.pack(fill='x', padx=10, pady=5)
            tk.Label(jogo_frame, text=f"🎯 Jogo {idx}", bg='#313244', fg='#fab387',
                     font=('Segoe UI', 12, 'bold')).pack(anchor='w', padx=10, pady=(10, 5))
            bolas_frame = tk.Frame(jogo_frame, bg='#313244')
            bolas_frame.pack(fill='x', padx=10, pady=(0, 10))
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
        plt.style.use('dark_background')
        fig, ax = plt.subplots(figsize=(10, 6))
        fig.patch.set_facecolor('#1e1e2e')
        ax.set_facecolor('#313244')
        bars = ax.bar(range(1, loteria_config['num_total'] + 1), self.app.freq,
                      color=loteria_config['cor_bola'], alpha=0.8)
        ax.set_xlabel("Números", color='#cdd6f4', fontsize=12)
        ax.set_ylabel("Frequência", color='#cdd6f4', fontsize=12)
        ax.set_title(f"📊 Frequência dos Números - {self.app.loteria.get()}",
                     color='#fab387', fontsize=14, fontweight='bold')
        ax.tick_params(colors='#cdd6f4')
        ax.grid(True, alpha=0.3)
        top_5_indices = np.argsort(self.app.freq)[-5:]
        for idx in top_5_indices:
            bars[idx].set_color('#f38ba8')
        plt.tight_layout()
        grafico_window = tk.Toplevel(self.app.root)
        grafico_window.title("📊 Gráfico de Frequências")
        grafico_window.configure(bg='#1e1e2e')
        grafico_window.geometry("1000x700")
        canvas = FigureCanvasTkAgg(fig, master=grafico_window)
        canvas.draw()
        canvas.get_tk_widget().pack(fill='both', expand=True)
        plt.close(fig)

    def criar_janela_salvar(self):
        save_window = tk.Toplevel(self.app.root)
        save_window.title("💾 Salvar Jogo")
        save_window.geometry("400x300")
        save_window.configure(bg='#1e1e2e')
        save_window.transient(self.app.root)
        save_window.grab_set()
        save_window.geometry(
            "+%d+%d" % (self.app.root.winfo_rootx() + 50, self.app.root.winfo_rooty() + 50))
        title_label = tk.Label(save_window, text="💾 Salvar Jogo",
                               bg='#1e1e2e', fg='#fab387', font=('Segoe UI', 14, 'bold'))
        title_label.pack(pady=(20, 10))
        info_frame = tk.Frame(save_window, bg='#313244', relief='raised', bd=1)
        info_frame.pack(fill='x', padx=20, pady=(0, 20))
        info_text = f"""🎲 {self.app.loteria.get()}
📊 {len(self.app.jogos_atuais)} jogo(s) gerado(s)
🎯 {self.app.num_dezenas.get()} dezenas cada
💰 R$ {self.calcular_preco(self.app.num_dezenas.get()) * len(self.app.jogos_atuais):.2f}"""
        tk.Label(info_frame, text=info_text, bg='#313244', fg='#cdd6f4',
                 font=('Segoe UI', 10), justify='left').pack(padx=15, pady=15)
        tk.Label(save_window, text="📝 Observações (opcional):", bg='#1e1e2e',
                 fg='#cdd6f4', font=('Segoe UI', 11, 'bold')).pack(anchor='w', padx=20)
        obs_text = tk.Text(save_window, height=4, width=40, bg='#45475a', fg='#cdd6f4', font=(
            'Segoe UI', 10), relief='flat', wrap='word', insertbackground='#cdd6f4')
        obs_text.pack(fill='x', padx=20, pady=(5, 20))
        buttons_frame = tk.Frame(save_window, bg='#1e1e2e')
        buttons_frame.pack(fill='x', padx=20, pady=(0, 20))

        def confirmar_save():
            observacoes = obs_text.get("1.0", tk.END).strip()
            if self.app.db_manager.salvar_no_banco(self.app, observacoes):
                save_window.destroy()
        tk.Button(buttons_frame, text="💾 Salvar", command=confirmar_save, bg='#a6e3a1', fg='#1e1e2e', font=(
            'Segoe UI', 10, 'bold'), relief='flat', cursor='hand2').pack(side='left', fill='x', expand=True, padx=(0, 10))
        tk.Button(buttons_frame, text="❌ Cancelar", command=save_window.destroy, bg='#f38ba8', fg='white', font=(
            'Segoe UI', 10, 'bold'), relief='flat', cursor='hand2').pack(side='right', fill='x', expand=True)

    def abrir_historico(self):
        hist_window = tk.Toplevel(self.app.root)
        hist_window.title("📚 Histórico de Jogos")
        hist_window.geometry("1000x600")
        hist_window.configure(bg='#1e1e2e')
        title_label = tk.Label(hist_window, text="📚 Histórico de Jogos Salvos",
                               bg='#1e1e2e', fg='#fab387', font=('Segoe UI', 16, 'bold'))
        title_label.pack(pady=(20, 10))
        filter_frame = tk.Frame(hist_window, bg='#313244')
        filter_frame.pack(fill='x', padx=20, pady=(0, 20))
        tk.Label(filter_frame, text="Filtrar por loteria:", bg='#313244', fg='#cdd6f4', font=(
            'Segoe UI', 10)).pack(side='left', padx=(15, 5), pady=15)
        filter_var = tk.StringVar(value="Todas")
        filter_combo = ttk.Combobox(filter_frame, textvariable=filter_var, values=[
                                    'Todas', 'Mega-Sena', 'Loto Fácil'], state='readonly', width=15)
        filter_combo.pack(side='left', padx=(0, 15), pady=15)

        def atualizar_lista():
            self.app.db_manager.carregar_historico(tree, filter_var.get())
        filter_combo.bind('<<ComboboxSelected>>', lambda e: atualizar_lista())
        tk.Button(filter_frame, text="🔄 Atualizar", command=atualizar_lista, bg='#74c0fc', fg='white', font=(
            'Segoe UI', 9, 'bold'), relief='flat', cursor='hand2').pack(side='left', padx=(10, 15), pady=15)
        tree_frame = tk.Frame(hist_window, bg='#1e1e2e')
        tree_frame.pack(fill='both', expand=True, padx=20, pady=(0, 20))
        tree_scroll_y = ttk.Scrollbar(tree_frame, orient="vertical")
        tree_scroll_x = ttk.Scrollbar(tree_frame, orient="horizontal")
        tree = ttk.Treeview(tree_frame, yscrollcommand=tree_scroll_y.set,
                            xscrollcommand=tree_scroll_x.set, height=15)
        tree['columns'] = ("ID", "Loteria", "Método",
                           "Dezenas", "Jogos", "Preço", "Data", "Obs")
        tree['show'] = 'headings'
        tree.heading("ID", text="ID")
        tree.heading("Loteria", text="Loteria")
        tree.heading("Método", text="Método")
        tree.heading("Dezenas", text="Dezenas")
        tree.heading("Jogos", text="Jogos")
        tree.heading("Preço", text="Preço (R$)")
        tree.heading("Data", text="Data")
        tree.heading("Obs", text="Observações")
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
        buttons_frame = tk.Frame(hist_window, bg='#1e1e2e')
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
        tk.Button(buttons_frame, text="👁️ Ver Detalhes", command=ver_detalhes, bg='#74c0fc', fg='white', font=(
            'Segoe UI', 10, 'bold'), relief='flat', cursor='hand2').pack(side='left', padx=(0, 10))
        tk.Button(buttons_frame, text="🗑️ Excluir", command=excluir_jogo, bg='#f38ba8', fg='white', font=(
            'Segoe UI', 10, 'bold'), relief='flat', cursor='hand2').pack(side='left')
        self.app.db_manager.carregar_historico(tree, "Todas")

    def mostrar_detalhes_jogo(self, jogo_id, jogo):
        det_window = tk.Toplevel(self.app.root)
        det_window.title(f"🔍 Detalhes do Jogo #{jogo_id}")
        det_window.geometry("600x500")
        det_window.configure(bg='#1e1e2e')
        title_label = tk.Label(
            det_window, text=f"🔍 Jogo #{jogo_id} - {jogo[1]}", bg='#1e1e2e', fg='#fab387', font=('Segoe UI', 16, 'bold'))
        title_label.pack(pady=(20, 20))
        main_frame = tk.Frame(det_window, bg='#313244', relief='raised', bd=2)
        main_frame.pack(fill='both', expand=True, padx=20, pady=(0, 20))
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
{jogo[10] if jogo[10] else 'Nenhuma observação'}

🎯 NÚMEROS JOGADOS:"""
        info_label = tk.Label(main_frame, text=info_text, bg='#313244',
                              fg='#cdd6f4', font=('Segoe UI', 11), justify='left')
        info_label.pack(anchor='w', padx=20, pady=20)
        numeros_frame = tk.Frame(main_frame, bg='#313244')
        numeros_frame.pack(fill='x', padx=20, pady=(0, 20))
        try:
            numeros_jogos = json.loads(jogo[3])
            config = self.config_loteria[jogo[1]]
            for idx, numeros in enumerate(numeros_jogos, 1):
                jogo_frame = tk.Frame(
                    numeros_frame, bg='#45475a', relief='raised', bd=1)
                jogo_frame.pack(fill='x', pady=5)
                tk.Label(jogo_frame, text=f"Jogo {idx}:", bg='#45475a', fg='#fab387', font=(
                    'Segoe UI', 10, 'bold')).pack(anchor='w', padx=10, pady=(10, 5))
                bolas_frame = tk.Frame(jogo_frame, bg='#45475a')
                bolas_frame.pack(fill='x', padx=10, pady=(0, 10))
                for num in numeros:
                    bola = self.criar_bola_canvas(
                        bolas_frame, num, config['cor_bola'], 25)
                    bola.pack(side='left', padx=2)
        except Exception as e:
            tk.Label(
                numeros_frame, text=f"Erro ao carregar números: {e}", bg='#313244', fg='#f38ba8').pack()

    def criar_interface(self):
        main_container = tk.Frame(self.app.root, bg='#1e1e2e')
        main_container.pack(fill='both', expand=True, padx=20, pady=20)
        title_label = ttk.Label(
            main_container, text="🎯 Gerador de Números para Loterias", style='Title.TLabel')
        title_label.pack(pady=(0, 20))
        content_frame = tk.Frame(main_container, bg='#1e1e2e')
        content_frame.pack(fill='both', expand=True)
        left_frame = tk.Frame(content_frame, bg='#1e1e2e')
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
        config_card = tk.LabelFrame(left_frame, text="⚙️ Configurações",
                                    bg='#313244', fg='#fab387', font=('Segoe UI', 11, 'bold'))
        config_card.pack(fill='x', pady=(0, 15))
        ttk.Label(config_card, text="Método de geração:", style='Modern.TLabel').pack(
            anchor='w', padx=15, pady=(15, 5))
        metodo_combo = ttk.Combobox(config_card, textvariable=self.app.metodo, values=[
                                    'Top Frequentes', 'Probabilístico'], state='readonly', style='Modern.TCombobox')
        metodo_combo.pack(fill='x', padx=15, pady=(0, 15))
        ttk.Label(config_card, text="Número de dezenas:", style='Modern.TLabel').pack(
            anchor='w', padx=15, pady=(0, 5))
        dezenas_frame = tk.Frame(config_card, bg='#313244')
        dezenas_frame.pack(fill='x', padx=15, pady=(0, 15))
        self.dezenas_scale = tk.Scale(dezenas_frame, from_=6, to=20, orient=tk.HORIZONTAL, variable=self.app.num_dezenas, bg='#313244',
                                      fg='#cdd6f4', highlightthickness=0, troughcolor='#45475a', activebackground='#f38ba8', command=self.atualizar_label_dezenas)
        self.dezenas_scale.pack(side='left', fill='x', expand=True)
        self.dezenas_value_label = ttk.Label(
            dezenas_frame, text="6 dezenas", style='Modern.TLabel')
        self.dezenas_value_label.pack(side='right', padx=(10, 0))
        bolao_check = tk.Checkbutton(config_card, text="🤝 Gerar Bolão?", variable=self.app.is_bolao, command=self.toggle_bolao, bg='#313244',
                                     fg='#cdd6f4', selectcolor='#45475a', activebackground='#313244', activeforeground='#f38ba8', font=('Segoe UI', 10, 'bold'))
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
        buttons_frame = tk.Frame(left_frame, bg='#1e1e2e')
        buttons_frame.pack(fill='x', pady=(0, 15))
        ttk.Button(buttons_frame, text="🎲 Gerar Números", command=self.gerar_jogos,
                   style='Modern.TButton').pack(fill='x', pady=(0, 10))
        self.salvar_button = ttk.Button(
            buttons_frame, text="💾 Salvar Jogo", command=self.criar_janela_salvar, style='Success.TButton')
        ttk.Button(buttons_frame, text="📊 Ver Frequências", command=self.mostrar_grafico,
                   style='Secondary.TButton').pack(fill='x', pady=(10, 0))
        ttk.Button(buttons_frame, text="📚 Ver Histórico", command=self.abrir_historico,
                   style='Secondary.TButton').pack(fill='x', pady=(10, 0))
        ttk.Button(buttons_frame, text="🔄 Verificar Atualizações", command=lambda: self.app.update_manager.check_for_updates(
            True), style='Secondary.TButton').pack(fill='x', pady=(10, 0))
        right_frame = tk.Frame(content_frame, bg='#1e1e2e')
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
