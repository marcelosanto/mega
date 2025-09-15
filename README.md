# 🎲 Gerador de Números para Loterias

Uma aplicação de desktop moderna para gerar números de loteria (Mega-Sena e Loto Fácil) com base em diferentes estratégias estatísticas. Inclui histórico de jogos, visualização de frequência e um sistema de atualização automática.

## ✨ Funcionalidades

-   **Múltiplas Loterias**: Suporte para Mega-Sena e Loto Fácil.
    
-   **Métodos de Geração**:
    
    -   **Top Frequentes**: Gera números baseados nos mais sorteados historicamente.
        
    -   **Probabilístico**: Gera números usando a frequência de cada dezena como um peso para o sorteio.
        
-   **Cálculo de Custos**: Calcula o custo total do jogo e o valor por participante em tempo real.
    
-   **Suporte a Bolão**: Permite gerar múltiplos jogos para um bolão, dividindo os custos entre os participantes.
    
-   **Histórico de Jogos**: Salva todos os jogos gerados num banco de dados local (SQLite) para consulta futura.
    
-   **Visualização Avançada**:
    
    -   **Paginação**: O histórico é exibido em páginas para melhor organização.
        
    -   **Detalhes do Jogo**: Clique num jogo salvo para ver todos os números e detalhes da aposta.
        
-   **Análise de Dados**: Exibe um gráfico com a frequência histórica de cada número sorteado.
    
-   **Atualização Automática**: O aplicativo verifica se existem novas versões no GitHub e permite a atualização com um clique.
    
-   **Interface Moderna**: Construído com Flet para uma experiência de utilizador limpa e responsiva.
    

## 🛠️ Tecnologias Utilizadas

-   **Linguagem**: Python 3.13
    
-   **Interface Gráfica**: [Flet](https://flet.dev/ "null")
    
-   **Análise de Dados**: [Pandas](https://pandas.pydata.org/ "null") & [NumPy](https://numpy.org/ "null")
    
-   **Gráficos**: [Matplotlib](https://matplotlib.org/ "null")
    
-   **Gestor de Dependências**: [Poetry](https://python-poetry.org/ "null")
    
-   **Build e CI/CD**: [GitHub Actions](https://github.com/features/actions "null")
    

## 🚀 Instalação e Uso

### Para Utilizadores Finais

1.  Vá para a secção de [**Releases**](https://www.google.com/search?q=https://github.com/marcelosanto/mega/releases/latest "null") deste repositório.
    
2.  Faça o download do arquivo correspondente ao seu sistema operativo:
    
    -   `loteria-gerador-windows.zip` para Windows.
        
    -   `loteria-gerador-linux.tar.gz` para Linux.
        
3.  Descompacte o arquivo e execute o programa.
    

### Para Desenvolvedores

Se deseja executar o projeto localmente para desenvolvimento:

1.  **Clone o repositório:**
    
    ```
    git clone [https://github.com/marcelosanto/mega.git](https://github.com/marcelosanto/mega.git)
    cd mega
    
    ```
    
2.  **Instale o Poetry** (caso ainda não o tenha):
    
    ```
    pip install poetry
    
    ```
    
3.  **Instale as dependências do projeto:**
    
    ```
    poetry install
    
    ```
    
4.  **Execute a aplicação:**
    
    ```
    poetry run python megasena_gerador/main.py
    
    ```
    

## 🏗️ Processo de Build

O build dos executáveis para Windows e Linux é totalmente automatizado através do **GitHub Actions**. A cada `push` na branch `main`, um novo workflow é disparado, que:

1.  Configura o ambiente para Linux e Windows.
    
2.  Instala as dependências com Poetry.
    
3.  Executa o comando `flet build` para empacotar a aplicação, incluindo os arquivos de dados da pasta `assets`.
    
4.  Cria uma nova "Release" no GitHub.
    
5.  Anexa os executáveis (`.zip` e `.tar.gz`) à release, prontos para download.
    

Para fazer um build manual, o comando é:

```
# Para Linux
poetry run flet build linux megasena_gerador/main.py

# Para Windows
poetry run flet build windows megasena_gerador/main.py

```

## 📄 Licença

Distribuído sob a licença MIT. Veja o arquivo `LICENSE` para mais informações.

Feito com ❤️ por **Marcelo Santo**.
