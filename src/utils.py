import os
import sys


def get_resource_path(relative_path):
    """Obter o caminho correto para arquivos no script ou no executável"""
    if hasattr(sys, '_MEIPASS'):
        # Executável: arquivos estão no diretório temporário
        return os.path.join(sys._MEIPASS, relative_path)
    else:
        # Script: arquivos estão no diretório do projeto
        return os.path.join(os.path.dirname(__file__), relative_path)
