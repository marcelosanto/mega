VERSION = "1.0.17"
UPDATE_BASE_URL = "https://api.github.com/repos/marcelosanto/mega"

LOTTERY_CONFIG = {
    "Mega-Sena": {
        "num_total": 60,
        "num_sorteados": 6,
        "min_dezenas": 6,
        "max_dezenas": 20,
        "cor_bola": "#209869",
        "preco_base": 5.00,
        "caminho_xlsx": "assets/mega_sena.xlsx",
        "colunas_numeros": ["Coluna 1", "Coluna 2", "Coluna 3", "Coluna 4", "Coluna 5", "Coluna 6"]
    },
    "Loto Fácil": {
        "num_total": 25,
        "num_sorteados": 15,
        "min_dezenas": 15,
        "max_dezenas": 20,
        "cor_bola": "#930089",
        "preco_base": 3.00,
        "caminho_xlsx": "assets/loto_facil.xlsx",
        "colunas_numeros": [f"Coluna {i}" for i in range(1, 16)]
    },
    "Quina": {
        "num_total": 80,
        "num_sorteados": 5,
        "min_dezenas": 5,
        "max_dezenas": 15,
        "cor_bola": "#260085",
        "preco_base": 2.50,
        "caminho_xlsx": "assets/quina.xlsx",
        "colunas_numeros": ["Coluna 1", "Coluna 2", "Coluna 3", "Coluna 4", "Coluna 5"]
    },
    "Loto Mania": {
        "num_total": 99, # 00 a 99
        "num_sorteados": 20,
        "min_dezenas": 50,
        "max_dezenas": 50,
        "cor_bola": "#f7941d",
        "preco_base": 3.00,
        "caminho_xlsx": "assets/lotomania.xlsx",
        "colunas_numeros": [f"Coluna {i}" for i in range(1, 21)]
    },
    "Dupla Sena": {
        "caminho_xlsx": "assets/dupla_sena_asloterias_ate_concurso_2934_sorteio.xlsx",
        "colunas_numeros": [
            "Sorteio1 - bola 1", "Sorteio1 - bola 2", "Sorteio1 - bola 3", 
            "Sorteio1 - bola 4", "Sorteio1 - bola 5", "Sorteio1 - bola 6"
        ],
        "min_dezenas": 6,
        "max_dezenas": 15,
        "num_total": 50,
        "preco_base": 2.50,
        "num_sorteados": 6,
        "cor_bola": "#bf190e",
        "cor_gradiente": ["#bf190e", "#9e140a"],
    }
}