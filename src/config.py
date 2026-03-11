VERSION = "1.0.65"
UPDATE_BASE_URL = "https://api.github.com/repos/marcelosanto/mega"

LOTTERY_CONFIG = {
    "Mega-Sena": {
        "caminho_xlsx": "assets/mega_sena.xlsx",
        "colunas_numeros": ["bola 1", "bola 2", "bola 3", "bola 4", "bola 5", "bola 6"],
        "min_dezenas": 6,
        "max_dezenas": 20,
        "num_total": 60,
        "preco_base": 5.00,
        "num_sorteados": 6,
        "cor_bola": "#209869",
    },
    "Loto Fácil": {
        "caminho_xlsx": "assets/loto_facil.xlsx",
        "colunas_numeros": [f"bola {i}" for i in range(1, 16)],
        "min_dezenas": 15,
        "max_dezenas": 20,
        "num_total": 25,
        "preco_base": 3.00,
        "num_sorteados": 15,
        "cor_bola": "#930089",
    },
    "Quina": {
        "caminho_xlsx": "assets/quina.xlsx",
        "colunas_numeros": ["bola 1", "bola 2", "bola 3", "bola 4", "bola 5"],
        "min_dezenas": 5,
        "max_dezenas": 15,
        "num_total": 80,
        "preco_base": 2.50,
        "num_sorteados": 5,
        "cor_bola": "#260085",
    },
    "Loto Mania": {
        "caminho_xlsx": "assets/lotomania.xlsx",
        "colunas_numeros": [f"bola {i}" for i in range(1, 21)],
        "min_dezenas": 50,
        "max_dezenas": 50,
        "num_total": 99,  # 00 a 99
        "preco_base": 3.00,
        "num_sorteados": 20,
        "cor_bola": "#f7941d",
    },
    "Dupla Sena": {
        "caminho_xlsx": "assets/dupla_sena.xlsx",
        "colunas_numeros": [f"Sorteio1 - bola {i}" for i in range(1, 7)],
        "colunas_numeros_2": [
            f"Sorteio2 - bola {i}" for i in range(1, 7)
        ],  # Nova chave
        "min_dezenas": 6,
        "max_dezenas": 15,
        "num_total": 50,
        "preco_base": 2.50,
        "num_sorteados": 6,
        "cor_bola": "#bf190e",
    },
}
