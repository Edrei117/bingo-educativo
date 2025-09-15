"""
Pantalla de Multijugador Mejorada
Versión con mejor manejo de errores y conexiones
"""

from kivymd.uix.screen import MDScreen
from kivymd.uix.button import MDRaisedButton
from kivymd.uix.label import MDLabel
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.card import MDCard
from kivymd.uix.dialog import MDDialog
from kivy.clock import Clock
from kivy.metrics import dp, sp
from kivy.properties import BooleanProperty, StringProperty
from typing import Optional, Dict, Any
import threading
import json
import random
import os

from utils.multiplayer_utils import ConnectionManager, MultiplayerUtils
from kivymd.app import MDApp

# Importar la aplicación principal
BingoApp = None
try:
    from main import BingoApp
except ImportError:
    pass

class MultiplayerScreenImproved(MDScreen):
    """Pantalla de multijugador mejorada"""
    
    # Propiedades reactivas
    is_host = BooleanProperty(False)
    modo_seleccionado = StringProperty('wifi')
    nombre_jugador_global = StringProperty('')
    connection_status = StringProperty('Desconectado')
    room_info = StringProperty('')
    local_ip = StringProperty('')
    player_count = StringProperty('0/10')
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.name = 'multiplayer_improved'
        
        # Gestor de conexiones
        self.connection_manager = ConnectionManager()
        self.setup_connection_handlers()
        
        # Estado del juego
        self.game_started = False
        self.current_dialog = None
        
        print("[DEBUG] MultiplayerScreenImproved inicializada")
    
    def setup_connection_handlers(self):
        """Configura los manejadores de eventos de conexión"""
        if hasattr(self.connection_manager, 'on_data_received'):
            self.connection_manager.on_data_received = self.handle_data_received
        if hasattr(self.connection_manager, 'on_player_connected'):
            self.connection_manager.on_player_connected = self.handle_player_connected
        if hasattr(self.connection_manager, 'on_player_disconnected'):
            self.connection_manager.on_player_disconnected = self.handle_player_disconnected
        if hasattr(self.connection_manager, 'on_connection_lost'):
            self.connection_manager.on_connection_lost = self.handle_connection_lost
    
    def seleccionar_modo(self, modo):
        """Selecciona el modo de conexión"""
        self.modo_seleccionado = modo
        print(f"[DEBUG] Modo multijugador seleccionado: {modo}")
        
        # Actualizar UI según el modo
        if hasattr(self.ids, 'wifi_options'):
            self.ids.wifi_options.opacity = 1 if modo == 'wifi' else 0
            self.ids.wifi_options.disabled = False if modo == 'wifi' else True
        
        if hasattr(self.ids, 'bluetooth_options'):
            self.ids.bluetooth_options.opacity = 1 if modo == 'bluetooth' else 0
            self.ids.bluetooth_options.disabled = False if modo == 'bluetooth' else True
    
    def crear_sala(self):
        """Crea una nueva sala de juego"""
        try:
            print("[DEBUG] Intentando crear sala...")
            
            # Iniciar servidor
            if not self.connection_manager.start_server(5000):
                self.show_error("No se pudo crear la sala. Verifica que el puerto 5000 esté disponible.")
                return
            
            # Actualizar estado
            self.is_host = True
            self.connection_status = f"Sala creada - Código: {self.connection_manager.room_code}"
            self.room_info = "Esperando jugadores..."
            self.local_ip = f"IP local: {MultiplayerUtils.get_local_ip()}"
            self.player_count = "1/10"
            
            # Mostrar botón de iniciar juego
            if hasattr(self.ids, 'start_game_button'):
                self.ids.start_game_button.opacity = 1
                self.ids.start_game_button.disabled = False
            
            print(f"[DEBUG] Sala creada exitosamente. Código: {self.connection_manager.room_code}")
            
        except Exception as e:
            print(f"[ERROR] Error al crear sala: {e}")
            self.show_error(f"Error al crear sala: {str(e)}")
    
    def unirse_sala(self):
        """Muestra diálogo para unirse a una sala"""
        def on_ip_entered(ip):
            if not MultiplayerUtils.validate_ip(ip):
                self.show_error("IP inválida. Ingresa una IP válida (ej: 192.168.1.10)")
                return
            
            self.conectar_a_host(ip)
        
        MultiplayerUtils.show_input_dialog(
            "Unirse a Sala",
            "Ingresa la IP del host (ej: 192.168.1.10)",
            on_ip_entered
        )
    
    def conectar_a_host(self, ip_host):
        """Conecta a un host específico"""
        try:
            print(f"[DEBUG] Intentando conectar a {ip_host}...")
            
            # Conectar al servidor
            if not self.connection_manager.connect_to_server(ip_host, 5000):
                self.show_error(f"No se pudo conectar a {ip_host}. Verifica la IP y que el host esté disponible.")
                return
            
            # Actualizar estado
            self.is_host = False
            self.connection_status = f"Conectado a {ip_host}"
            self.room_info = "Conectado como jugador"
            self.local_ip = ""
            self.player_count = "1/10"
            
            print(f"[DEBUG] Conectado exitosamente a {ip_host}")
            
        except Exception as e:
            print(f"[ERROR] Error al conectar: {e}")
            self.show_error(f"Error al conectar: {str(e)}")
    
    def handle_data_received(self, data: Dict[str, Any], addr: Optional[tuple]):
        """Maneja los datos recibidos"""
        try:
            print(f"[DEBUG] Datos recibidos: {list(data.keys())}")
            
            app = MDApp.get_running_app()
            if not hasattr(app, 'cambiar_pantalla'):
                print("ERROR: La aplicación no es una instancia de BingoApp")
                return
            
            # Manejar diferentes tipos de datos
            if 'type' in data:
                if data['type'] == 'game_start':
                    self.handle_game_start(data)
                elif data['type'] == 'question':
                    self.handle_question(data)
                elif data['type'] == 'bingo':
                    self.handle_bingo(data)
                elif data['type'] == 'player_answer':
                    self.handle_player_answer(data, addr)
            
            # Datos de inicio de juego (compatibilidad)
            elif 'carton' in data and 'preguntas_globales' in data:
                self.handle_game_data(data)
                
        except Exception as e:
            print(f"[ERROR] Error al procesar datos recibidos: {e}")
    
    def handle_game_data(self, data: Dict[str, Any]):
        """Maneja los datos de inicio de juego"""
        try:
            app = MDApp.get_running_app()
            if not hasattr(app, 'cambiar_pantalla'):
                print("ERROR: La aplicación no es una instancia de BingoApp")
                return
            
            # Asignar cartón y preguntas
            app.cartones_jugador = [data['carton']]
            app.preguntas_disponibles = data['preguntas_globales']
            app.preguntas_ya_usadas = []
            app.game_in_progress = True
            
            print("[DEBUG] Datos de juego recibidos")
            
            # Cambiar a pantalla de juego
            app.cambiar_pantalla('game', 'up')
            
        except Exception as e:
            print(f"[ERROR] Error al procesar datos de juego: {e}")
    
    def handle_game_start(self, data: Dict[str, Any]):
        """Maneja el inicio del juego"""
        try:
            app = MDApp.get_running_app()
            if not hasattr(app, 'cambiar_pantalla'):
                print("ERROR: La aplicación no es una instancia de BingoApp")
                return
            
            # Configurar juego
            app.cartones_jugador = [data['carton']]
            app.preguntas_disponibles = data['questions']
            app.preguntas_ya_usadas = []
            app.game_in_progress = True
            
            # Cambiar a pantalla de juego
            app.cambiar_pantalla('game', 'up')
            
        except Exception as e:
            print(f"[ERROR] Error al procesar inicio de juego: {e}")
    
    def handle_question(self, data: Dict[str, Any]):
        """Maneja una pregunta recibida"""
        try:
            app = MDApp.get_running_app()
            if not hasattr(app, 'cambiar_pantalla'):
                print("ERROR: La aplicación no es una instancia de BingoApp")
                return
            
            # Mostrar pregunta en la pantalla de juego
            if app.sm and app.sm.current == 'game':
                game_screen = app.sm.get_screen('game')
                if hasattr(game_screen, 'mostrar_pregunta_en_ui'):
                    game_screen.mostrar_pregunta_en_ui(data['question'])
            
        except Exception as e:
            print(f"[ERROR] Error al procesar pregunta: {e}")
    
    def handle_bingo(self, data: Dict[str, Any]):
        """Maneja un bingo anunciado"""
        try:
            winner_name = data.get('winner', 'Jugador')
            self.show_message(f"¡{winner_name} ha cantado BINGO!")
            
        except Exception as e:
            print(f"[ERROR] Error al procesar bingo: {e}")
    
    def handle_player_answer(self, data: Dict[str, Any], addr: Optional[tuple]):
        """Maneja la respuesta de un jugador"""
        try:
            player_name = data.get('player', f'Jugador {addr[0] if addr else "Desconocido"}')
            is_correct = data.get('correct', False)
            
            message = f"{player_name}: {'Correcto' if is_correct else 'Incorrecto'}"
            print(f"[DEBUG] {message}")
            
        except Exception as e:
            print(f"[ERROR] Error al procesar respuesta: {e}")
    
    def handle_player_connected(self, addr: tuple):
        """Maneja la conexión de un nuevo jugador"""
        try:
            print(f"[DEBUG] Jugador conectado desde {addr}")
            
            # Actualizar contador de jugadores
            count = self.connection_manager.get_player_count()
            self.player_count = f"{count}/10"
            
            # Actualizar lista de jugadores
            self.update_players_list()
            
            # Actualizar información de la sala
            if self.is_host:
                self.room_info = f"Jugadores conectados: {count}"
            
        except Exception as e:
            print(f"[ERROR] Error al manejar conexión de jugador: {e}")
    
    def handle_player_disconnected(self, addr: tuple):
        """Maneja la desconexión de un jugador"""
        try:
            print(f"[DEBUG] Jugador desconectado desde {addr}")
            
            # Actualizar contador de jugadores
            count = self.connection_manager.get_player_count()
            self.player_count = f"{count}/10"
            
            # Actualizar lista de jugadores
            self.update_players_list()
            
            # Actualizar información de la sala
            if self.is_host:
                self.room_info = f"Jugadores conectados: {count}"
            
        except Exception as e:
            print(f"[ERROR] Error al manejar desconexión de jugador: {e}")
    
    def handle_connection_lost(self):
        """Maneja la pérdida de conexión"""
        try:
            print("[DEBUG] Conexión perdida")
            
            # Actualizar estado
            self.connection_status = "Conexión perdida"
            self.room_info = "Reconectando..."
            self.is_host = False
            
            # Mostrar mensaje
            self.show_error("Se perdió la conexión con el servidor")
            
        except Exception as e:
            print(f"[ERROR] Error al manejar pérdida de conexión: {e}")
    
    def update_players_list(self):
        """Actualiza la lista de jugadores en la UI"""
        try:
            if not hasattr(self.ids, 'players_list'):
                return
            
            # Limpiar lista actual
            self.ids.players_list.clear_widgets()
            
            # Agregar host
            host_label = MDLabel(
                text="Host (Tú)" if self.is_host else "Host",
                theme_text_color="Custom",
                text_color=(1, 1, 1, 1),
                size_hint_y=None,
                height=dp(30)
            )
            self.ids.players_list.add_widget(host_label)
            
            # Agregar clientes
            for i, (client, addr) in enumerate(self.connection_manager.connected_players, 1):
                player_label = MDLabel(
                    text=f"Jugador {i+1}: {addr[0]}",
                    theme_text_color="Custom",
                    text_color=(1, 1, 1, 1),
                    size_hint_y=None,
                    height=dp(30)
                )
                self.ids.players_list.add_widget(player_label)
                
        except Exception as e:
            print(f"[ERROR] Error al actualizar lista de jugadores: {e}")
    
    def iniciar_juego(self):
        """Inicia el juego multijugador"""
        if not self.is_host or self.game_started:
            return
        
        try:
            print("[DEBUG] Iniciando juego multijugador...")
            
            app = MDApp.get_running_app()
            if not isinstance(app, BingoApp):
                return
            
            # Generar cartones y preguntas
            game_data = self.generate_multiplayer_game()
            if not game_data:
                self.show_error("No se pudieron generar los datos del juego")
                return
            
            # Enviar datos a todos los clientes
            for i, (client, addr) in enumerate(self.connection_manager.connected_players, 1):
                try:
                    data = {
                        'type': 'game_start',
                        'carton': game_data['cartones'][i],
                        'questions': game_data['preguntas_globales']
                    }
                    if not MultiplayerUtils.send_data(client, data):
                        print(f"[WARNING] No se pudo enviar datos a {addr}")
                except Exception as e:
                    print(f"[ERROR] Error al enviar datos a {addr}: {e}")
            
            # Configurar juego para el host
            app.cartones_jugador = [game_data['cartones'][0]]
            app.preguntas_disponibles = game_data['preguntas_globales'].copy()
            app.preguntas_ya_usadas = []
            app.game_in_progress = True
            
            # Marcar juego como iniciado
            self.game_started = True
            
            # Cambiar a pantalla de juego
            app.cambiar_pantalla('game', 'up')
            
            print("[DEBUG] Juego multijugador iniciado")
            
        except Exception as e:
            print(f"[ERROR] Error al iniciar juego: {e}")
            self.show_error(f"Error al iniciar juego: {str(e)}")
    
    def generate_multiplayer_game(self) -> Optional[Dict[str, Any]]:
        """Genera los datos del juego para multijugador"""
        try:
            # Cargar todas las preguntas
            all_questions = []
            base_dir = 'cartones'
            
            if not os.path.exists(base_dir):
                self.show_error("No se encontró el directorio de cartones")
                return None
            
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
                self.show_error("No se encontraron preguntas válidas")
                return None
            
            # Generar cartones únicos
            num_jugadores = self.connection_manager.get_player_count()
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
            
            # Generar lista global de preguntas
            preguntas_globales = []
            for carton in cartones:
                preguntas_globales.extend(carton['preguntas'])
            
            preguntas_globales = list({p['id']: p for p in preguntas_globales}.values())
            random.shuffle(preguntas_globales)
            
            return {
                'cartones': cartones,
                'preguntas_globales': preguntas_globales
            }
            
        except Exception as e:
            print(f"[ERROR] Error al generar juego: {e}")
            return None
    
    def show_error(self, message: str):
        """Muestra un mensaje de error"""
        MultiplayerUtils.show_error_dialog(message)
    
    def show_message(self, message: str):
        """Muestra un mensaje informativo"""
        dialog = MDDialog(
            title="Información",
            text=message,
            buttons=[
                MDRaisedButton(
                    text="OK",
                    on_release=lambda x: dialog.dismiss()
                )
            ]
        )
        dialog.open()
    
    def volver(self):
        """Vuelve a la pantalla principal"""
        # Desconectar todas las conexiones
        self.connection_manager.disconnect()
        
        # Resetear estado
        self.is_host = False
        self.game_started = False
        self.connection_status = "Desconectado"
        self.room_info = ""
        self.local_ip = ""
        self.player_count = "0/10"
        
        # Ocultar botón de iniciar juego
        if hasattr(self.ids, 'start_game_button'):
            self.ids.start_game_button.opacity = 0
            self.ids.start_game_button.disabled = True
        
        # Cambiar a pantalla principal
        app = MDApp.get_running_app()
        if BingoApp and isinstance(app, BingoApp) and hasattr(app, 'cambiar_pantalla'):
            app.cambiar_pantalla('main', 'right')
        else:
            # Fallback: cambiar directamente usando el manager
            if hasattr(self, 'manager') and self.manager:
                self.manager.current = 'main'
    
    def crear_sala_bluetooth(self):
        """Crea una nueva sala de juego por Bluetooth"""
        try:
            print("[DEBUG] Intentando crear sala Bluetooth...")
            
            # Por ahora, usar el mismo método que WiFi
            # En una implementación completa, aquí se configuraría Bluetooth
            self.show_message("Funcionalidad Bluetooth en desarrollo. Usando WiFi como alternativa.")
            self.crear_sala()
            
        except Exception as e:
            print(f"[ERROR] Error al crear sala Bluetooth: {e}")
            self.show_error(f"Error al crear sala Bluetooth: {str(e)}")
    
    def unirse_sala_bluetooth(self):
        """Muestra diálogo para unirse a una sala por Bluetooth"""
        try:
            print("[DEBUG] Intentando unirse a sala Bluetooth...")
            
            # Por ahora, usar el mismo método que WiFi
            # En una implementación completa, aquí se configuraría Bluetooth
            self.show_message("Funcionalidad Bluetooth en desarrollo. Usando WiFi como alternativa.")
            self.unirse_sala()
            
        except Exception as e:
            print(f"[ERROR] Error al unirse a sala Bluetooth: {e}")
            self.show_error(f"Error al unirse a sala Bluetooth: {str(e)}")
    
    def on_leave(self):
        """Se llama cuando se sale de la pantalla"""
        # Desconectar al salir
        self.connection_manager.disconnect() 