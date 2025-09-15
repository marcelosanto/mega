import sqlite3
import json
import os
from math import comb
from utils import get_resource_path
from config import LOTTERY_CONFIG


class DatabaseManager:
    def __init__(self):
        db_path = get_resource_path('loteria_historico.db')
        self.conn = sqlite3.connect(db_path, check_same_thread=False)
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
            print("DEBUG: Banco de dados inicializado com sucesso!")
        except sqlite3.Error as e:
            print(f"Erro ao inicializar banco de dados: {e}")

    def calcular_preco(self, loteria, num_dezenas):
        """Calcula o preço baseado na loteria e número de dezenas"""
        try:
            config = LOTTERY_CONFIG[loteria]
            if loteria == 'Mega-Sena':
                if num_dezenas < 6 or num_dezenas > 20:
                    return 0
                num_combs = comb(num_dezenas, 6)
            elif loteria == 'Loto Fácil':
                if num_dezenas < 15 or num_dezenas > 20:
                    return 0
                num_combs = comb(num_dezenas, 15)
            else:
                return 0
            return num_combs * config['preco_base']
        except Exception as e:
            print(f"Erro ao calcular preço: {e}")
            return 0

    def salvar_no_banco(self, app, observacoes=""):
        """Salva o jogo no banco - PARÂMETROS CORRIGIDOS"""
        try:
            if not app.jogos_atuais:
                print("DEBUG: Nenhum jogo para salvar!")
                return False

            # Obter valores corretos
            loteria = app.loteria.current.value
            metodo = app.metodo.current.value
            num_dezenas = int(app.num_dezenas.current.value)
            num_jogos = len(app.jogos_atuais)
            num_participantes = int(
                app.num_participantes.current.value) if app.is_bolao.current.value else 1
            is_bolao = app.is_bolao.current.value

            # Calcular preço total
            preco_por_jogo = self.calcular_preco(loteria, num_dezenas)
            preco_total = preco_por_jogo * num_jogos

            # Converter jogos para JSON
            numeros_json = json.dumps(app.jogos_atuais)

            print(
                f"DEBUG: Salvando jogo - Loteria: {loteria}, Jogos: {num_jogos}, Preço: R$ {preco_total:.2f}")

            # Inserir no banco
            self.cursor.execute('''
                INSERT INTO jogos
                (loteria, metodo, numeros, num_dezenas, preco, is_bolao,
                 num_jogos, num_participantes, observacoes)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                loteria,
                metodo,
                numeros_json,
                num_dezenas,
                preco_total,
                is_bolao,
                num_jogos,
                num_participantes,
                observacoes
            ))

            self.conn.commit()
            print("DEBUG: Jogo salvo com sucesso no banco!")
            return True

        except sqlite3.Error as e:
            print(f"Erro SQL ao salvar jogo: {e}")
            return False
        except Exception as e:
            print(f"Erro geral ao salvar jogo: {e}")
            return False

    def carregar_historico(self):
        """Carrega o histórico de jogos"""
        try:
            query = '''
                SELECT id, loteria, metodo, numeros, num_dezenas, preco,
                       is_bolao, num_jogos, num_participantes,
                       datetime(data_criacao, 'localtime'), observacoes
                FROM jogos ORDER BY data_criacao DESC
            '''
            self.cursor.execute(query)
            jogos = self.cursor.fetchall()
            print(f"DEBUG: Carregados {len(jogos)} jogos do histórico")
            return jogos
        except sqlite3.Error as e:
            print(f"Erro ao carregar histórico: {e}")
            return []

    def mostrar_detalhes_jogo(self, jogo_id):
        """Mostra detalhes de um jogo específico"""
        try:
            self.cursor.execute('SELECT * FROM jogos WHERE id = ?', (jogo_id,))
            jogo = self.cursor.fetchone()
            if jogo:
                print(f"DEBUG: Detalhes do jogo {jogo_id} carregados")
            else:
                print(f"DEBUG: Jogo {jogo_id} não encontrado")
            return jogo
        except sqlite3.Error as e:
            print(f"Erro ao carregar detalhes: {e}")
            return None

    def excluir_jogo(self, jogo_id):
        """Exclui um jogo do banco"""
        try:
            # Verificar se o jogo existe
            self.cursor.execute(
                'SELECT id FROM jogos WHERE id = ?', (jogo_id,))
            if not self.cursor.fetchone():
                print(f"DEBUG: Jogo {jogo_id} não existe")
                return False

            # Excluir o jogo
            self.cursor.execute('DELETE FROM jogos WHERE id = ?', (jogo_id,))
            self.conn.commit()
            print(f"DEBUG: Jogo {jogo_id} excluído com sucesso")
            return True
        except sqlite3.Error as e:
            print(f"Erro ao excluir jogo: {e}")
            return False

    def contar_jogos(self):
        """Conta o total de jogos salvos"""
        try:
            self.cursor.execute('SELECT COUNT(*) FROM jogos')
            count = self.cursor.fetchone()[0]
            print(f"DEBUG: Total de jogos no banco: {count}")
            return count
        except sqlite3.Error as e:
            print(f"Erro ao contar jogos: {e}")
            return 0

    def buscar_jogos(self, loteria=None, metodo=None, data_inicio=None, data_fim=None):
        """Busca jogos com filtros"""
        try:
            query = '''
                SELECT id, loteria, metodo, numeros, num_dezenas, preco,
                       is_bolao, num_jogos, num_participantes,
                       datetime(data_criacao, 'localtime'), observacoes
                FROM jogos WHERE 1=1
            '''
            params = []

            if loteria:
                query += ' AND loteria = ?'
                params.append(loteria)

            if metodo:
                query += ' AND metodo = ?'
                params.append(metodo)

            if data_inicio:
                query += ' AND date(data_criacao) >= ?'
                params.append(data_inicio)

            if data_fim:
                query += ' AND date(data_criacao) <= ?'
                params.append(data_fim)

            query += ' ORDER BY data_criacao DESC'

            self.cursor.execute(query, params)
            jogos = self.cursor.fetchall()
            print(f"DEBUG: Busca retornou {len(jogos)} jogos")
            return jogos
        except sqlite3.Error as e:
            print(f"Erro na busca: {e}")
            return []

    def get_estatisticas(self):
        """Retorna estatísticas dos jogos salvos"""
        try:
            stats = {}

            # Total de jogos
            self.cursor.execute('SELECT COUNT(*) FROM jogos')
            stats['total_jogos'] = self.cursor.fetchone()[0]

            # Total gasto
            self.cursor.execute('SELECT SUM(preco) FROM jogos')
            resultado = self.cursor.fetchone()[0]
            stats['total_gasto'] = resultado if resultado else 0

            # Jogos por loteria
            self.cursor.execute(
                'SELECT loteria, COUNT(*) FROM jogos GROUP BY loteria')
            stats['por_loteria'] = dict(self.cursor.fetchall())

            # Jogos por método
            self.cursor.execute(
                'SELECT metodo, COUNT(*) FROM jogos GROUP BY metodo')
            stats['por_metodo'] = dict(self.cursor.fetchall())

            print(f"DEBUG: Estatísticas calculadas: {stats}")
            return stats
        except sqlite3.Error as e:
            print(f"Erro ao calcular estatísticas: {e}")
            return {}

    def close(self):
        """Fecha a conexão com o banco"""
        try:
            if hasattr(self, 'conn') and self.conn:
                self.conn.close()
                print("DEBUG: Conexão com banco fechada")
        except Exception as e:
            print(f"Erro ao fechar banco: {e}")
