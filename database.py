import sqlite3
from tkinter import messagebox
import json


class DatabaseManager:
    def __init__(self):
        self.conn = sqlite3.connect('loteria_historico.db')
        self.cursor = self.conn.cursor()
        self.init_database()

    def init_database(self):
        try:
            self.cursor.execute('''
                CREATE TABLE IF NOT EXISTS jogos (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    loteria TEXT NOT NULL,
                    metodo TEXT NOT NULL,
                    numeros TEXT NOT NULL,
                    num_dezenas INTEGER NOT NULL,
                    preco REAL NOT NULL,
                    is_bolao BOOLEAN NOT NULL,
                    num_jogos INTEGER DEFAULT 1,
                    num_participantes INTEGER DEFAULT 1,
                    data_criacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    observacoes TEXT
                )
            ''')
            self.conn.commit()
        except sqlite3.Error as e:
            messagebox.showerror(
                "❌ Erro de Banco", f"Erro ao inicializar banco de dados: {e}")

    def salvar_no_banco(self, app, observacoes=""):
        try:
            numeros_json = json.dumps(app.jogos_atuais)
            preco = app.ui.calcular_preco(
                app.num_dezenas.get()) * len(app.jogos_atuais)
            self.cursor.execute('''
                INSERT INTO jogos 
                (loteria, metodo, numeros, num_dezenas, preco, is_bolao, 
                 num_jogos, num_participantes, observacoes)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                app.loteria.get(),
                app.metodo.get(),
                numeros_json,
                app.num_dezenas.get(),
                preco,
                app.is_bolao.get(),
                len(app.jogos_atuais),
                app.num_participantes.get(),
                observacoes
            ))
            self.conn.commit()
            messagebox.showinfo(
                "✅ Sucesso", "Jogo salvo com sucesso no histórico!")
            print("DEBUG: Tentando salvar jogo...", app.jogos_atuais)
            return True
        except sqlite3.Error as e:
            messagebox.showerror("❌ Erro", f"Erro ao salvar jogo: {e}")
            return False

    def carregar_historico(self, tree, filtro_loteria="Todas"):
        for item in tree.get_children():
            tree.delete(item)
        try:
            query = '''
                SELECT id, loteria, metodo, numeros, num_dezenas, preco, 
                       is_bolao, num_jogos, num_participantes, 
                       datetime(data_criacao, 'localtime'), observacoes
                FROM jogos
            '''
            params = []
            if filtro_loteria != "Todas":
                query += " WHERE loteria = ?"
                params.append(filtro_loteria)
            query += " ORDER BY data_criacao DESC"
            self.cursor.execute(query, params)
            jogos = self.cursor.fetchall()
            for jogo in jogos:
                jogo_id, loteria, metodo, _, num_dezenas, preco, _, num_jogos, _, data_criacao, observacoes = jogo
                from datetime import datetime
                try:
                    data_obj = datetime.strptime(
                        data_criacao, '%Y-%m-%d %H:%M:%S')
                    data_formatada = data_obj.strftime('%d/%m/%Y %H:%M')
                except:
                    data_formatada = data_criacao
                tree.insert("", "end", values=(
                    jogo_id, loteria, metodo, f"{num_dezenas} nums",
                    num_jogos, f"R$ {preco:.2f}", data_formatada,
                    observacoes[:30] +
                    "..." if len(str(observacoes)) > 30 else observacoes
                ))
        except sqlite3.Error as e:
            messagebox.showerror("❌ Erro", f"Erro ao carregar histórico: {e}")

    def mostrar_detalhes_jogo(self, app, jogo_id):
        try:
            self.cursor.execute('SELECT * FROM jogos WHERE id = ?', (jogo_id,))
            jogo = self.cursor.fetchone()
            if not jogo:
                messagebox.showerror("❌ Erro", "Jogo não encontrado!")
                return
            app.ui.mostrar_detalhes_jogo(jogo_id, jogo)
        except sqlite3.Error as e:
            messagebox.showerror("❌ Erro", f"Erro ao carregar detalhes: {e}")

    def excluir_jogo(self, jogo_id):
        try:
            self.cursor.execute('DELETE FROM jogos WHERE id = ?', (jogo_id,))
            self.conn.commit()
            messagebox.showinfo("✅ Sucesso", "Jogo excluído com sucesso!")
        except sqlite3.Error as e:
            messagebox.showerror("❌ Erro", f"Erro ao excluir jogo: {e}")

    def close(self):
        if hasattr(self, 'conn'):
            self.conn.close()
