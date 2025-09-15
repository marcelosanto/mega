import flet as ft
import threading
import time


def main(page: ft.Page):
    page.title = "Teste de Thread e UI Update"
    page.vertical_alignment = ft.MainAxisAlignment.CENTER
    page.horizontal_alignment = ft.CrossAxisAlignment.CENTER

    def update_text_and_show_snackbar(message, color):
        """Função para atualizar o texto E mostrar um snackbar."""
        txt_status.value = message
        page.open(ft.SnackBar(content=ft.Text(message), bgcolor=color))
        # page.snack_bar.open = True
        page.update()

    def background_task():
        """Esta função executa em segundo plano."""
        # Atualiza a UI a partir da thread
        update_text_and_show_snackbar(
            "Tarefa iniciou em segundo plano...", "blue")

        time.sleep(3)  # Simula um trabalho pesado (como uma chamada de rede)

        # Atualiza a UI novamente a partir da thread
        update_text_and_show_snackbar(
            "Tarefa terminou. A UI foi atualizada!", "green")

    def start_task_click(e):
        # Atualiza a UI a partir do clique do botão (thread principal)
        update_text_and_show_snackbar(
            "Botão clicado. Iniciando a tarefa...", "grey")

        # Inicia a thread para a tarefa demorada
        thread = threading.Thread(target=background_task)
        thread.start()

    txt_status = ft.Text("Clique no botão para iniciar o teste.")
    btn_start = ft.ElevatedButton(
        "Iniciar Tarefa de Teste", on_click=start_task_click)

    page.add(txt_status, btn_start)


# Para testar no desktop, use a linha abaixo:
# ft.app(target=main)

# Para testar no navegador, comente a linha acima e descomente a linha abaixo:
ft.app(target=main, view=ft.WEB_BROWSER)
