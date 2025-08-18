
# Gerador de Números para Loteria

Este é um aplicativo Python para gerar números para **Mega-Sena** e **Lotofácil**, utilizando dados históricos de arquivos Excel fornecidos. O aplicativo possui uma interface gráfica construída com Matplotlib, exibindo os números da Lotofácil (15-20) em roxo (`#8b44cc`) com uma barra de rolagem, e inclui um mecanismo de atualização automática para baixar a versão mais recente a partir das releases do GitHub.

## Funcionalidades

-   Gera números aleatórios para Mega-Sena e Lotofácil com base em dados históricos.
-   Interface gráfica amigável com Matplotlib, exibindo números da Lotofácil em roxo.
-   Verificação de atualizações automáticas comparando a versão atual com `version.txt` das releases do GitHub.
-   Multiplataforma: Executáveis pré-compilados para Linux (`loteria-gerador-linux`) e Windows (`loteria-gerador.exe`).

## Pré-requisitos

Para executar ou compilar o aplicativo a partir do código-fonte, você precisa de:

-   **Python**: Versão 3.13 (recomendado, <3.15 devido à compatibilidade com PyInstaller).
-   **Poetry**: Para gerenciamento de dependências.
-   **Dependências**: Listadas em `pyproject.toml` (Pandas, NumPy, Matplotlib, OpenPyXL, Requests).
-   **Fontes**: Segoe UI e Consolas (para renderização consistente da interface). No Linux, instale com:
    
    ```bash
    sudo apt install ttf-mscorefonts-installer
    
    ```
    

## Instalação

### Usando Executáveis Pré-compilados

1.  Acesse a página de [Releases](https://github.com/marcelosanto/mega/releases).
2.  Baixe a versão mais recente:
    -   **Linux**: `loteria-gerador-linux`
    -   **Windows**: `loteria-gerador.exe`
3.  Execute o aplicativo:
    -   **Linux**:
        
        ```bash
        chmod +x loteria-gerador-linux
        ./loteria-gerador-linux
        
        ```
        
    -   **Windows**:
        
        ```powershell
        .\loteria-gerador.exe
        
        ```
        

### Executando a Partir do Código-Fonte

1.  Clone o repositório:
    
    ```bash
    git clone https://github.com/marcelosanto/mega.git
    cd mega
    
    ```
    
2.  Instale o Poetry:
    
    ```bash
    python -m pip install --user poetry==2.1.4
    
    ```
    
3.  Instale as dependências:
    
    ```bash
    poetry install --no-root --with dev
    
    ```
    
4.  Execute o aplicativo:
    
    ```bash
    poetry run python app.py
    
    ```
    

## Compilando Executáveis

Para compilar seus próprios executáveis:

1.  Certifique-se de que o Poetry e as dependências estão instalados (veja acima).
2.  Compile com o PyInstaller:
    -   **Linux**:
        
        ```bash
        poetry run pyinstaller --noconfirm --onefile \
            --add-data "mega_sena_asloterias_ate_concurso_2899_sorteio.xlsx:." \
            --add-data "loto_facil_asloterias_ate_concurso_3469_sorteio.xlsx:." \
            --name loteria-gerador-linux \
            app.py
        
        ```
        
    -   **Windows** (PowerShell):
        
        ```powershell
        poetry run pyinstaller --noconfirm --onefile `
            --add-data "mega_sena_asloterias_ate_concurso_2899_sorteio.xlsx;." `
            --add-data "loto_facil_asloterias_ate_concurso_3469_sorteio.xlsx;." `
            --name loteria-gerador `
            app.py
        
        ```
        
3.  Encontre os executáveis na pasta `dist/`.

## Atualização Automática

O aplicativo verifica atualizações comparando sua versão (`1.0.0`) com o `version.txt` das [releases](https://github.com/marcelosanto/mega/releases/latest/download/version.txt). Se uma nova versão estiver disponível, ele baixa o executável correspondente e atualiza automaticamente.

## Estrutura do Projeto

-   `app.py`: Script principal com a interface gráfica e lógica do aplicativo.
-   `mega_sena_asloterias_ate_concurso_2899_sorteio.xlsx`: Dados históricos da Mega-Sena.
-   `loto_facil_asloterias_ate_concurso_3469_sorteio.xlsx`: Dados históricos da Lotofácil.
-   `pyproject.toml`: Configuração do projeto e dependências.
-   `.github/workflows/build.yml`: Workflow do GitHub Actions para compilação e criação de releases.

## Desenvolvimento

Para contribuir:

1.  Faça um fork e clone o repositório.
2.  Crie um ambiente virtual com Poetry:
    
    ```bash
    poetry install --no-root --with dev
    
    ```
    
3.  Faça alterações e teste:
    
    ```bash
    poetry run python app.py
    
    ```
    
4.  Envie um pull request.

## Licença

Este projeto está licenciado sob a Licença MIT. Veja o arquivo LICENSE para mais detalhes.

## Agradecimentos

-   Desenvolvido com [Python](https://www.python.org/), [Pandas](https://pandas.pydata.org/), [Matplotlib](https://matplotlib.org/) e [PyInstaller](https://pyinstaller.org/).
-   Dados históricos fornecidos pela Caixa Econômica Federal (resultados de loterias).
