import flet as ft
import datetime
import json
import os
import pandas as pd
import threading
from collections import defaultdict
import time

class ConfiguracionContainer(ft.Container):
    def __init__(self, page=None, reloj_global=None, usuario_actual=None, rol_actual=None):
        super().__init__(expand=True)
        
        self.page = page
        self.reloj_global = reloj_global
        self.usuario_actual = usuario_actual
        self.rol_actual = rol_actual
        self.hora_objetivo = None
        
        # Archivo de usuarios
        self.usuarios_file = "usuarios.json"
        
        # Cargar usuarios al inicio
        self.usuarios = self.cargar_usuarios()
        
        # Variable para rastrear el usuario original que se está editando
        self.usuario_original_editando = None
        
        # ---------- TIME PICKER ----------
        self.time_picker = ft.TimePicker(
            confirm_text="Aceptar",
            help_text="Selecciona una hora",
            on_change=self.hora_seleccionada,
        )
        
        if page:
            page.overlay.append(self.time_picker)

        # ---------- TEXTO HORA ACTUAL ----------
        self.texto_hora = ft.Text(
            value="--:-- --",
            size=28,
            weight="bold",
            color="black",
        )

        # ---------- BOTÓN ----------
        self.btn_seleccionar = ft.ElevatedButton(
            "Seleccionar hora",
            on_click=self.abrir_time_picker,
            width=130,
            height=48,
        )

        # ---------- LISTA DE HORAS ----------
        self.lista_horas = ft.Column(spacing=5, scroll=ft.ScrollMode.AUTO)

        # ---------- GESTIÓN DE USUARIOS ----------
        self.controles_usuarios = ft.Column(spacing=10, scroll=ft.ScrollMode.AUTO)
        
        # ---------- HISTORIAL DE REGISTROS ----------
        self.historial_registros = ft.Column(spacing=10, scroll=ft.ScrollMode.AUTO)
        
        # ---------- PESTAÑAS ----------
        self.tabs = ft.Tabs(
            selected_index=0,
            animation_duration=300,
            tabs=[
                ft.Tab(text="Configuración de Horas"),
                ft.Tab(text="Gestión de Usuarios"),
                ft.Tab(text="Historial de Registros"),
            ],
            on_change=self.cambiar_pestana
        )
        
        # Crear contenedores para cada pestaña
        self.contenedor_horas = self.crear_contenedor_horas()
        self.contenedor_usuarios = self.crear_contenedor_usuarios()
        self.contenedor_historial = self.crear_contenedor_historial()
        
        # Contenedor que mostrará la pestaña activa
        self.contenedor_activo = ft.Container(
            expand=True,
            content=self.contenedor_horas
        )

        # ---------- INTERFAZ PRINCIPAL ----------
        self.content = ft.Column(
            alignment=ft.MainAxisAlignment.START,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            expand=True,
            controls=[
                ft.Container(
                    padding=ft.padding.only(bottom=10),
                    content=self.tabs
                ),
                self.contenedor_activo
            ]
        )

        # Cargar horas desde el reloj global si existe
        self.actualizar_lista_horas()
        
        # Iniciar solo la actualización de la hora visual
        self.iniciar_actualizacion_hora_visual()
        
        # Cargar historial de registros
        self.cargar_y_mostrar_historial()

        # self.snackbar = ft.SnackBar(
        #     content=ft.Text("", color=ft.Colors.WHITE),
        #     bgcolor=ft.Colors.BLUE,
        #     duration=2000,
        # )
        # self.page.snack_bar = self.snackbar

    def crear_contenedor_horas(self):
        """Crea el contenedor para la pestaña de horas"""
        return ft.Container(
            expand=True,
            content=ft.Column(
                alignment=ft.MainAxisAlignment.START,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                expand=True,
                controls=[
                    ft.Container(
                        bgcolor="white",
                        height=100,
                        border_radius=20,
                        alignment=ft.alignment.center,
                        content=ft.Row(
                            alignment=ft.MainAxisAlignment.SPACE_AROUND,
                            controls=[self.texto_hora, self.btn_seleccionar]
                        )
                    ),
                    ft.Divider(height=9, thickness=3, color=ft.Colors.BLACK),
                    ft.Text("Horas registradas:", size=16, weight="bold"),
                    ft.Container(
                        bgcolor="white",
                        border_radius=20,
                        expand=True,
                        padding=10,
                        content=self.lista_horas
                    )
                ]
            )
        )

    def crear_contenedor_usuarios(self):
        """Crea el contenedor para la pestaña de usuarios"""
        if self.rol_actual != "admin":
            return ft.Container(
                expand=True,
                alignment=ft.alignment.center,
                content=ft.Column(
                    alignment=ft.MainAxisAlignment.CENTER,
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    spacing=20,
                    controls=[
                        ft.Icon(ft.Icons.LOCK, size=80, color=ft.Colors.GREY_400),
                        ft.Text(
                            "Acceso Restringido",
                            size=28,
                            weight=ft.FontWeight.BOLD,
                            color=ft.Colors.GREY_600,
                        ),
                        ft.Text(
                            "Esta sección solo está disponible\npara usuarios administradores",
                            size=16,
                            color=ft.Colors.GREY_500,
                            text_align=ft.TextAlign.CENTER,
                        ),
                    ]
                )
            )
        else:
            # Botón para agregar nuevo usuario
            btn_agregar_usuario = ft.ElevatedButton(
                text="Agregar Nuevo Usuario",
                icon=ft.Icons.PERSON_ADD,
                on_click=lambda e: self.abrir_dialogo_nuevo_usuario(),
                width=300,
                height=45,
                style=ft.ButtonStyle(
                    bgcolor=ft.Colors.GREEN_700,
                    color=ft.Colors.WHITE,
                )
            )
            
            # Actualizar lista de usuarios
            self.actualizar_lista_usuarios()
            
            return ft.Container(
                expand=True,
                content=ft.Column(
                    alignment=ft.MainAxisAlignment.START,
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    expand=True,
                    spacing=15,
                    controls=[
                        btn_agregar_usuario,
                        ft.Divider(height=10, thickness=2, color=ft.Colors.GREY_400),
                        ft.Text("Usuarios registrados:", size=18, weight="bold", color=ft.Colors.BLUE_900),
                        ft.Container(
                            bgcolor=ft.Colors.WHITE,
                            border_radius=15,
                            padding=15,
                            expand=True,
                            content=self.controles_usuarios
                        )
                    ]
                )
            )

    def crear_contenedor_historial(self):
        """Crea el contenedor para la pestaña de historial de registros"""
        # Botón para limpiar historial
        btn_limpiar_historial = ft.ElevatedButton(
            text="Limpiar Historial",
            icon=ft.Icons.DELETE_FOREVER,
            on_click=self.limpiar_historial,
            width=200,
            height=45,
            style=ft.ButtonStyle(
                bgcolor=ft.Colors.RED_700,
                color=ft.Colors.WHITE,
            )
        )
        
        # Texto informativo
        texto_info = ft.Text(
            "Descarga archivos Excel organizados por mes con todos los registros",
            size=14,
            color=ft.Colors.GREY_600,
            text_align=ft.TextAlign.CENTER,
        )
        
        return ft.Container(
            expand=True,
            content=ft.Column(
                alignment=ft.MainAxisAlignment.START,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                expand=True,
                spacing=15,
                controls=[
                    ft.Row(
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                        controls=[
                            ft.Text("Historial de Registros por Mes:", size=20, weight="bold", color=ft.Colors.BLUE_900),
                            btn_limpiar_historial
                        ]
                    ),
                    texto_info,
                    ft.Divider(height=10, thickness=2, color=ft.Colors.GREY_400),
                    ft.Container(
                        bgcolor=ft.Colors.WHITE,
                        border_radius=15,
                        padding=15,
                        expand=True,
                        content=self.historial_registros
                    )
                ]
            )
        )

    def cargar_y_mostrar_historial(self):
        """Carga y muestra el historial de registros organizado por mes"""
        self.historial_registros.controls.clear()
        
        # Cargar historial desde el reloj global si existe
        if self.reloj_global and hasattr(self.reloj_global, 'historial_registros'):
            historial = self.reloj_global.historial_registros
            
            if not historial:
                self.historial_registros.controls.append(
                    ft.Container(
                        padding=20,
                        alignment=ft.alignment.center,
                        content=ft.Text(
                            "No hay registros en el historial",
                            size=16,
                            color=ft.Colors.GREY_500,
                            italic=True
                        )
                    )
                )
                return
            
            # Agrupar registros por mes
            registros_por_mes = self.agrupar_registros_por_mes(historial)
            
            if not registros_por_mes:
                self.historial_registros.controls.append(
                    ft.Container(
                        padding=20,
                        alignment=ft.alignment.center,
                        content=ft.Text(
                            "No hay registros en el historial",
                            size=16,
                            color=ft.Colors.GREY_500,
                            italic=True
                        )
                    )
                )
                return
            
            # Crear una fila para cada mes
            for mes_key, registros in registros_por_mes.items():
                fila = self.crear_fila_mes(mes_key, registros)
                self.historial_registros.controls.append(fila)

    def agrupar_registros_por_mes(self, historial):
        """Agrupa los registros por mes (YYYY-MM)"""
        registros_por_mes = defaultdict(list)
        
        for registro in historial:
            try:
                # Parsear fecha del registro
                fecha_str = registro["fecha"]
                # Formato: dd/mm/yy
                dia, mes, anio = fecha_str.split('/')
                anio_completo = f"20{anio}" if len(anio) == 2 else anio
                
                # Crear clave del mes (YYYY-MM)
                mes_key = f"{anio_completo}-{mes.zfill(2)}"
                
                # Obtener nombre del mes en español
                meses_es = {
                    "01": "Enero", "02": "Febrero", "03": "Marzo", "04": "Abril",
                    "05": "Mayo", "06": "Junio", "07": "Julio", "08": "Agosto",
                    "09": "Septiembre", "10": "Octubre", "11": "Noviembre", "12": "Diciembre"
                }
                nombre_mes = meses_es.get(mes, f"Mes {mes}")
                
                # Agregar registro al mes correspondiente
                registros_por_mes[mes_key].append({
                    "registro": registro,
                    "nombre_mes": nombre_mes,
                    "anio": anio_completo
                })
            except Exception as e:
                print(f"Error procesando registro: {e}")
                continue
        
        return dict(registros_por_mes)

    def crear_fila_mes(self, mes_key, registros_mes):
        """Crea una fila para mostrar un mes con sus registros"""
        # Obtener información del mes
        primer_registro = registros_mes[0]
        nombre_mes = primer_registro["nombre_mes"]
        anio = primer_registro["anio"]
        
        # Contar registros por tipo
        total_registros = len(registros_mes)
        automaticos = sum(1 for r in registros_mes if r["registro"]["tipo"] == "registro_automatico")
        manuales = sum(1 for r in registros_mes if r["registro"]["tipo"] == "registro_manual")
        
        # Crear botón para descargar Excel del mes
        btn_descargar = ft.ElevatedButton(
            text=f"Descargar {nombre_mes} {anio}",
            icon=ft.Icons.DOWNLOAD,
            on_click=lambda e, mes=mes_key, regs=registros_mes: self.descargar_excel_mes(mes, regs),
            width=250,
            height=45,
            style=ft.ButtonStyle(
                bgcolor=ft.Colors.GREEN_700,
                color=ft.Colors.WHITE,
            )
        )
        
        # Crear fila
        fila = ft.Container(
            padding=20,
            border_radius=12,
            bgcolor=ft.Colors.GREY_50,
            border=ft.border.all(1, ft.Colors.GREY_300),
            margin=ft.margin.only(bottom=15),
        )
        
        fila.content = ft.Column(
            spacing=12,
            controls=[
                # Fila superior: Mes y botón
                ft.Row(
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    controls=[
                        ft.Column(
                            spacing=5,
                            controls=[
                                ft.Text(
                                    f"{nombre_mes} {anio}",
                                    size=22,
                                    weight=ft.FontWeight.BOLD,
                                    color=ft.Colors.BLUE_900,
                                ),
                                ft.Text(
                                    f"Total registros: {total_registros}",
                                    size=14,
                                    color=ft.Colors.GREY_700,
                                )
                            ]
                        ),
                        btn_descargar
                    ]
                ),
                
                # Información de tipos de registros
                ft.Container(
                    padding=ft.padding.symmetric(horizontal=10, vertical=8),
                    bgcolor=ft.Colors.WHITE,
                    border_radius=8,
                    content=ft.Row(
                        spacing=30,
                        controls=[
                            ft.Column(
                                spacing=3,
                                controls=[
                                    ft.Text(
                                        "Registros Automáticos",
                                        size=12,
                                        color=ft.Colors.GREY_600,
                                    ),
                                    ft.Container(
                                        content=ft.Text(
                                            f"{automaticos}",
                                            size=16,
                                            weight=ft.FontWeight.BOLD,
                                            color=ft.Colors.BLUE_700,
                                        ),
                                        padding=ft.padding.symmetric(horizontal=10, vertical=4),
                                        bgcolor=ft.Colors.BLUE_50,
                                        border_radius=6,
                                    )
                                ]
                            ),
                            ft.Column(
                                spacing=3,
                                controls=[
                                    ft.Text(
                                        "Registros Manuales",
                                        size=12,
                                        color=ft.Colors.GREY_600,
                                    ),
                                    ft.Container(
                                        content=ft.Text(
                                            f"{manuales}",
                                            size=16,
                                            weight=ft.FontWeight.BOLD,
                                            color=ft.Colors.GREEN_700,
                                        ),
                                        padding=ft.padding.symmetric(horizontal=10, vertical=4),
                                        bgcolor=ft.Colors.GREEN_50,
                                        border_radius=6,
                                    )
                                ]
                            ),
                            ft.Column(
                                spacing=3,
                                controls=[
                                    ft.Text(
                                        "Periodo",
                                        size=12,
                                        color=ft.Colors.GREY_600,
                                    ),
                                    ft.Container(
                                        content=ft.Text(
                                            f"{mes_key}",
                                            size=14,
                                            color=ft.Colors.GREY_700,
                                        ),
                                        padding=ft.padding.symmetric(horizontal=10, vertical=4),
                                        bgcolor=ft.Colors.GREY_100,
                                        border_radius=6,
                                    )
                                ]
                            )
                        ]
                    )
                )
            ]
        )
        
        return fila

    def descargar_excel_mes(self, mes_key, registros_mes):
        """Descarga todos los registros de un mes como archivo Excel"""
        try:
            # Preparar datos para Excel
            datos_excel = []
            
            for item in registros_mes:
                registro = item["registro"]
                datos = registro["datos"]
                
                # Convertir fecha al formato YYYY-MM-DD para ordenamiento
                fecha_str = registro["fecha"]  # Formato: dd/mm/yy
                hora_str = registro["hora"]     # Formato: HH:MM
                
                # Parsear fecha
                dia, mes, anio = fecha_str.split('/')
                anio_completo = f"20{anio}" if len(anio) == 2 else anio
                fecha_iso = f"{anio_completo}-{mes.zfill(2)}-{dia.zfill(2)}"
                
                # Crear fila para Excel
                fila_excel = {
                    "Fecha": fecha_iso,
                    "Hora": hora_str,
                    "Tipo": "Automático" if registro["tipo"] == "registro_automatico" else "Manual",
                    "Fuente": registro.get("fuente", "Sistema"),
                    "Temperatura (°C)": datos.get('temperatura', '--'),
                    "Humedad (%)": datos.get('humedad', '--'),
                    "Presión 1 (Pa)": datos.get('presion1', '--'),
                    "Presión 2 (Pa)": datos.get('presion2', '--'),
                    "Presión 3 (Pa)": datos.get('presion3', '--')
                }
                
                datos_excel.append(fila_excel)
            
            # Ordenar por fecha y hora
            datos_excel.sort(key=lambda x: (x["Fecha"], x["Hora"]))
            
            # Crear DataFrame
            df = pd.DataFrame(datos_excel)
            
            # Obtener información del mes
            anio, mes_num = mes_key.split('-')
            meses_es = {
                "01": "Enero", "02": "Febrero", "03": "Marzo", "04": "Abril",
                "05": "Mayo", "06": "Junio", "07": "Julio", "08": "Agosto",
                "09": "Septiembre", "10": "Octubre", "11": "Noviembre", "12": "Diciembre"
            }
            nombre_mes = meses_es.get(mes_num, f"Mes_{mes_num}")
            
            # Crear nombre de archivo
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"Registros_{nombre_mes}_{anio}_{timestamp}.xlsx"
            
            # Ruta del escritorio
            desktop_path = os.path.join(os.path.expanduser("~"), "Desktop")
            filepath = os.path.join(desktop_path, filename)
            
            # Guardar como Excel con formato
            with pd.ExcelWriter(filepath, engine='openpyxl') as writer:
                df.to_excel(writer, sheet_name=f'{nombre_mes}_{anio}', index=False)
                
                # Ajustar ancho de columnas
                worksheet = writer.sheets[f'{nombre_mes}_{anio}']
                for column in df:
                    column_length = max(df[column].astype(str).map(len).max(), len(column))
                    col_idx = df.columns.get_loc(column)
                    worksheet.column_dimensions[chr(65 + col_idx)].width = column_length + 2
            
            # Mostrar notificación de éxito
            self.mostrar_notificacion(f"✓ Archivo guardado en Escritorio: {filename}", ft.Colors.GREEN)
            
            print(f"Archivo Excel guardado: {filepath}")
            print(f"Total registros: {len(datos_excel)}")
            
        except Exception as e:
            print(f"Error al guardar Excel: {e}")
            self.mostrar_notificacion(f"✗ Error al guardar archivo: {str(e)}", ft.Colors.RED)

    def limpiar_historial(self, e):
        """Limpia todo el historial de registros"""
        def confirmar_limpieza(e):
            if self.reloj_global and hasattr(self.reloj_global, 'limpiar_historial'):
                self.reloj_global.limpiar_historial()
                self.cargar_y_mostrar_historial()
                dlg.open = False
                self.page.update()
                self.mostrar_notificacion("✓ Historial limpiado", ft.Colors.GREEN)
        
        def cancelar_limpieza(e):
            dlg.open = False
            self.page.update()
        
        dlg = ft.AlertDialog(
            modal=True,
            title=ft.Text("Confirmar limpieza"),
            content=ft.Text("¿Está seguro que desea eliminar TODOS los registros del historial?\nEsta acción no se puede deshacer."),
            actions=[
                ft.TextButton("Cancelar", on_click=cancelar_limpieza),
                ft.ElevatedButton(
                    "Limpiar Todo", 
                    on_click=confirmar_limpieza,
                    bgcolor=ft.Colors.RED,
                    color=ft.Colors.WHITE
                ),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )
        
        self.page.dialog = dlg
        dlg.open = True
        self.page.update()

    def cargar_usuarios(self):
        """Carga los usuarios desde el archivo JSON"""
        try:
            if os.path.exists(self.usuarios_file):
                with open(self.usuarios_file, "r") as f:
                    datos = json.load(f)
                    
                    # Verificar si es un diccionario
                    if isinstance(datos, dict):
                        return datos
                    else:
                        # Convertir a diccionario si no lo es
                        print(f"⚠️ Advertencia: Formato de usuarios no es diccionario, es {type(datos)}")
                        return {}
            else:
                # Crear archivo con admin por defecto
                usuarios_default = {
                    "admin": {
                        "password": "admin123",
                        "rol": "admin"
                    }
                }
                with open(self.usuarios_file, "w") as f:
                    json.dump(usuarios_default, f, indent=2)
                return usuarios_default
        except Exception as e:
            print(f"❌ Error cargando usuarios: {e}")
            return {}

    def guardar_usuarios(self):
        """Guarda los usuarios en el archivo JSON"""
        try:
            with open(self.usuarios_file, "w") as f:
                json.dump(self.usuarios, f, indent=2)
            print("✅ Usuarios guardados exitosamente")
            return True
        except Exception as e:
            print(f"❌ Error guardando usuarios: {e}")
            return False

    def actualizar_lista_usuarios(self):
        """Actualiza la lista de usuarios en la interfaz"""
        self.controles_usuarios.controls.clear()
        
        # Recargar usuarios
        self.usuarios = self.cargar_usuarios()
        
        if not self.usuarios:
            self.controles_usuarios.controls.append(
                ft.Container(
                    padding=20,
                    alignment=ft.alignment.center,
                    content=ft.Text(
                        "No hay usuarios registrados",
                        size=16,
                        color=ft.Colors.GREY_500,
                        italic=True
                    )
                )
            )
            return
        
        for usuario, datos in self.usuarios.items():
            # No mostrar el usuario actual en la lista de edición
            # if usuario == self.usuario_actual:
            #     continue
                
            # Crear fila para cada usuario
            fila = self.crear_fila_usuario(usuario, datos)
            self.controles_usuarios.controls.append(fila)
        
        # Si no hay usuarios (excepto el actual)
        if len(self.controles_usuarios.controls) == 0:
            self.controles_usuarios.controls.append(
                ft.Container(
                    padding=20,
                    alignment=ft.alignment.center,
                    content=ft.Text(
                        "No hay otros usuarios registrados",
                        size=16,
                        color=ft.Colors.GREY_500,
                        italic=True
                    )
                )
            )

    def crear_fila_usuario(self, usuario, datos):
        """Crea una fila para mostrar un usuario"""
        # Determinar color según rol
        rol_color = ft.Colors.GREEN if datos["rol"] == "admin" else ft.Colors.BLUE
        rol_texto = "Administrador" if datos["rol"] == "admin" else "Usuario"
        
        fila = ft.Container(
            padding=15,
            border_radius=10,
            bgcolor=ft.Colors.WHITE,
            border=ft.border.all(1, ft.Colors.GREY_300),
            margin=ft.margin.only(bottom=10),
            shadow=ft.BoxShadow(
                spread_radius=1,
                blur_radius=3,
                color=ft.Colors.GREY_300,
            )
        )
        
        fila.content = ft.Row(
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
            controls=[
                ft.Column(
                    spacing=8,
                    expand=True,
                    controls=[
                        ft.Row(
                            spacing=10,
                            controls=[
                                ft.Icon(ft.Icons.PERSON, color=ft.Colors.BLUE_700, size=20),
                                ft.Text(
                                    f"Usuario: {usuario}", 
                                    size=16, 
                                    weight="bold", 
                                    color=ft.Colors.BLUE_900
                                ),
                            ]
                        ),
                        ft.Row(
                            spacing=10,
                            controls=[
                                ft.Icon(ft.Icons.LOCK, color=ft.Colors.GREY_600, size=16),
                                ft.Text(
                                    f"Contraseña: {'•' * 8}", 
                                    size=14, 
                                    color=ft.Colors.GREY_700
                                ),
                            ]
                        ),
                        ft.Container(
                            content=ft.Text(
                                rol_texto, 
                                size=12, 
                                color=ft.Colors.WHITE,
                                weight=ft.FontWeight.BOLD
                            ),
                            bgcolor=rol_color,
                            padding=ft.padding.symmetric(horizontal=12, vertical=4),
                            border_radius=8,
                            width=120,
                        )
                    ]
                ),
                ft.Row(
                    spacing=5,
                    controls=[
                        ft.IconButton(
                            icon=ft.Icons.EDIT,
                            icon_color=ft.Colors.BLUE_700,
                            icon_size=24,
                            tooltip="Editar usuario",
                            data={"usuario": usuario, "datos": datos},
                            on_click=self.abrir_dialogo_editar_usuario
                        ),
                        ft.IconButton(
                            icon=ft.Icons.DELETE,
                            icon_color=ft.Colors.RED_700,
                            icon_size=24,
                            tooltip="Eliminar usuario",
                            data=usuario,
                            on_click=self.abrir_dialogo_eliminar_usuario
                        )
                    ]
                )
            ]
        )
        
        return fila

    def abrir_dialogo_nuevo_usuario(self, e=None):
        """Muestra diálogo para crear nuevo usuario"""
        # Campos del formulario
        self.nuevo_usuario_nombre = ft.TextField(
            label="Nombre de usuario",
            prefix_icon=ft.Icons.PERSON_ADD,
            width=300,
            autofocus=True,
            hint_text="Ej: usuario1",
        )
        
        self.nuevo_usuario_contrasena = ft.TextField(
            label="Contraseña",
            password=True,
            can_reveal_password=True,
            prefix_icon=ft.Icons.LOCK,
            width=300,
            hint_text="Mínimo 6 caracteres",
        )
        
        self.nuevo_usuario_rol = ft.Dropdown(
            label="Rol del usuario",
            width=300,
            options=[
                ft.dropdown.Option("usuario", "Usuario Normal"),
                ft.dropdown.Option("admin", "Administrador"),
            ],
            value="usuario",
            hint_text="Seleccione un rol",
        )
        
        self.error_text_nuevo = ft.Text("", color=ft.Colors.RED, size=12)
        
        def crear_usuario(e):
            usuario = self.nuevo_usuario_nombre.value.strip()
            contrasena = self.nuevo_usuario_contrasena.value.strip()
            rol = self.nuevo_usuario_rol.value
            
            # Validaciones básicas
            if not usuario:
                self.error_text_nuevo.value = "El nombre de usuario es obligatorio"
                self.page.update()
                return
            
            if not contrasena:
                self.error_text_nuevo.value = "La contraseña es obligatoria"
                self.page.update()
                return
            
            if len(contrasena) < 6:
                self.error_text_nuevo.value = "La contraseña debe tener al menos 6 caracteres"
                self.page.update()
                return
            
            # Verificar si el usuario ya existe
            if usuario in self.usuarios:
                self.error_text_nuevo.value = "El usuario ya existe"
                self.page.update()
                return
            
            # Crear nuevo usuario
            self.usuarios[usuario] = {
                'password': contrasena,
                'rol': rol
            }
            
            if self.guardar_usuarios():
                # Actualizar lista de usuarios
                self.actualizar_lista_usuarios()
                dlg.open = False
                self.page.update()
                self.mostrar_notificacion(f"✅ Usuario '{usuario}' creado exitosamente", ft.Colors.GREEN)
            else:
                self.error_text_nuevo.value = "Error al guardar el usuario"
                self.page.update()
        
        def cancelar(e):
            dlg.open = False
            self.page.update()
        
        dlg = ft.AlertDialog(
            modal=True,
            title=ft.Text("➕ Crear Nuevo Usuario"),
            content=ft.Column(
                width=400,
                spacing=15,
                controls=[
                    self.nuevo_usuario_nombre,
                    self.nuevo_usuario_contrasena,
                    self.nuevo_usuario_rol,
                    self.error_text_nuevo,
                ]
            ),
            actions=[
                ft.TextButton("Cancelar", on_click=cancelar),
                ft.ElevatedButton(
                    "Crear Usuario",
                    on_click=crear_usuario,
                    bgcolor=ft.Colors.GREEN,
                    color=ft.Colors.WHITE,
                ),
            ],
        )
        
        self.page.dialog = dlg
        dlg.open = True
        self.page.update()

    def abrir_dialogo_editar_usuario(self, e):
        """Muestra diálogo para editar usuario existente - AHORA editable"""
        usuario_data = e.control.data
        usuario_original = usuario_data["usuario"]
        datos = usuario_data["datos"]
        
        # Guardar el usuario original para referencia
        self.usuario_original_editando = usuario_original
        
        # Campos del formulario con valores actuales - AHORA EDITABLES
        self.editar_usuario_nombre = ft.TextField(
            label="Nombre de usuario",
            value=usuario_original,
            prefix_icon=ft.Icons.PERSON,
            width=300,
            autofocus=True,
            hint_text="Nuevo nombre de usuario",
        )
        
        # Mostrar la contraseña actual
        self.editar_usuario_contrasena = ft.TextField(
            label="Contraseña actual",
            value=datos["password"],  # MOSTRAR LA CONTRASEÑA ACTUAL
            password=False,  # Cambiar a False para mostrar la contraseña
            can_reveal_password=True,
            prefix_icon=ft.Icons.LOCK_RESET,
            width=300,
        )
        
        self.editar_usuario_rol = ft.Dropdown(
            label="Rol del usuario",
            width=300,
            options=[
                ft.dropdown.Option("usuario", "Usuario Normal"),
                ft.dropdown.Option("admin", "Administrador"),
            ],
            value=datos["rol"],
            hint_text="Seleccione un rol",
        )
        
        self.error_text_editar = ft.Text("", color=ft.Colors.RED, size=12)
        
        def guardar_cambios(e):
            nuevo_nombre = self.editar_usuario_nombre.value.strip()
            nueva_contrasena = self.editar_usuario_contrasena.value.strip()
            nuevo_rol = self.editar_usuario_rol.value
            
            # Validaciones
            if not nuevo_nombre:
                self.error_text_editar.value = "El nombre de usuario es obligatorio"
                self.page.update()
                return
            
            if not nueva_contrasena:
                self.error_text_editar.value = "La contraseña es obligatoria"
                self.page.update()
                return
            
            if len(nueva_contrasena) < 6:
                self.error_text_editar.value = "La contraseña debe tener al menos 6 caracteres"
                self.page.update()
                return
            
            # Verificar si el nuevo nombre ya existe (y no es el mismo usuario)
            if nuevo_nombre in self.usuarios and nuevo_nombre != usuario_original:
                self.error_text_editar.value = f"El usuario '{nuevo_nombre}' ya existe"
                self.page.update()
                return
            
            # Caso 1: Si el nombre cambió, necesitamos crear nuevo usuario y eliminar el viejo
            if nuevo_nombre != usuario_original:
                # Crear nuevo usuario con los datos actualizados
                self.usuarios[nuevo_nombre] = {
                    'password': nueva_contrasena,
                    'rol': nuevo_rol
                }
                
                # Eliminar el usuario original
                if usuario_original in self.usuarios:
                    del self.usuarios[usuario_original]
                
                mensaje_exito = f"Usuario '{usuario_original}' renombrado a '{nuevo_nombre}'"
            
            # Caso 2: Solo actualizar datos del mismo usuario
            else:
                # Actualizar datos del usuario existente
                self.usuarios[usuario_original] = {
                    'password': nueva_contrasena,
                    'rol': nuevo_rol
                }
                mensaje_exito = f"Usuario '{usuario_original}' actualizado"
            
            # Guardar cambios
            if self.guardar_usuarios():
                # Actualizar lista de usuarios
                self.actualizar_lista_usuarios()
                dlg.open = False
                self.page.update()
                self.mostrar_notificacion(f"✅ {mensaje_exito}", ft.Colors.GREEN)
            else:
                self.error_text_editar.value = "Error al guardar los cambios"
                self.page.update()
        
        def cancelar(e):
            dlg.open = False
            self.page.update()
        
        dlg = ft.AlertDialog(
            modal=True,
            title=ft.Text(f"✏️ Editar Usuario: {usuario_original}"),
            content=ft.Column(
                width=400,
                spacing=15,
                controls=[
                    ft.Text(f"Editando usuario: {usuario_original}", size=14, color=ft.Colors.GREY_600),
                    self.editar_usuario_nombre,
                    self.editar_usuario_contrasena,
                    self.editar_usuario_rol,
                    self.error_text_editar,
                    ft.Container(
                        padding=ft.padding.only(top=10),
                        content=ft.Column(
                            spacing=5,
                            controls=[
                                ft.Text(
                                    "💡 Información:",
                                    size=12,
                                    weight=ft.FontWeight.BOLD,
                                    color=ft.Colors.BLUE_700,
                                ),
                                ft.Text(
                                    "• Puedes cambiar el nombre de usuario\n"
                                    "• La contraseña se muestra para editar\n"
                                    "• Mínimo 6 caracteres para la contraseña",
                                    size=11,
                                    color=ft.Colors.GREY_600,
                                )
                            ]
                        )
                    )
                ]
            ),
            actions=[
                ft.TextButton("Cancelar", on_click=cancelar),
                ft.ElevatedButton(
                    "Guardar Cambios",
                    on_click=guardar_cambios,
                    bgcolor=ft.Colors.BLUE,
                    color=ft.Colors.WHITE,
                ),
            ],
        )
        
        self.page.dialog = dlg
        dlg.open = True
        self.page.add(dlg)

    def abrir_dialogo_eliminar_usuario(self, e):
        """Muestra diálogo para eliminar usuario"""
        usuario = e.control.data
        
        # Verificar si es el último admin
        admins = [u for u, d in self.usuarios.items() if d.get('rol') == 'admin']
        if self.usuarios[usuario].get('rol') == 'admin' and len(admins) <= 1:
            self.mostrar_notificacion("❌ No puedes eliminar el único administrador", ft.Colors.RED)
            return
        
        # No permitir eliminar el usuario actual
        if usuario == self.usuario_actual:
            self.mostrar_notificacion("❌ No puedes eliminar tu propio usuario", ft.Colors.RED)
            return
        
        def confirmar_eliminar(e):
            if usuario in self.usuarios:
                del self.usuarios[usuario]
                if self.guardar_usuarios():
                    # Actualizar lista de usuarios
                    self.actualizar_lista_usuarios()
                    dlg.open = False
                    self.page.update()
                    self.mostrar_notificacion(f"✅ Usuario '{usuario}' eliminado", ft.Colors.GREEN)
                else:
                    self.mostrar_notificacion("❌ Error al eliminar usuario", ft.Colors.RED)
        
        def cancelar(e):
            dlg.open = False
            self.page.update()
        
        dlg = ft.AlertDialog(
            modal=True,
            title=ft.Text("🗑️ Eliminar Usuario"),
            content=ft.Text(
                f"¿Está seguro que desea eliminar al usuario '{usuario}'?\n\n"
                f"Rol: {'Administrador' if self.usuarios[usuario].get('rol') == 'admin' else 'Usuario Normal'}\n\n"
                f"⚠️ Esta acción no se puede deshacer."
            ),
            actions=[
                ft.TextButton("Cancelar", on_click=cancelar),
                ft.ElevatedButton(
                    "Eliminar",
                    on_click=confirmar_eliminar,
                    bgcolor=ft.Colors.RED,
                    color=ft.Colors.WHITE,
                ),
            ],
        )
        
        self.page.dialog = dlg
        dlg.open = True
        self.page.add(dlg)

    def mostrar_notificacion(self, mensaje, color):
        """Muestra una notificación temporal"""
        # snackbar = ft.SnackBar(
        #     content=ft.Text(mensaje, color=ft.Colors.WHITE),
        #     bgcolor=color,
        #     duration=2000,
        # )
        # # self.page.snack_bar = snackbar
        # # snackbar.open = True
        # # self.page.add(snackbar)

        # self.page.overlay.append(snackbar)
        # self.page.update()

        

        # self.snackbar.content.value = mensaje
        # self.snackbar.bgcolor = color
        # self.snackbar.open = True
        # self.page.update()

        snack_bar = ft.SnackBar(
            content=ft.Text(mensaje, color=ft.Colors.WHITE),
            bgcolor=color,
            duration=2000,
        )
        self.page.overlay.append(snack_bar)
        snack_bar.open = True
        self.page.update()


    def cambiar_pestana(self, e):
        """Cambia entre pestañas"""
        index = e.control.selected_index
        
        if index == 0:  # Pestaña de horas
            self.contenedor_activo.content = self.contenedor_horas
        elif index == 1:  # Pestaña de usuarios
            # Si es admin, actualizar lista de usuarios
            if self.rol_actual == "admin":
                self.actualizar_lista_usuarios()
                # Crear nuevo contenedor de usuarios
                self.contenedor_usuarios = self.crear_contenedor_usuarios()
            self.contenedor_activo.content = self.contenedor_usuarios
        else:  # Pestaña de historial (índice 2)
            # Cargar y mostrar historial
            self.cargar_y_mostrar_historial()
            # Crear nuevo contenedor de historial
            self.contenedor_historial = self.crear_contenedor_historial()
            self.contenedor_activo.content = self.contenedor_historial
        
        if self.page:
            self.page.update()

    def actualizar_lista_horas(self):
        """Actualiza la lista de horas desde el reloj global"""
        self.lista_horas.controls.clear()
        if self.reloj_global and hasattr(self.reloj_global, 'horas_registradas'):
            for hora_time in self.reloj_global.horas_registradas:
                hora_str = hora_time.strftime("%I:%M %p")
                
                # Usar el atributo data para pasar la hora
                btn_eliminar = ft.IconButton(
                    icon=ft.Icons.DELETE,
                    icon_color="red",
                    data=hora_time,  # Almacenar la hora en data
                    on_click=lambda e: self.eliminar_hora(e.control.data)
                )
                
                fila = ft.Container(
                    padding=10,
                    border_radius=8,
                    bgcolor=ft.Colors.GREY_100,
                )

                fila.content = ft.Row(
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    controls=[
                        ft.Text(hora_str, size=16, color="black"),
                        btn_eliminar
                    ]
                )
                self.lista_horas.controls.append(fila)

    def iniciar_actualizacion_hora_visual(self):
        """Solo actualiza la hora visual, no las alarmas"""
        def actualizar_hora():
            while True:
                try:
                    ahora = datetime.datetime.now()
                    if self.page:
                        def update_ui():
                            self.texto_hora.value = ahora.strftime("%I:%M:%S %p")
                            self.page.update()
                        self.page.run_thread(update_ui)
                    time.sleep(1)
                except:
                    break
        
        thread = threading.Thread(target=actualizar_hora, daemon=True)
        thread.start()

    def abrir_time_picker(self, e):
        if self.page:
            self.time_picker.open = True
            self.page.update()

    def hora_seleccionada(self, e):
        if e.control.value:
            self.hora_objetivo = e.control.value
            hora_formato = self.hora_objetivo.strftime("%I:%M %p")

            # Usar el reloj global para agregar la hora
            if self.reloj_global and hasattr(self.reloj_global, 'agregar_hora'):
                if self.reloj_global.agregar_hora(self.hora_objetivo):
                    print("Hora agregada globalmente:", hora_formato)
                    # Actualizar lista local
                    self.actualizar_lista_horas()
                    if self.page:
                        self.page.update()

    def eliminar_hora(self, hora_time):
        """Elimina una hora usando el reloj global"""
        if self.reloj_global and hasattr(self.reloj_global, 'eliminar_hora'):
            if self.reloj_global.eliminar_hora(hora_time):
                self.actualizar_lista_horas()
                if self.page:
                    self.page.update()

    def mi_accion(self, hora):
        print(f"¡La hora {hora} ha sido alcanzada!")
        
    # Nueva función para actualizar el historial desde fuera
    def actualizar_historial_desde_externo(self):
        """Actualiza el historial cuando se llama desde fuera"""
        if self.tabs.selected_index == 2:  # Si está en la pestaña de historial
            self.cargar_y_mostrar_historial()
            if self.page:
                self.page.update()