import flet as ft


def main(page: ft.Page):
    def on_click(e):
        # Crear y mostrar el SnackBar
        snack_bar = ft.SnackBar(ft.Text("Hello, world!"))
        page.overlay.append(snack_bar)
        snack_bar.open = True
        page.update()
    
    # Crear un Container con propiedades
    container = ft.Container(
        expand=True,
        content=ft.Column(
            expand=True,
            controls=[
            ft.Text("Mi Aplicación Flet", size=24, weight="bold"),
            ft.Button("Open SnackBar", on_click=on_click),
            ft.Text("Presiona el botón para ver el mensaje")
            ]
        ),
        padding=20,
        margin=10,
        bgcolor=ft.Colors.RED,
        border_radius=10,
        width=300,
        alignment=ft.alignment.center
    )
    
    page.add(container)


if __name__ == "__main__":
    ft.app(target=main)