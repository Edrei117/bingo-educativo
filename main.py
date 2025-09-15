from kivymd.app import MDApp
from kivy.lang import Builder
from kivy.core.window import Window
from kivy.metrics import dp, sp
from kivy.utils import platform
from kivy.uix.screenmanager import ScreenManager, Screen, FadeTransition, SlideTransition
from kivymd.uix.screen import MDScreen
from kivymd.uix.button import MDRaisedButton
from kivymd.uix.label import MDLabel
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.gridlayout import MDGridLayout
from kivymd.uix.card import MDCard
from kivymd.uix.dialog import MDDialog
from kivy.core.audio import SoundLoader
from kivy.animation import Animation
from kivy.uix.image import Image
from kivy.clock import Clock
import os
import json
import random
# from pymongo import MongoClient  # Eliminado para modo offline
# from pymongo.database import Database  # Eliminado para modo offline
# from dotenv import load_dotenv  # Eliminado para modo offline
import socket
import threading
from kivy.network.urlrequest import UrlRequest
from kivymd.uix.textfield import MDTextField
from kivymd.uix.scrollview import MDScrollView
from typing import Optional, List, Dict, Any
from kivy.properties import BooleanProperty, StringProperty

# Importar pantalla de Bluetooth
from screens.bluetooth_screen import BluetoothScreen

# Importar utilidades de pantalla
from utils.screen_utils import ScreenUtils, ImageConfig

# Importar utilidades de multijugador
from utils.multiplayer_utils import ConnectionManager, MultiplayerUtils

# Cargar variables de entorno
# load_dotenv()  # Eliminado para modo offline

class MultiplayerScreen(MDScreen):
    is_host = BooleanProperty(False)
    modo_seleccionado = StringProperty('wifi')
    nombre_jugador_global = StringProperty('')

    def seleccionar_modo(self, modo):
        self.modo_seleccionado = modo
        print(f"[DEBUG] Modo multijugador seleccionado: {modo}")

    def crear_sala_bluetooth(self):
        print("[DEBUG] Crear sala Bluetooth")
        # Cambiar a la pantalla de Bluetooth
        self.manager.current = 'bluetooth_screen'

    def unirse_sala_bluetooth(self):
        print("[DEBUG] Unirse a sala Bluetooth")
        # Cambiar a la pantalla de Bluetooth
        self.manager.current = 'bluetooth_screen'

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.name = 'multiplayer'
        self.server_socket = None
        self.client_socket = None
        self.connected_players = []
        self.is_host = False
        self.room_code = None
        self.max_players = 10
        self.game_started = False

    def get_local_ip(self):
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(('8.8.8.8', 80))
            ip = s.getsockname()[0]
            s.close()
            return ip
        except Exception:
            return 'IP no detectada'

    def crear_sala(self):
        """Crea una nueva sala de juego."""
        try:
            print("[DEBUG] Intentando crear sala como servidor...")
            self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.server_socket.bind(('0.0.0.0', 5000))  # Puerto fijo para facilitar conexión
            self.server_socket.listen(self.max_players)
            self.room_code = ''.join(random.choices('0123456789', k=6))
            self.is_host = True
            local_ip = self.get_local_ip()
            from kivy.clock import Clock
            def set_labels(dt):
                self.ids.connection_status.text = f"Estado: Sala creada - Código: {self.room_code}"
                self.ids.room_info.text = "Esperando jugadores..."
                self.ids.local_ip_label.text = f"IP local: {local_ip}"
            Clock.schedule_once(set_labels, 0)
            print(f"[DEBUG] Servidor escuchando en IP {local_ip} puerto 5000")
            threading.Thread(target=self.aceptar_conexiones, daemon=True).start()
        except Exception as e:
            print(f"[ERROR] Error al crear sala: {e}")
            self.mostrar_error(f"Error al crear sala: {str(e)}")

    def buscar_salas(self):
        """Busca salas disponibles."""
        # Crear el campo de texto
        text_field = MDTextField(
            hint_text="Ingresa el código de la sala",
            helper_text="Código de 6 dígitos",
            helper_text_mode="on_error",
            input_filter="int",
            max_text_length=6
        )
        
        # Crear el diálogo con el campo de texto
        dialog = MDDialog(
            title="Buscar Sala",
            type="custom",
            content_cls=text_field,
            buttons=[
                MDRaisedButton(
                    text="Conectar",
                    on_release=lambda x: self.conectar_sala(text_field.text)
                ),
                MDRaisedButton(
                    text="Cancelar",
                    on_release=lambda x: dialog.dismiss()
                )
            ],
        )
        dialog.open()

    def conectar_sala(self, room_code):
        """Conecta a una sala existente."""
        try:
            if not room_code or len(room_code) != 6:
                self.mostrar_error("Por favor ingresa un código de sala válido (6 dígitos)")
                return
                
            # Aquí implementarías la lógica para conectar a la sala
            # Por ahora solo simulamos la conexión
            self.ids.connection_status.text = f"Estado: Conectado a sala {room_code}"
            self.ids.room_info.text = "Conectado como jugador"
            
        except Exception as e:
            self.mostrar_error(f"Error al conectar: {str(e)}")

    def unirse_sala(self):
        """Muestra un diálogo para ingresar la IP del host y conectarse como cliente."""
        from kivymd.uix.textfield import MDTextField
        from kivymd.uix.dialog import MDDialog
        from kivymd.uix.button import MDRaisedButton
        text_field = MDTextField(
            hint_text="Ingresa la IP del host",
            helper_text="Ejemplo: 192.168.1.10",
            helper_text_mode="on_error",
        )
        dialog = MDDialog(
            title="Unirse a Sala",
            type="custom",
            content_cls=text_field,
            buttons=[
                MDRaisedButton(
                    text="Conectar",
                    on_release=lambda x: self.conectar_a_host(text_field.text)
                ),
                MDRaisedButton(
                    text="Cancelar",
                    on_release=lambda x: dialog.dismiss()
                )
            ],
        )
        dialog.open()
        self._join_dialog = dialog

    def conectar_a_host(self, ip_host):
        if hasattr(self, '_join_dialog'):
            self._join_dialog.dismiss()
        if not ip_host:
            self.mostrar_error("Debes ingresar la IP del host")
            return
        try:
            print(f"[DEBUG] Intentando conectar a host {ip_host}:5000 ...")
            self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.client_socket.connect((ip_host, 5000))
            self.is_host = False
            self.ids.connection_status.text = f"Estado: Conectado a {ip_host}"
            self.ids.room_info.text = "Conectado como jugador"
            self.ids.local_ip_label.text = ""
            print(f"[DEBUG] Conexión exitosa al host {ip_host}:5000")
            from kivy.clock import Clock
            def set_status(dt):
                self.ids.connection_status.text = f"Conectado a {ip_host}"
            Clock.schedule_once(set_status, 0)
            threading.Thread(target=self.recibir_mensajes_cliente, daemon=True).start()
        except Exception as e:
            print(f"[ERROR] Error al conectar: {e}")
            self.mostrar_error(f"Error al conectar: {str(e)}")

    def recibir_mensajes_cliente(self):
        # Verifica que el socket esté inicializado
        if not self.client_socket:
            print("[ERROR] El socket del cliente no está inicializado.")
            return
        try:
            while True:
                data = self.client_socket.recv(65536)
                if not data:
                    print("[ERROR] No se recibió información del servidor.")
                    break
                import json
                info = json.loads(data.decode('utf-8'))
                print(f"[DEBUG] Datos recibidos del host: {info.keys()}")
                app = MDApp.get_running_app()
                if isinstance(app, BingoApp):
                    if 'carton' in info and 'preguntas_globales' in info:
                        # Asignar el cartón y la lista global de preguntas al cliente (inicio de partida)
                        app.cartones_jugador = [info['carton']]
                        app.preguntas_disponibles = info['preguntas_globales']
                        app.preguntas_ya_usadas = []
                        app.game_in_progress = True
                        print("[DEBUG] Cartón y preguntas globales asignados al cliente.")
                        app.cambiar_pantalla('game', 'up')
                        # Iniciar el flujo de preguntas de manera autónoma
                        if hasattr(app, 'iniciar_juego_automatico'):
                            app.iniciar_juego_automatico()
        except Exception as e:
            print(f"[ERROR] Al recibir datos del host: {e}")

    def aceptar_conexiones(self):
        """Acepta conexiones entrantes de jugadores."""
        if not self.server_socket:
            print("[ERROR] No hay socket de servidor disponible.")
            return
        print("[DEBUG] Esperando conexiones de clientes...")
        while self.is_host and self.server_socket:
            try:
                client, addr = self.server_socket.accept()
                print(f"[DEBUG] Cliente conectado desde {addr}")
                if len(self.connected_players) < self.max_players:
                    self.connected_players.append((client, addr))
                    self.actualizar_lista_jugadores()
                    from kivy.clock import Clock
                    def set_connection_status(dt):
                        self.ids.connection_status.text = f"Conexión recibida de {addr[0]}"
                    Clock.schedule_once(set_connection_status, 0)
                else:
                    client.close()
            except Exception as e:
                print(f"[ERROR] Error al aceptar conexión: {str(e)}")
                break

    def actualizar_lista_jugadores(self):
        """Actualiza la lista de jugadores en la UI y el contador."""
        self.ids.players_list.clear_widgets()
        for i, (client, addr) in enumerate(self.connected_players, 1):
            label = MDLabel(
                text=f"Jugador {i+1}: {addr[0]}",
                theme_text_color="Custom",
                text_color=(1, 1, 1, 1)
            )
            self.ids.players_list.add_widget(label)
        # Actualizar información de la sala y contador de jugadores
        total = len(self.connected_players) + 1  # +1 por el host
        self.ids.players_count_label.text = f"Jugadores conectados: {total}/10"
        if self.is_host:
            self.ids.room_info.text = f"Jugadores conectados: {total}"

    def mostrar_error(self, mensaje):
        """Muestra un mensaje de error."""
        dialog = MDDialog(
            title="Error",
            text=mensaje,
            buttons=[
                MDRaisedButton(
                    text="OK",
                    on_release=lambda x: dialog.dismiss()
                )
            ],
        )
        dialog.open()

    def volver(self):
        """Vuelve a la pantalla principal."""
        if self.server_socket:
            self.server_socket.close()
        if self.client_socket:
            self.client_socket.close()
        app = MDApp.get_running_app()
        if isinstance(app, BingoApp):
            app.cambiar_pantalla('main', 'right')

    def iniciar_juego(self):
        """Inicia el juego cuando el anfitrión lo decide."""
        if not self.is_host or self.game_started:
            return
        app = MDApp.get_running_app()
        if isinstance(app, BingoApp):
            # 1. Generar cartones únicos para cada jugador
            num_jugadores = len(self.connected_players) + 1  # +1 por el host
            print(f"[DEBUG] Generando cartones para {num_jugadores} jugadores...")
            # Usar la lógica de cargar_juego_data pero adaptada para multijugador
            import os, json, random
            all_questions = []
            base_dir = 'cartones'
            categorias_encontradas = [d for d in os.listdir(base_dir) if os.path.isdir(os.path.join(base_dir, d))]
            for categoria in categorias_encontradas:
                categoria_dir = os.path.join(base_dir, categoria)
                for archivo in os.listdir(categoria_dir):
                    if archivo.endswith('.json'):
                        ruta_archivo = os.path.join(categoria_dir, archivo)
                        try:
                            with open(ruta_archivo, 'r', encoding='utf-8') as f:
                                data = json.load(f)
                                preguntas = data.get('preguntas', [])
                                for i, pregunta in enumerate(preguntas):
                                    pregunta = pregunta.copy()
                                    pregunta['categoria'] = categoria
                                    pregunta['id'] = f"{categoria}_{archivo}_{i}"
                                    pregunta['respondida'] = False
                                    pregunta['correcta'] = False
                                    if 'opciones' in pregunta and isinstance(pregunta['opciones'], list):
                                        respuesta_correcta = pregunta.get('respuesta_correcta')
                                        opciones = pregunta['opciones'].copy()
                                        random.shuffle(opciones)
                                        pregunta['opciones'] = opciones
                                        if respuesta_correcta in opciones:
                                            pregunta['respuesta_correcta'] = respuesta_correcta
                                            pregunta['indice_correcto'] = opciones.index(respuesta_correcta)
                                    all_questions.append(pregunta)
                        except Exception as e:
                            print(f"Error procesando {ruta_archivo}: {e}")
            if not all_questions:
                self.mostrar_error("No se encontraron preguntas en los archivos locales. Asegúrate de tener al menos una categoría con preguntas válidas.")
                return
            # Crear cartones únicos
            cartones = []
            for _ in range(num_jugadores):
                preguntas_seleccionadas = []
                categorias_usadas = set()
                while len(preguntas_seleccionadas) < 8:
                    pregunta = random.choice(all_questions)
                    if pregunta not in preguntas_seleccionadas:
                        preguntas_seleccionadas.append(pregunta)
                        categorias_usadas.add(pregunta['categoria'])
                random.shuffle(preguntas_seleccionadas)
                carton = {
                    'preguntas': preguntas_seleccionadas,
                    'categorias': list(categorias_usadas),
                    'id': f"carton_{random.randint(100000, 999999)}",
                    'estructura': {
                        'filas': 2,
                        'columnas': 4
                    }
                }
                cartones.append(carton)
            # Generar lista global de preguntas (orden de turnos)
            preguntas_globales = []
            for carton in cartones:
                preguntas_globales.extend(carton['preguntas'])
            preguntas_globales = list({p['id']: p for p in preguntas_globales}.values())
            random.shuffle(preguntas_globales)
            # Asignar cartón y preguntas globales al host
            app.cartones_jugador = [cartones[0]]
            app.preguntas_disponibles = preguntas_globales.copy()
            app.preguntas_ya_usadas = []
            # Enviar a cada cliente su cartón y la lista global usando la función robusta
            if hasattr(self.manager.get_screen('multiplayer'), 'asignar_cartones_y_enviar_wifi'):
                self.manager.get_screen('multiplayer').asignar_cartones_y_enviar_wifi(cartones, preguntas_globales)
            else:
                # Fallback: método antiguo
                for idx, (client, addr) in enumerate(self.connected_players, 1):
                    try:
                        data = {
                            'carton': cartones[idx],
                            'preguntas_globales': preguntas_globales
                        }
                        client.send(json.dumps(data).encode('utf-8'))
                        print(f"[DEBUG] Cartón enviado a cliente {addr}")
                    except Exception as e:
                        print(f"[ERROR] No se pudo enviar cartón a {addr}: {e}")
            self.game_started = True
            self.ids.connection_status.text = "Estado: Iniciando juego..."
            app.game_in_progress = True
            app.cambiar_pantalla('game', 'up')
            # Iniciar el flujo de preguntas de manera autónoma
            if hasattr(app, 'iniciar_juego_automatico'):
                app.iniciar_juego_automatico()
        # Notificar a todos los jugadores que el juego ha comenzado
        for client, _ in self.connected_players:
            try:
                client.send(b"START_GAME")
            except:
                pass

    def anunciar_ganador(self, nombre_ganador):
        """Anuncia el ganador a todos los jugadores (WiFi y Bluetooth)"""
        # WiFi
        if hasattr(self, 'enviar_bingo_wifi'):
            self.enviar_bingo_wifi(nombre_ganador)
        # Bluetooth
        if hasattr(self, 'enviar_bingo_bluetooth'):
            self.enviar_bingo_bluetooth(nombre_ganador)

    def mostrar_dialogo_nombre_global(self):
        if self.nombre_jugador_global:
            return  # Ya está definido
        from kivymd.uix.textfield import MDTextField
        from kivymd.uix.dialog import MDDialog
        from kivymd.uix.button import MDRaisedButton
        content = MDTextField(
            hint_text="Tu nombre",
            helper_text="Ingresa tu nombre de jugador",
            helper_text_mode="on_error",
        )
        dialog = MDDialog(
            title="Nombre de jugador",
            type="custom",
            content_cls=content,
            buttons=[
                MDRaisedButton(
                    text="Continuar",
                    on_release=lambda x: self._guardar_nombre_global(content.text, dialog)
                )
            ],
        )
        dialog.open()

    def _guardar_nombre_global(self, nombre, dialog):
        if not nombre:
            return
        self.nombre_jugador_global = nombre
        if dialog:
            dialog.dismiss()

class MainScreen(MDScreen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.name = 'main'

    def jugar(self):
        app = MDApp.get_running_app()
        if isinstance(app, BingoApp):
            app.cambiar_pantalla('login', 'left')

    def mostrar_multijugador(self):
        app = MDApp.get_running_app()
        if isinstance(app, BingoApp):
            # Usar la pantalla de multijugador mejorada
            app.cambiar_pantalla('multiplayer_improved', 'left')

    def mostrar_instrucciones(self):
        instructions_text = """
        Instrucciones del Juego:

        1. Selecciona una categoría.
        2. Se te asignará un cartón con 8 preguntas.
        3. Responde las preguntas correctamente para marcar tu cartón.
        4. ¡Sé el primero en completar todas tus preguntas para ganar!

        Modo Multijugador:
        - Crea una sala o únete a una existente
        - Hasta 10 jugadores por sala
        - El anfitrión controla el inicio del juego
        - Todos los jugadores compiten simultáneamente
        """
        
        dialog = MDDialog(
            title="Instrucciones",
            text=instructions_text,
            buttons=[
                MDRaisedButton(
                    text="Cerrar",
                    on_release=lambda x: dialog.dismiss()
                )
            ],
        )
        dialog.open()

class LoginScreen(MDScreen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.name = 'login'
        self.selected_difficulty = "Facil"
        self.selected_num_ais = 1

    def update_difficulty(self, difficulty):
        """Actualiza la dificultad seleccionada y desactiva los otros switches."""
        self.selected_difficulty = difficulty
        # Desactivar otros switches
        if difficulty == "Facil":
            self.ids.moderate_difficulty.active = False
            self.ids.hard_difficulty.active = False
        elif difficulty == "Moderado":
            self.ids.easy_difficulty.active = False
            self.ids.hard_difficulty.active = False
        else:  # Dificil
            self.ids.easy_difficulty.active = False
            self.ids.moderate_difficulty.active = False

    def update_num_ais(self, num_ais):
        """Actualiza el número de IAs seleccionado y desactiva los otros switches."""
        self.selected_num_ais = num_ais
        # Desactivar otros switches
        if num_ais == 1:
            self.ids.three_ais.active = False
            self.ids.nine_ais.active = False
        elif num_ais == 3:
            self.ids.one_ai.active = False
            self.ids.nine_ais.active = False
        else:  # 9 IAs
            self.ids.one_ai.active = False
            self.ids.three_ais.active = False

    def start_game(self, player_name):
        if player_name:
            app = MDApp.get_running_app()
            if isinstance(app, BingoApp):
                app.player_name = player_name
                app.ai_difficulty = self.selected_difficulty
                app.num_ai_players = self.selected_num_ais

                # Iniciar la carga de datos y el juego
                if app.cargar_juego_data():
                    app.iniciar_juego_automatico() # Inicia el flujo de preguntas
                    app.cambiar_pantalla('game', 'up') # Cambiar a la pantalla de juego con animación
                else:
                    # Mostrar un mensaje de error si no se puede iniciar el juego
                    dialog = MDDialog(
                        title="Error",
                        text="No se pudo iniciar el juego. Inténtalo de nuevo más tarde.",
                        buttons=[
                            MDRaisedButton(
                                text="OK",
                                on_release=lambda x: dialog.dismiss()
                            )
                        ],
                    )
                    dialog.open()
        else:
            # Mostrar un mensaje al usuario si el nombre está vacío
            dialog = MDDialog(
                title="Error",
                text="Por favor, ingresa tu nombre para comenzar.",
                buttons=[
                    MDRaisedButton(
                        text="OK",
                        on_release=lambda x: dialog.dismiss()
                    )
                ],
            )
            dialog.open()

class LoadingScreen(MDScreen):
    FRASES_EDUCATIVAS = [
        'La educación es el arma más poderosa que puedes usar para cambiar el mundo. — Nelson Mandela',
        'Enseñar es sembrar en el alma de los demás. — Simón Rodríguez',
        'El maestro debe ser ejemplo, no solo palabra. — Luis Beltrán Prieto Figueroa',
        'La educación es la base de la libertad. — Andrés Bello',
        'Educar no es dar carrera para vivir, sino templar el alma para las dificultades de la vida. — Pitágoras',
        'La educación es el desarrollo en el hombre de toda la perfección de que su naturaleza es capaz. — Immanuel Kant',
        'Un ser sin estudios es un ser incompleto. — Simón Bolívar',
        'La educación es el principio con el que se construyen los pueblos. — José Martí',
        'La educación ayuda a la persona a aprender a ser lo que es capaz de ser. — Hesíodo',
        'La educación es la llave para abrir el mundo, un pasaporte a la libertad. — Oprah Winfrey',
        'La educación es el arte de hacer al hombre ético. — Georg Wilhelm Friedrich Hegel',
        'La educación es el vestido de gala para asistir a la fiesta de la vida. — Anónimo',
        'La educación es la vacuna contra la violencia. — Edward James Olmos',
        'La educación no cambia el mundo, cambia a las personas que van a cambiar el mundo. — Paulo Freire',
        'La educación es la base del progreso. — Rafael Caldera',
        'La educación es la mejor herencia. — Proverbio venezolano',
        'La educación es la luz que ilumina el camino de los pueblos. — Rómulo Gallegos',
        'La educación es la semilla de la libertad. — Cecilio Acosta',
        'La educación es la mejor inversión para el futuro. — Arturo Uslar Pietri',
        'La educación es la madre de la ciencia. — Simón Rodríguez',
    ]
    def on_enter(self):
        self.progress = 0
        self.ids = self.ids if hasattr(self, 'ids') else {}
        self.carga_completa = False
        self.animar_loading()
        self.simular_carga()
        self.frase_actual = ''
        self.cambiar_frase()
        # Esperar a que la pantalla tenga tamaño válido antes de animar destellos
        Clock.schedule_once(self.iniciar_destellos, 0.1)

    def animar_destellos(self):
        for i in range(1, 9):
            glow = self.ids.get(f'glow{i}')
            if glow:
                self.animar_punto(glow)

    def animar_punto(self, punto):
        # Mueve y destella el punto a una posición aleatoria
        w, h = self.width, self.height
        new_x = random.randint(40, int(w-40))
        new_y = random.randint(40, int(h-80))
        new_op = random.uniform(0.2, 0.8)
        new_size = random.randint(10, 26)
        anim = Animation(x=new_x, y=new_y, opacity=new_op, size=(new_size, new_size), duration=random.uniform(1.2,2.5), t='in_out_sine')
        anim.bind(on_complete=lambda *_: self.animar_punto(punto))
        anim.start(punto)

    def cambiar_frase(self, *args):
        if 'loading_quote' in self.ids:
            frase = random.choice(self.FRASES_EDUCATIVAS)
            while frase == self.frase_actual and len(self.FRASES_EDUCATIVAS) > 1:
                frase = random.choice(self.FRASES_EDUCATIVAS)
            self.frase_actual = frase
            quote = self.ids['loading_quote']
            Animation.cancel_all(quote)
            fade_out = Animation(opacity=0, duration=0.3)
            fade_in = Animation(opacity=1, duration=0.5)
            def set_text(*_):
                quote.text = frase
                fade_in.start(quote)
            fade_out.bind(on_complete=set_text)
            fade_out.start(quote)
            if not self.carga_completa:
                Clock.schedule_once(self.cambiar_frase, 2.5)

    def animar_loading(self):
        # Animación de entrada para el texto LOADING (fade in + rebote de tamaño)
        if 'loading_text' in self.ids:
            self.ids['loading_text'].opacity = 0
            self.ids['loading_text'].font_size = '40sp'
            anim = Animation(opacity=1, font_size=70, duration=0.7, t='out_back')
            anim.start(self.ids['loading_text'])

    def simular_carga(self):
        if 'loading_bar' in self.ids and 'loading_percent' in self.ids:
            self.ids['loading_bar'].value = self.progress
            # Animar el glow de la barra
            if 'bar_glow' in self.ids:
                bar = self.ids['loading_bar']
                glow = self.ids['bar_glow']
                new_x = bar.x + (bar.width-40) * (self.progress/bar.max)
                Animation.cancel_all(glow)
                anim = Animation(x=new_x, duration=0.1, t='out_quad')
                anim.start(glow)
            # Animación de color en el porcentaje
            actual = self.ids['loading_percent'].text
            # Asegurarse de que el texto no sea vertical
            if '\n' in actual:
                actual = actual.replace('\n', '')
            if actual.isdigit():
                actual = int(actual.replace('%',''))
            else:
                actual = 100
            if actual < self.progress:
                Animation.cancel_all(self.ids['loading_percent'])
                anim = Animation(text_color=(1,1,1,1), duration=0.05) + Animation(text_color=(0.2,0.7,1,1), duration=0.15)
                anim.start(self.ids['loading_percent'])
            if self.progress < 100:
                self.ids['loading_percent'].text = f"{self.progress}%"
            else:
                self.ids['loading_percent'].text = '¡Listo!'
        if self.progress < 100:
            self.progress += 1
            Clock.schedule_once(lambda dt: self.simular_carga(), 0.015)
        else:
            self.carga_completa = True
            # Mostrar y animar el mensaje de tap
            if 'loading_tap' in self.ids:
                self.ids['loading_tap'].opacity = 1
                self.animar_tap()

    def animar_tap(self):
        if 'loading_tap' in self.ids:
            tap = self.ids['loading_tap']
            tap.opacity = 1
            tap.font_size = '20sp'
            anim = (Animation(opacity=0.2, font_size=26, duration=0.7) + Animation(opacity=1, font_size=20, duration=0.7))
            anim.repeat = True
            anim.start(tap)

    def on_touch_down(self, touch):
        if self.carga_completa:
            app = MDApp.get_running_app()
            if app is not None and hasattr(app, 'sm') and app.sm:
                app.sm.current = 'main'
        return super().on_touch_down(touch)

    def iniciar_destellos(self, *args):
        if self.width > 100 and self.height > 100:
            self.animar_destellos()
        else:
            Clock.schedule_once(self.iniciar_destellos, 0.1)

class SplashScreen(MDScreen):
    def on_enter(self):
        from kivy.clock import Clock
        Clock.schedule_once(self.ir_a_loading, 2.5)
    def ir_a_loading(self, *args):
        app = MDApp.get_running_app()
        if app is not None and hasattr(app, 'sm') and app.sm:
            app.sm.current = 'loading'

class BingoApp(MDApp):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.cartones: Dict[str, List[Dict[str, Any]]] = {}
        self.cartones_jugador: List[Dict[str, Any]] = []
        self.cartones_ia: List[Dict[str, Any]] = []
        self.num_ai_players: int = 1
        self.preguntas_disponibles: List[Dict[str, Any]] = []
        self.preguntas_ya_usadas: List[Dict[str, Any]] = []
        self.categoria_actual: Optional[str] = None
        # self.db: Optional[Database] = None  # Eliminado para modo offline
        self.sounds: Dict[str, Any] = {}
        self.categorias = [
            'animales', 'deportes', 'geografia', 'historia', 'literatura', 'medicina', 'mujeres',
            'frases_celebres', 'inventos', 'transporte', 'arte', 'monumentos', 'matematicas', 'teologia', 'ciencia'
        ]
        self.game_in_progress = False
        self.player_name: str = "Jugador 1"
        self.ai_difficulty: str = "Moderado"
        self.ai_probabilities = {
            "Facil": 0.6,
            "Moderado": 0.75,
            "Dificil": 0.9
        }
        self.sm = None  # ScreenManager
        self.player_timer = None
        self.pregunta_actual_multijugador: Optional[Dict[str, Any]] = None # Para almacenar la pregunta actual del host
        print("BingoApp: Inicialización completada")

    def configurar_pantalla(self) -> None:
        """Configura el manejo de diferentes densidades de pantalla y orientaciones."""
        try:
            # Usar las utilidades de pantalla
            ScreenUtils.configure_window_for_device()
            
            # Obtener información de la pantalla
            density = ScreenUtils.get_screen_density()
            screen_size = ScreenUtils.get_screen_size()
            orientation = ScreenUtils.get_screen_orientation()
            
            print(f"[DEBUG] Densidad de pantalla: {density}")
            print(f"[DEBUG] Tamaño de pantalla: {screen_size}")
            print(f"[DEBUG] Orientación: {orientation}")
            
        except Exception as e:
            print(f"[WARNING] No se pudo configurar la pantalla específicamente: {e}")
            # Configuración por defecto
            Window.minimum_width = 320
            Window.minimum_height = 480

    def cargar_sonidos(self) -> None:
        # Crear directorio de sonidos si no existe
        if not os.path.exists('sounds'):
            os.makedirs('sounds')
            
        # Sonidos básicos
        self.sounds['click'] = SoundLoader.load('sounds/click.wav')
        self.sounds['correct'] = SoundLoader.load('sounds/correct.wav')
        self.sounds['wrong'] = SoundLoader.load('sounds/wrong.wav')
        self.sounds['bingo'] = SoundLoader.load('sounds/bingo.wav')
        
        # Ajustar volumen
        for sound in self.sounds.values():
            if sound:
                sound.volume = 0.5

    # def conectar_mongodb(self) -> None:  # Eliminado para modo offline
    #     try:
    #         mongo_url = os.getenv('MONGO_URL', 'mongodb://localhost:27017')
    #         client = MongoClient(mongo_url)
    #         self.db = client['bingo_educativo']
    #         # Verificar la conexión
    #         client.admin.command('ping')
    #         print("Conexión exitosa a MongoDB")
    #     except Exception as e:
    #         print(f"Error al conectar a MongoDB: {e}")
    #         self.db = None

    def build(self):
        print("BingoApp: Iniciando build")
        self.title = "Bingo Cultural"
        
        # Configurar manejo de diferentes densidades de pantalla
        self.configurar_pantalla()
        
        # Configurar el ScreenManager con diferentes transiciones
        self.sm = ScreenManager()
        
        # Cargar los archivos KV
        Builder.load_file("main.kv")
        Builder.load_file("multiplayer_improved.kv")
        
        # Agregar las pantallas con sus transiciones
        self.sm.add_widget(SplashScreen(name='splash'))
        self.sm.add_widget(LoadingScreen(name='loading'))
        self.sm.add_widget(LoginScreen())
        self.sm.add_widget(MainScreen())
        self.sm.add_widget(MultiplayerScreen())
        self.sm.add_widget(BluetoothScreen())
        
        # Agregar pantalla de multijugador mejorada
        from screens.multiplayer_screen_improved import MultiplayerScreenImproved
        self.sm.add_widget(MultiplayerScreenImproved())
        from screens.game_screen import GameScreen
        self.sm.add_widget(GameScreen(name='game'))
        
        # Cargar sonidos y conectar a MongoDB
        self.cargar_sonidos()
        # self.conectar_mongodb()
        
        print("BingoApp: Build completado")
        self.sm.current = 'splash'
        return self.sm

    def on_stop(self):
        # Manejar el cierre de la aplicación
        print("Cerrando la aplicación...")
        return True

    def seleccionar_categoria_aleatoria(self) -> str:
        # Esta función ya no es estrictamente necesaria para cargar preguntas, 
        # pero puede ser útil para mostrar la categoría principal del juego.
        # Podemos seguir seleccionando una categoría aleatoria para mostrarla en la UI.
        return random.choice(self.categorias)

    def cargar_juego_data(self) -> bool:
        """Carga todos los cartones y prepara las preguntas para el juego desde archivos JSON locales."""
        import os
        import json
        import random
        all_questions = []
        base_dir = 'cartones'
        try:
            # Recorrer cada categoría (carpeta)
            for categoria in self.categorias:
                categoria_dir = os.path.join(base_dir, categoria)
                if not os.path.isdir(categoria_dir):
                    print(f"[ADVERTENCIA] No existe la carpeta de categoría: {categoria} (se ignora)")
                    continue
                for archivo in os.listdir(categoria_dir):
                    if archivo.endswith('.json'):
                        ruta_archivo = os.path.join(categoria_dir, archivo)
                        try:
                            with open(ruta_archivo, 'r', encoding='utf-8') as f:
                                data = json.load(f)
                                preguntas = data.get('preguntas', [])
                                for i, pregunta in enumerate(preguntas):
                                    pregunta = pregunta.copy()
                                    pregunta['categoria'] = categoria
                                    pregunta['id'] = f"{categoria}_{archivo}_{i}"
                                    pregunta['respondida'] = False
                                    pregunta['correcta'] = False
                                    if 'opciones' in pregunta and isinstance(pregunta['opciones'], list):
                                        respuesta_correcta = pregunta.get('respuesta_correcta')
                                        opciones = pregunta['opciones'].copy()
                                        random.shuffle(opciones)
                                        pregunta['opciones'] = opciones
                                        if respuesta_correcta in opciones:
                                            pregunta['respuesta_correcta'] = respuesta_correcta
                                            pregunta['indice_correcto'] = opciones.index(respuesta_correcta)
                                    all_questions.append(pregunta)
                        except Exception as e:
                            print(f"Error procesando {ruta_archivo}: {e}")

            if not all_questions:
                print("No se encontraron preguntas en los archivos locales.")
                dialog = MDDialog(
                    title="Error",
                    text="No se encontraron preguntas en los archivos locales. Por favor, contacta al administrador.",
                    buttons=[
                        MDRaisedButton(
                            text="OK",
                            on_release=lambda x: dialog.dismiss()
                        )
                    ],
                )
                dialog.open()
                return False

            # Crear cartones mixtos
            cartones_mixtos = []
            required_cartones = 1 + self.num_ai_players  # 1 para jugador + IAs
            for _ in range(required_cartones):
                preguntas_seleccionadas = []
                categorias_usadas = set()
                # Seleccionar 8 preguntas aleatorias (de cualquier categoría)
                while len(preguntas_seleccionadas) < 8:
                    pregunta = random.choice(all_questions)
                    if pregunta not in preguntas_seleccionadas:
                        preguntas_seleccionadas.append(pregunta)
                        categorias_usadas.add(pregunta['categoria'])
                random.shuffle(preguntas_seleccionadas)
                carton = {
                    'preguntas': preguntas_seleccionadas,
                    'categorias': list(categorias_usadas),
                    'id': f"carton_{random.randint(100000, 999999)}",
                    'estructura': {
                        'filas': 2,
                        'columnas': 4
                    }
                }
                cartones_mixtos.append(carton)

            # Asignar cartones
            self.cartones_jugador = [cartones_mixtos[0]]
            self.cartones_ia = cartones_mixtos[1:]

            # Inicializar estado de preguntas para el jugador y las IAs
            all_players_cartones = self.cartones_jugador + self.cartones_ia
            for carton in all_players_cartones:
                if isinstance(carton, dict):
                    for pregunta in carton.get('preguntas', []) or []:
                        if isinstance(pregunta, dict):
                            pregunta['respondida'] = False
                            pregunta['correcta'] = False
                            if 'id' not in pregunta:
                                pregunta['id'] = f"{carton['id']}_{random.randint(100000, 999999)}"

            # Preparar lista de preguntas disponibles para el juego automático
            all_game_questions = []
            for carton in cartones_mixtos:
                if isinstance(carton, dict):
                    all_game_questions.extend(carton.get('preguntas', []) or [])
            self.preguntas_disponibles = list({pregunta['id']: pregunta for pregunta in all_game_questions if isinstance(pregunta, dict) and 'id' in pregunta}.values())
            random.shuffle(self.preguntas_disponibles)
            self.preguntas_ya_usadas = []

            return True
        except Exception as e:
            print(f"Error al cargar datos del juego: {e}")
            dialog = MDDialog(
                title="Error",
                text=f"Ocurrió un error al cargar los datos del juego: {str(e)}",
                buttons=[
                    MDRaisedButton(
                        text="OK",
                        on_release=lambda x: dialog.dismiss()
                    )
                ],
            )
            dialog.open()
            return False

    def asignar_cartones_jugador(self) -> bool:
        # Esta función ya no es necesaria, su lógica se integró en cargar_juego_data
        # La mantenemos solo para no romper llamadas existentes si las hay.
        # Verifica si los cartones ya fueron asignados.
        return len(self.cartones_jugador) > 0 and len(self.cartones_ia) == self.num_ai_players

    def obtener_pregunta_por_id(self, carton_id: str, pregunta_id: str) -> Optional[Dict[str, Any]]:
        # Esta función puede seguir siendo útil si necesitas encontrar una pregunta específica
        # Buscar en los cartones asignados (jugador e IAs)
        all_assigned_cartones = self.cartones_jugador + self.cartones_ia
        for carton in all_assigned_cartones:
            if isinstance(carton, Dict) and str(carton.get('_id')) == carton_id:
                for pregunta in carton.get('preguntas', []) or []:
                    if isinstance(pregunta, Dict) and pregunta.get('id') == pregunta_id:
                        return pregunta
        return None

    def verificar_bingo(self, carton: Dict[str, Any]) -> bool:
        """Verifica si un cartón tiene bingo (todas las preguntas respondidas correctamente)."""
        if not isinstance(carton, Dict):
            print("Error: Cartón no es un diccionario válido")
            return False
            
        preguntas = carton.get('preguntas', []) or []
        if not preguntas:
            print("Error: Cartón no tiene preguntas")
            return False
            
        # Contar preguntas respondidas correctamente
        preguntas_correctas = sum(1 for p in preguntas if isinstance(p, Dict) and p.get('respondida', False) and p.get('correcta', False))
        total_preguntas = len(preguntas)
        
        print(f"Verificando bingo - Preguntas correctas: {preguntas_correctas}/{total_preguntas}")
        
        # Verificar si todas las preguntas están respondidas correctamente
        tiene_bingo = preguntas_correctas == total_preguntas
        
        if tiene_bingo:
            print(f"¡Bingo detectado! Cartón: {carton.get('id', 'N/A')}")
            
        return tiene_bingo

    def iniciar_juego_automatico(self):
        """Inicia el flujo de preguntas automáticas"""
        print("DEBUG: Iniciando juego automático")
        # Nos aseguramos de que se cargaron los datos antes de iniciar el juego
        if not self.cartones_jugador or not self.cartones_ia or not self.preguntas_disponibles:
             print("Error al iniciar el juego: Datos no cargados correctamente.")
             # Mostrar un mensaje al usuario si es posible
             game_screen = None
             if self.sm:
                  game_screen = self.sm.get_screen('game')
             if game_screen and hasattr(game_screen, 'mostrar_dialogo'):
                  game_screen.mostrar_dialogo("Error de Inicio", "No se pudieron cargar los datos del juego. Inténtalo de nuevo.")
             return

        self.game_in_progress = True
        
        # Asegurarse de que la pantalla de juego muestre el cartón inicial
        game_screen = None
        if self.sm:
             game_screen = self.sm.get_screen('game')
             if game_screen:
                  print("DEBUG: Mostrando cartón inicial")
                  game_screen.mostrar_cartones() # Mostrar el cartón del jugador
                  # Esperar un momento antes de mostrar la primera pregunta
                  Clock.schedule_once(lambda dt: self.mostrar_siguiente_pregunta(), 1)

    def mostrar_siguiente_pregunta(self):
        """Selecciona y muestra la siguiente pregunta aleatoria (una ronda)."""
        if not self.game_in_progress or not self.preguntas_disponibles:
            print("No quedan preguntas disponibles o juego no en progreso. Terminando juego.")
            self.terminar_juego() 
            return

        # Seleccionar una pregunta aleatoria del pool
        pregunta_actual_data = random.choice(self.preguntas_disponibles)
        print(f"DEBUG (main.py): Sacando pregunta (Ronda): {pregunta_actual_data.get('pregunta', '')}")

        # Verificar si esta pregunta está en algún cartón
        all_players_cartones = self.cartones_jugador + self.cartones_ia
        
        # Encontrar todos los cartones que tienen esta pregunta
        cartones_con_pregunta = []
        for carton in all_players_cartones:
            if isinstance(carton, Dict):
                pregunta_en_carton = next((p for p in carton.get('preguntas', []) or [] if isinstance(p, Dict) and p.get('id') == pregunta_actual_data.get('id')), None)
                if pregunta_en_carton:
                    cartones_con_pregunta.append((carton, pregunta_en_carton))

        # Si la pregunta no está en ningún cartón, pasar a la siguiente
        if not cartones_con_pregunta:
            print("Pregunta no encontrada en ningún cartón. Pasando a la siguiente.")
            game_screen = None
            if self.sm:
                game_screen = self.sm.get_screen('game')
                if game_screen and hasattr(game_screen, 'clear_question_area'):
                    game_screen.clear_question_area()
                    if hasattr(game_screen.ids, 'game_messages'):
                        game_screen.ids.game_messages.text = "Nadie tiene esta pregunta. Pasando a la siguiente..."
                        Clock.schedule_once(lambda dt: setattr(game_screen.ids.game_messages, 'text', ''), 2)

            # Programar la siguiente pregunta después de un breve retraso
            Clock.schedule_once(lambda dt: self.mostrar_siguiente_pregunta(), 1)
            return

        # Verificar si la pregunta está en el cartón del jugador
        pregunta_en_carton_jugador = next((p for p in self.cartones_jugador[0].get('preguntas', []) or [] if isinstance(p, Dict) and p.get('id') == pregunta_actual_data.get('id')), None)
        
        # Encontrar las preguntas en los cartones de las IAs que no han respondido
        preguntas_en_cartones_ia = [(carton, p_ia) for carton, p_ia in cartones_con_pregunta if carton in self.cartones_ia and not p_ia.get('respondida', False)]

        game_screen = None
        if self.sm:
            game_screen = self.sm.get_screen('game')
            
        # Mostrar la pregunta en la pantalla del juego
        if game_screen and hasattr(game_screen, 'mostrar_pregunta_en_ui'):
            game_screen.mostrar_pregunta_en_ui(pregunta_actual_data)
            
        # Lógica de notificación si la pregunta está en múltiples cartones
        if len(cartones_con_pregunta) > 1:
            if game_screen and hasattr(game_screen.ids, 'game_messages'):
                if pregunta_en_carton_jugador:
                    game_screen.ids.game_messages.text = f"¡Esta pregunta está en {len(cartones_con_pregunta)} cartones! ¡Todos pueden responder!"
                else:
                    game_screen.ids.game_messages.text = f"Esta pregunta no está en tu cartón. Las IAs están respondiendo..."
                    Clock.schedule_once(lambda dt: setattr(game_screen.ids.game_messages, 'text', ''), 3)

        # Lógica de respuesta y avance del juego
        if pregunta_en_carton_jugador and not pregunta_en_carton_jugador.get('respondida', False):
            print("Jugador tiene la pregunta. Iniciando temporizador de respuesta del jugador (15 segundos).")
            if self.game_in_progress:
                self.start_player_timer()
                # No programar respuestas de IA hasta que el jugador responda o se agote el tiempo
                return
        else:
            # Si el jugador no tiene la pregunta, programar respuestas de IA y avanzar
            if self.game_in_progress:
                # Programar respuestas de las IAs que tienen la pregunta y no han respondido
                for ia_carton, pregunta_ia in preguntas_en_cartones_ia:
                    # Reducir el tiempo de respuesta de la IA
                    ia_delay = random.uniform(1, 3)  # Reducido de 3-10 a 1-3 segundos
                    print(f"IA tiene la pregunta. Programando respuesta de IA ({ia_carton.get('categoria', 'N/A')}) en {ia_delay:.2f} segundos.")
                    Clock.schedule_once(lambda dt, ia_carton=ia_carton, p_ia=pregunta_ia: self.ia_responder(ia_carton, p_ia), ia_delay)
                
                # Programar la siguiente pregunta después de que todas las IAs hayan respondido
                max_delay = max([random.uniform(1, 3) for _ in preguntas_en_cartones_ia]) if preguntas_en_cartones_ia else 1
                Clock.schedule_once(lambda dt: self.mostrar_siguiente_pregunta(), max_delay + 1)  # Reducido a 1 segundo extra

    def process_player_answer(self, pregunta: Dict[str, Any], selected_option_index: int):
        """Procesa la respuesta del jugador humano."""
        # Cancelar el temporizador del jugador ya que ha respondido
        self.cancel_player_timer()

        print("Después de cancelar temporizador.")

        # Asegurarse de que el juego sigue en progreso y hay cartones de jugador
        if not self.game_in_progress or not self.cartones_jugador:
            print("Juego no en progreso o cartones del jugador vacíos. Saliendo de process_player_answer.")
            return
        
        player_carton = self.cartones_jugador[0]
        
        # Encontrar la pregunta en el cartón del jugador por ID
        pregunta_en_carton = next((p for p in player_carton.get('preguntas', []) or [] if isinstance(p, Dict) and p.get('id') == pregunta.get('id')), None)

        if not pregunta_en_carton:
            print("Error: Pregunta del jugador no encontrada en el cartón al procesar respuesta.")
            # Avanzar a la siguiente ronda
            if self.game_in_progress:
                Clock.schedule_once(lambda dt: self.mostrar_siguiente_pregunta(), 1)
            return

        # Verificar si la respuesta es correcta usando el índice correcto
        is_correct = selected_option_index == pregunta.get('indice_correcto', -1)

        # Actualizar el estado de la pregunta en el cartón
        pregunta_en_carton['respondida'] = True
        pregunta_en_carton['correcta'] = is_correct
        
        print(f"Pregunta marcada en cartón jugador: {pregunta.get('pregunta', '')}, Correcta: {is_correct}")

        # Manejar el estado de la pregunta en el pool
        if is_correct:
            # Si la respuesta es correcta, remover la pregunta del pool
            self.preguntas_disponibles = [p for p in self.preguntas_disponibles if p.get('id') != pregunta.get('id')]
            # Agregar la pregunta a preguntas_ya_usadas si no está
            if not any(p.get('id') == pregunta.get('id') for p in self.preguntas_ya_usadas):
                self.preguntas_ya_usadas.append(pregunta)
            print("Respuesta correcta. Pregunta removida del pool.")
        else:
            # Si la respuesta es incorrecta, asegurarse de que la pregunta esté en el pool
            if not any(p.get('id') == pregunta.get('id') for p in self.preguntas_disponibles):
                # Crear una copia de la pregunta para el pool
                pregunta_pool = pregunta.copy()
                pregunta_pool['respondida'] = False  # Resetear el estado
                pregunta_pool['correcta'] = False    # Resetear el estado
                self.preguntas_disponibles.append(pregunta_pool)
                print("Respuesta incorrecta. Pregunta agregada al pool con estado reseteado.")
            # También resetear el estado en el cartón del jugador para que pueda volver a responderse
            if pregunta_en_carton:
                pregunta_en_carton['respondida'] = False
                pregunta_en_carton['correcta'] = False

        # Actualizar la interfaz del cartón del jugador
        if self.sm:
            game_screen = self.sm.get_screen('game')
            if game_screen and hasattr(game_screen, 'mostrar_cartones'):
                game_screen.mostrar_cartones() # Refresh player's card display
                print("Cartón del jugador actualizado en la UI.")

        # Mostrar feedback al jugador (sonido)
        if is_correct:
            if self.sounds.get('correct'):
                self.sounds['correct'].play()
                print("Sonido de respuesta correcta.")
        else:
            if self.sounds.get('wrong'):
                self.sounds['wrong'].play()
                print("Sonido de respuesta incorrecta.")

        # Verificar si alguna IA ha ganado
        # for i, carton_ia in enumerate(self.cartones_ia, 1):
        #     if self.verificar_bingo(carton_ia):
        #         print(f"¡Bingo de la IA {i}!")
        #         self.terminar_juego(winner=f"IA_{i}")
        #         return
        
        # Si no hay bingo, avanzar a la siguiente ronda
        print("Verificando si el juego está en progreso para programar la siguiente pregunta después de respuesta del jugador...")
        if self.game_in_progress:
            print("Programando siguiente pregunta después de respuesta del jugador...")
            # Pequeño retraso antes de la siguiente pregunta para dar tiempo a ver el feedback
            Clock.schedule_once(lambda dt: self.mostrar_siguiente_pregunta(), 1)
        else:
            print("Juego no está en progreso, no se programa la siguiente pregunta después de respuesta del jugador.")

    def handle_player_timeout(self):
        """Maneja el caso en que el jugador no responde a tiempo."""
        print("Tiempo del jugador agotado.")
        if not self.game_in_progress or not self.cartones_jugador or not self.preguntas_ya_usadas: # Asegurarse de que hay una pregunta actual
             return
        # Marcar la última pregunta mostrada al jugador como no respondida/incorrecta en su cartón
        pregunta_actual_data = self.preguntas_ya_usadas[-1] if self.preguntas_ya_usadas else None
        player_carton = self.cartones_jugador[0]
        pregunta_en_carton = None
        if pregunta_actual_data:
            pregunta_en_carton = next((p for p in player_carton.get('preguntas', []) or [] if isinstance(p, Dict) and p.get('id') == pregunta_actual_data.get('id')), None)
        if pregunta_en_carton and not pregunta_en_carton.get('respondida', False): # Solo si no estaba respondida ya
            pregunta_en_carton['respondida'] = True # Marcar como respondida (por timeout)
            pregunta_en_carton['correcta'] = False # Considerar incorrecta o no respondida
            if pregunta_actual_data:
                print(f"Pregunta '{pregunta_actual_data.get('pregunta', '')}' marcada como incorrecta por timeout del jugador.")
            # Actualizar UI del cartón del jugador para reflejar el estado incorrecto
            if self.sm:
                game_screen = self.sm.get_screen('game')
                if game_screen and hasattr(game_screen, 'mostrar_cartones'):
                     game_screen.mostrar_cartones() # Refresh player's card display
                     print("Cartón del jugador actualizado en la UI después de timeout.")
        # Limpiar el área de pregunta actual en la UI
        game_screen = None
        if self.sm:
             game_screen = self.sm.get_screen('game')
             if game_screen and hasattr(game_screen, 'clear_question_area'):
                  game_screen.clear_question_area()
        # Mostrar un mensaje indicando que el tiempo se agotó y continuar automáticamente
        if game_screen and hasattr(game_screen, 'mostrar_dialogo'):
            # Mostrar el diálogo
            game_screen.mostrar_dialogo("Se acabó el tiempo", "No respondiste a tiempo. Pasando a la siguiente pregunta.")
            # Cerrar el diálogo y continuar después de 1 segundo
            def cerrar_y_continuar(dt):
                if hasattr(game_screen, 'dialog') and game_screen.dialog:
                    game_screen.dialog.dismiss()
                # Avanzar a la siguiente pregunta SIEMPRE
                if self.game_in_progress:
                    self.mostrar_siguiente_pregunta()
            Clock.schedule_once(cerrar_y_continuar, 1)
        else:
            # Si no se puede mostrar diálogo, pasar directamente a la siguiente pregunta
            if self.game_in_progress:
                self.mostrar_siguiente_pregunta()

    def start_player_timer(self):
        """Inicia el temporizador para la respuesta del jugador y actualiza el contador visual cada segundo."""
        # Cancelar cualquier temporizador existente para evitar múltiples temporizadores corriendo
        if hasattr(self, 'player_timer') and self.player_timer:
            self.player_timer.cancel()
        if hasattr(self, 'player_timer_event') and self.player_timer_event:
            self.player_timer_event.cancel()

        self.player_time_left = 15
        game_screen = None
        if self.sm:
            game_screen = self.sm.get_screen('game')
        if game_screen and hasattr(game_screen, 'update_timer_label'):
            game_screen.update_timer_label(self.player_time_left)

        def update_timer(dt):
            self.player_time_left -= 1
            if self.player_time_left > 0:
                if game_screen and hasattr(game_screen, 'update_timer_label'):
                    game_screen.update_timer_label(self.player_time_left)
            else:
                if game_screen and hasattr(game_screen, 'update_timer_label'):
                    game_screen.update_timer_label(0)
                if hasattr(self, 'player_timer_event') and self.player_timer_event:
                    self.player_timer_event.cancel()

        # Programar el temporizador visual cada segundo
        self.player_timer_event = Clock.schedule_interval(update_timer, 1)
        # Programar el timeout real
        self.player_timer = Clock.schedule_once(lambda dt: self.handle_player_timeout(), self.player_time_left)
        print("Temporizador del jugador iniciado (15 segundos y contador visual).")

    def cancel_player_timer(self):
        """Cancela el temporizador de respuesta del jugador y oculta el contador visual."""
        if hasattr(self, 'player_timer') and self.player_timer:
            self.player_timer.cancel()
            print("Temporizador del jugador cancelado.")
        if hasattr(self, 'player_timer_event') and self.player_timer_event:
            self.player_timer_event.cancel()
        game_screen = None
        if self.sm:
            game_screen = self.sm.get_screen('game')
        if game_screen and hasattr(game_screen, 'update_timer_label'):
            game_screen.update_timer_label(0)

    def calcular_estadisticas(self, carton: Dict[str, Any]) -> Dict[str, int]:
        """Calcula las estadísticas de un cartón (aciertos y desaciertos)."""
        if not isinstance(carton, Dict):
            return {'aciertos': 0, 'desaciertos': 0}
            
        preguntas = carton.get('preguntas', []) or []
        aciertos = sum(1 for p in preguntas if isinstance(p, Dict) and p.get('respondida', False) and p.get('correcta', False))
        desaciertos = sum(1 for p in preguntas if isinstance(p, Dict) and p.get('respondida', False) and not p.get('correcta', False))
        
        return {
            'aciertos': aciertos,
            'desaciertos': desaciertos
        }

    def terminar_juego(self, winner: Optional[str] = None):
        """Termina el juego y muestra el resultado con estadísticas"""
        # Si el juego ya no está en progreso, salir para evitar duplicados
        if not self.game_in_progress and hasattr(self, '_game_finished_dialog_shown') and self._game_finished_dialog_shown:
            print("DEBUG: terminar_juego llamado pero juego ya terminado y diálogo mostrado.")
            return

        self.game_in_progress = False
        self._game_finished_dialog_shown = True # Marcar que el diálogo se mostrará
        
        print(f"DEBUG: Terminando juego. Ganador: {winner}")

        # Calcular estadísticas para todos los jugadores
        estadisticas = []
        
        # Estadísticas del jugador
        if self.cartones_jugador:
            stats_jugador = self.calcular_estadisticas(self.cartones_jugador[0])
            estadisticas.append({
                'nombre': self.player_name,
                'aciertos': stats_jugador['aciertos'],
                'desaciertos': stats_jugador['desaciertos']
            })
        
        # Estadísticas de las IAs
        for i, carton_ia in enumerate(self.cartones_ia, 1):
            stats_ia = self.calcular_estadisticas(carton_ia)
            estadisticas.append({
                'nombre': f"IA {i}",
                'aciertos': stats_ia['aciertos'],
                'desaciertos': stats_ia['desaciertos']
            })
        
        # Crear mensaje de victoria unificado
        if winner == "player":
            win_message = "¡Felicidades! Has ganado."
        elif isinstance(winner, str) and winner.startswith("IA_"):
            win_message = f"La IA ha ganado."
        elif winner and isinstance(winner, str) and winner.startswith("Jugador_"):
            win_message = f"¡Felicidades! Has ganado."
        else:
            win_message = "El juego ha terminado."
        
        # Limpiar datos del juego
        self.preguntas_disponibles = []
        self.preguntas_ya_usadas = []
        self.cartones_jugador = []
        self.cartones_ia = []

        game_screen = None
        if self.sm:
            game_screen = self.sm.get_screen('game')

        if game_screen and hasattr(game_screen, 'clear_question_area'):
            game_screen.clear_question_area()

        if game_screen and hasattr(game_screen, 'mostrar_dialogo'):
            # Crear un layout para el contenido del diálogo
            content = MDBoxLayout(
                orientation='vertical',
                spacing='10dp',
                padding='10dp',
                size_hint_y=None,
                height='300dp'  # Aumentamos la altura total
            )
            
            # Agregar el mensaje de victoria unificado
            win_label = MDLabel(
                text=win_message,
                halign="center",
                font_style="H6",
                size_hint_y=None,
                height='40dp',
                theme_text_color="Custom",
                text_color=(1, 0.84, 0, 1)  # Color dorado/amarillo llamativo
            )
            content.add_widget(win_label)
            
            # Crear un scroll view para las estadísticas
            scroll = MDScrollView(
                size_hint=(1, None),
                height='200dp',  # Aumentamos la altura del scroll
                do_scroll_x=False,  # Deshabilitamos scroll horizontal
                do_scroll_y=True    # Habilitamos scroll vertical
            )
            
            # Layout para las estadísticas
            stats_layout = MDBoxLayout(
                orientation='vertical',
                spacing='5dp',
                size_hint_y=None,
                height='200dp',
                md_bg_color=(0.3, 0.3, 0.3, 1) # Fondo oscuro para las estadísticas
            )
            
            # Agregar las estadísticas
            for stat in estadisticas:
                player_stats = MDBoxLayout(
                    orientation='vertical',
                    spacing='2dp',
                    size_hint_y=None,
                    height='50dp'  # Altura más compacta para cada jugador
                )
                
                name_label = MDLabel(
                    text=stat['nombre'],
                    theme_text_color="Custom",
                    text_color=(1, 1, 1, 1),
                    size_hint_y=None,
                    height='20dp'
                )
                stats_label = MDLabel(
                    text=f"Aciertos: {stat['aciertos']} | Desaciertos: {stat['desaciertos']}",
                    theme_text_color="Custom",
                    text_color=(0.7, 0.7, 0.7, 1),
                    size_hint_y=None,
                    height='20dp'
                )
                
                player_stats.add_widget(name_label)
                player_stats.add_widget(stats_label)
                stats_layout.add_widget(player_stats)
            
            scroll.add_widget(stats_layout)
            content.add_widget(scroll)
            
            # Crear botones para el diálogo
            buttons = [
                MDRaisedButton(
                    text="Nuevo Juego",
                    on_release=lambda x: self.iniciar_nuevo_juego(dialog)
                ),
                MDRaisedButton(
                    text="Salir",
                    on_release=lambda x: self.salir_juego(dialog)
                )
            ]
            
            # Mostrar el diálogo con el contenido personalizado
            dialog = MDDialog(
                title="Fin del Juego",
                type="custom",
                content_cls=content,
                buttons=buttons,
                md_bg_color=(0.15, 0.15, 0.15, 1) # Fondo gris oscuro para el diálogo
            )
            dialog.open()

    def iniciar_nuevo_juego(self, dialog):
        """Inicia un nuevo juego y cierra el diálogo actual."""
        if dialog:
            dialog.dismiss()
        self.cambiar_pantalla('login', 'right')

    def salir_juego(self, dialog):
        """Sale del juego y cierra el diálogo actual."""
        if dialog:
            dialog.dismiss()
        self.cambiar_pantalla('main', 'right')

    def ia_responder(self, ia_carton: Dict[str, Any], pregunta_actual_data: Dict[str, Any]):
        """Simula la respuesta de una IA específica a una pregunta específica."""
        # Asegurarse de que el juego sigue en progreso y los datos son válidos
        if not self.game_in_progress or not isinstance(ia_carton, Dict) or not isinstance(pregunta_actual_data, Dict):
            return
            
        print(f"IA está respondiendo a la pregunta: {pregunta_actual_data.get('pregunta', '')}")

        # Encontrar la pregunta en el cartón de la IA
        pregunta_en_carton_ia = next((p for p in ia_carton.get('preguntas', []) or [] 
                                    if isinstance(p, Dict) and p.get('id') == pregunta_actual_data.get('id')), None)

        if not pregunta_en_carton_ia or pregunta_en_carton_ia.get('respondida', False):
            print(f"IA no tiene o ya respondió la pregunta '{pregunta_actual_data.get('pregunta', '')}' en su cartón.")
            return

        # Lógica de respuesta de la IA basada en la dificultad
        correct_probability = self.ai_probabilities.get(self.ai_difficulty, 0.75)
        is_correct_ia = random.random() < correct_probability

        # Actualizar el estado de la pregunta en el cartón de la IA
        pregunta_en_carton_ia['respondida'] = True
        pregunta_en_carton_ia['correcta'] = is_correct_ia

        # Si la respuesta es correcta, remover la pregunta del pool
        if is_correct_ia:
            self.preguntas_disponibles = [p for p in self.preguntas_disponibles if p.get('id') != pregunta_actual_data.get('id')]
            print(f"IA ({ia_carton.get('categoria', 'N/A')}) respondió correctamente la pregunta.")
        else:
            # Si la respuesta es incorrecta, asegurarse de que la pregunta esté en el pool
            if not any(p.get('id') == pregunta_actual_data.get('id') for p in self.preguntas_disponibles):
                pregunta_pool = pregunta_actual_data.copy()
                pregunta_pool['respondida'] = False
                pregunta_pool['correcta'] = False
                self.preguntas_disponibles.append(pregunta_pool)
            print(f"IA ({ia_carton.get('categoria', 'N/A')}) respondió incorrectamente la pregunta.")

        # Verificar si hay bingo para la IA
        if self.verificar_bingo(ia_carton):
            print(f"¡Bingo de la IA! Cartón: {ia_carton.get('id', 'N/A')}")
            self.terminar_juego(winner=f"IA_{ia_carton.get('id', 'N/A')}")
            return

        # Actualizar la UI del cartón del jugador para reflejar los cambios
        if self.sm:
            game_screen = self.sm.get_screen('game')
            if game_screen and hasattr(game_screen, 'mostrar_cartones'):
                game_screen.mostrar_cartones()

        # Llamar a la función para que la IA cante bingo si corresponde
        for i, carton in enumerate(self.cartones_ia):
            if carton is ia_carton:
                self.ia_cantar_bingo(i, carton)
                break

    def ia_cantar_bingo(self, ia_index, carton_ia):
        """Permite que la IA cante bingo si tiene el cartón completo."""
        if self.verificar_bingo(carton_ia):
            print(f"¡Bingo de la IA {ia_index+1}!")
            self.terminar_juego(winner=f"IA_{ia_index+1}")

    def cambiar_pantalla(self, nombre_pantalla: str, direccion: str = 'left'):
        """Cambia a una pantalla con una animación de transición."""
        if not self.sm:
            return
            
        # Configurar la transición según la dirección
        if direccion == 'left':
            self.sm.transition = SlideTransition(direction='left')
        elif direccion == 'right':
            self.sm.transition = SlideTransition(direction='right')
        elif direccion == 'up':
            self.sm.transition = SlideTransition(direction='up')
        elif direccion == 'down':
            self.sm.transition = SlideTransition(direction='down')
        else:
            self.sm.transition = FadeTransition()
            
        # Cambiar a la pantalla
        self.sm.current = nombre_pantalla

    def mostrar_siguiente_pregunta_multijugador(self):
        """El host envía la siguiente pregunta de la lista global a todos los clientes y la muestra localmente."""
        app = MDApp.get_running_app()
        if not isinstance(app, BingoApp):
            return
        if not app.preguntas_disponibles:
            print("No quedan preguntas disponibles. Terminando juego.")
            self.terminar_juego_multijugador()
            return
        # Seleccionar la siguiente pregunta (puedes usar pop(0) para avanzar secuencialmente)
        pregunta_actual = app.preguntas_disponibles.pop(0)
        app.preguntas_ya_usadas.append(pregunta_actual)
        # Enviar la pregunta a todos los clientes
        import json
        for client, addr in self.connected_players:
            try:
                data = {'tipo': 'pregunta_turno', 'pregunta': pregunta_actual}
                client.send(json.dumps(data).encode('utf-8'))
                print(f"[DEBUG] Pregunta de turno enviada a {addr}")
            except Exception as e:
                print(f"[ERROR] No se pudo enviar pregunta a {addr}: {e}")
        # Mostrar la pregunta localmente (host)
        if app.sm:
            game_screen = app.sm.get_screen('game')
            if game_screen and hasattr(game_screen, 'mostrar_pregunta_en_ui'):
                game_screen.mostrar_pregunta_en_ui(pregunta_actual)

    def recibir_mensajes_cliente(self):
        # Verifica que el socket esté inicializado
        if not self.client_socket:
            print("[ERROR] El socket del cliente no está inicializado.")
            return
        try:
            while True:
                data = self.client_socket.recv(65536)
                if not data:
                    print("[ERROR] No se recibió información del servidor.")
                    break
                import json
                info = json.loads(data.decode('utf-8'))
                print(f"[DEBUG] Datos recibidos del host: {info.keys()}")
                app = MDApp.get_running_app()
                if isinstance(app, BingoApp):
                    if 'carton' in info and 'preguntas_globales' in info:
                        # Asignar el cartón y la lista global de preguntas al cliente (inicio de partida)
                        app.cartones_jugador = [info['carton']]
                        app.preguntas_disponibles = info['preguntas_globales']
                        app.preguntas_ya_usadas = []
                        app.game_in_progress = True
                        print("[DEBUG] Cartón y preguntas globales asignados al cliente.")
                        app.cambiar_pantalla('game', 'up')
                        # Iniciar el flujo de preguntas de manera autónoma
                        if hasattr(app, 'iniciar_juego_automatico'):
                            app.iniciar_juego_automatico()
        except Exception as e:
            print(f"[ERROR] Al recibir datos del host: {e}")

# Keep MainScreen and GameScreen classes as they define the UI structure based on the .kv file
# However, GameScreen will be instantiated and managed by the ScreenManager in build method
# The logic for question display and handling is now in BingoApp

if __name__ == '__main__':
    BingoApp().run() 