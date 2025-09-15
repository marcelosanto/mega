VERSION = "1.0.17"
UPDATE_BASE_URL = "https://api.github.com/repos/marcelosanto/mega"

LOTTERY_CONFIG = {
    'Mega-Sena': {
        'caminho_xlsx': 'mega_sena_asloterias_ate_concurso_2899_sorteio.xlsx',
        'colunas_numeros': ['bola 1', 'bola 2', 'bola 3', 'bola 4', 'bola 5', 'bola 6'],
        'min_dezenas': 6,
        'max_dezenas': 20,
        'num_total': 60,
        'preco_base': 6.00,
        'num_sorteados': 6,
        'cor_bola': '#00cc44',
        'cor_gradiente': ['#00cc44', '#00aa33']
    },
    'Loto Fácil': {
        'caminho_xlsx': 'loto_facil_asloterias_ate_concurso_3469_sorteio.xlsx',
        'colunas_numeros': ['bola 1', 'bola 2', 'bola 3', 'bola 4', 'bola 5', 'bola 6', 'bola 7', 'bola 8', 'bola 9', 'bola 10', 'bola 11', 'bola 12', 'bola 13', 'bola 14', 'bola 15'],
        'min_dezenas': 15,
        'max_dezenas': 20,
        'num_total': 25,
        'preco_base': 3.50,
        'num_sorteados': 15,
        'cor_bola': '#8b44cc',
        'cor_gradiente': ['#8b44cc', '#6a2c9b']
    }
}
