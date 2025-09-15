"""
Pantalla de Multijugador para Bingo Educativo
Implementa funcionalidad completa de multijugador
"""

from typing import Optional, Dict, Any
from kivy.clock import Clock
from kivy.properties import BooleanProperty, StringProperty
from kivymd.uix.screen import MDScreen
from kivymd.uix.button import MDRaisedButton
from kivymd.uix.label import MDLabel
from kivymd.uix.textfield import MDTextField
from kivymd.uix.dialog import MDDialog
from kivymd.uix.card import MDCard
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.gridlayout import MDGridLayout

from screens.base_screen import BaseScreen
from services.network_service import network_service, MessageType, Player
from utils.constants import Colors, TextConfig, UIConfig


class MultiplayerScreen(BaseScreen):
    """
    Pantalla de multijugador moderna y funcional
    """
    
    # Propiedades reactivas
    is_host = BooleanProperty(False)
    is_connected = BooleanProperty(False)
    room_code = StringProperty('')
    local_ip = StringProperty('')
    player_count = StringProperty('0/10')
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.name = 'multiplayer'
        self.player_name = ''
        self.dialog: Optional[MDDialog] = None
        self.connection_dialog: Optional[MDDialog] = None
        
        # Configurar listeners del estado
        self._setup_state_listeners()
        
        # Registrar callbacks de red
        network_service.register_connection_callback(self._on_network_connected)
        network_service.register_disconnection_callback(self._on_network_disconnected)
        
        # Registrar manejadores de mensajes
        network_service.register_message_handler(MessageType.JOIN_GAME, self._handle_player_join)
        network_service.register_message_handler(MessageType.LEAVE_GAME, self._handle_player_leave)
        network_service.register_message_handler(MessageType.START_GAME, self._handle_game_start)
        network_service.register_message_handler(MessageType.GAME_STATE, self._handle_game_state)
        network_service.register_message_handler(MessageType.QUESTION, self._handle_question)
        network_service.register_message_handler(MessageType.BINGO, self._handle_bingo)
    
    def _setup_state_listeners(self) -> None:
        """Configura los listeners del estado"""
        self.state_listeners = {
            'players': self._on_players_changed,
            'status': self._on_game_status_changed
        }
    
    def on_enter(self) -> None:
        """Se llama cuando la pantalla se activa"""
        super().on_enter()
        
        # Mostrar diálogo para obtener nombre del jugador
        self._show_player_name_dialog()
        
        # Actualizar UI
        self._update_ui()
    
    def on_leave(self) -> None:
        """Se llama cuando la pantalla se desactiva"""
        super().on_leave()
        
        # Limpiar recursos de red
        network_service.cleanup()
    
    def _show_player_name_dialog(self) -> None:
        """Muestra diálogo para obtener nombre del jugador"""
        text_field = MDTextField(
            hint_text="Tu nombre",
            helper_text="Ingresa tu nombre para el multijugador",
            helper_text_mode="on_error",
            size_hint_x=0.8,
            pos_hint={"center_x": .5}
        )
        
        self.dialog = MDDialog(
            title="Configurar Multijugador",
            type="custom",
            content_cls=text_field,
            buttons=[
                MDRaisedButton(
                    text="Continuar",
                    on_release=lambda x: self._set_player_name(text_field.text)
                ),
                MDRaisedButton(
                    text="Cancelar",
                    on_release=lambda x: self._cancel_multiplayer()
                )
            ]
        )
        self.dialog.open()
    
    def _set_player_name(self, name: str) -> None:
        """Establece el nombre del jugador"""
        if not name or len(name.strip()) < 2:
            self.show_error_dialog("El nombre debe tener al menos 2 caracteres")
            return
        
        self.player_name = name.strip()
        if self.dialog:
            self.dialog.dismiss()
        
        # Actualizar UI
        self._update_ui()
    
    def _cancel_multiplayer(self) -> None:
        """Cancela la configuración de multijugador"""
        if self.dialog:
            self.dialog.dismiss()
        self.navigate_to_screen('main', 'right')
    
    def seleccionar_modo(self, modo: str) -> None:
        """Selecciona el modo de conexión (WiFi/Bluetooth)"""
        print(f"[DEBUG] Modo seleccionado: {modo}")
        
        # Por ahora solo implementamos WiFi
        if modo == 'bluetooth':
            self.show_error_dialog("Funcionalidad Bluetooth en desarrollo")
            return
        
        # Actualizar UI según el modo
        self._update_mode_ui(modo)
    
    def _update_mode_ui(self, modo: str) -> None:
        """Actualiza la UI según el modo seleccionado"""
        # Mostrar/ocultar opciones según el modo
        wifi_options = self.ids.get('wifi_options', None)
        bluetooth_options = self.ids.get('bluetooth_options', None)
        
        if wifi_options:
            wifi_options.opacity = 1 if modo == 'wifi' else 0
            wifi_options.disabled = modo != 'wifi'
        
        if bluetooth_options:
            bluetooth_options.opacity = 1 if modo == 'bluetooth' else 0
            bluetooth_options.disabled = modo != 'bluetooth'
    
    def crear_sala(self) -> None:
        """Crea una nueva sala de juego"""
        if not self.player_name:
            self.show_error_dialog("Debes configurar tu nombre primero")
            return
        
        # Mostrar diálogo de carga
        self.show_loading_dialog("Creando sala...")
        
        # Iniciar servidor
        success = network_service.start_server(self.player_name)
        
        if success:
            self.hide_loading_dialog()
            self.is_host = True
            self.room_code = network_service.room_code
            self.local_ip = network_service.local_ip
            
            # Actualizar UI
            self._update_connection_status()
            self._update_player_list()
            
            print(f"[MULTIPLAYER] Sala creada: {self.room_code}")
        else:
            self.hide_loading_dialog()
            self.show_error_dialog("Error al crear la sala. Verifica tu conexión de red.")
    
    def unirse_sala(self) -> None:
        """Muestra diálogo para unirse a una sala"""
        text_field = MDTextField(
            hint_text="IP del host",
            helper_text="Ejemplo: 192.168.1.10",
            helper_text_mode="on_error",
            size_hint_x=0.8,
            pos_hint={"center_x": .5}
        )
        
        self.connection_dialog = MDDialog(
            title="Unirse a Sala",
            type="custom",
            content_cls=text_field,
            buttons=[
                MDRaisedButton(
                    text="Conectar",
                    on_release=lambda x: self._connect_to_host(text_field.text)
                ),
                MDRaisedButton(
                    text="Cancelar",
                    on_release=lambda x: self._dismiss_connection_dialog()
                )
            ]
        )
        self.connection_dialog.open()
    
    def _connect_to_host(self, host_ip: str) -> None:
        """Conecta a un host específico"""
        if not host_ip or len(host_ip.strip()) < 7:
            self.show_error_dialog("Ingresa una IP válida")
            return
        
        host_ip = host_ip.strip()
        
        # Mostrar diálogo de carga
        self.show_loading_dialog(f"Conectando a {host_ip}...")
        
        # Intentar conexión
        success = network_service.connect_to_server(host_ip, self.player_name)
        
        if success:
            self.hide_loading_dialog()
            self.is_host = False
            self.is_connected = True
            
            # Actualizar UI
            self._update_connection_status()
            
            print(f"[MULTIPLAYER] Conectado a host: {host_ip}")
        else:
            self.hide_loading_dialog()
            self.show_error_dialog(f"Error al conectar a {host_ip}. Verifica la IP y la conexión.")
        
        self._dismiss_connection_dialog()
    
    def _dismiss_connection_dialog(self) -> None:
        """Cierra el diálogo de conexión"""
        if self.connection_dialog:
            self.connection_dialog.dismiss()
            self.connection_dialog = None
    
    def iniciar_juego(self) -> None:
        """Inicia el juego multijugador"""
        if not self.is_host:
            self.show_error_dialog("Solo el host puede iniciar el juego")
            return
        
        if network_service.get_player_count() < 2:
            self.show_error_dialog("Se necesitan al menos 2 jugadores para iniciar")
            return
        
        # Enviar mensaje de inicio a todos los jugadores
        start_message = {
            'game_config': {
                'max_rounds': 25,
                'question_time': 30,
                'categories': ['animales', 'deportes', 'geografia']
            }
        }
        
        # Aquí enviarías el mensaje a través del servicio de red
        # network_service.send_message(MessageType.START_GAME, start_message)
        
        # Por ahora, simular inicio
        self.show_dialog(
            "Iniciando Juego",
            f"Juego iniciado con {network_service.get_player_count()} jugadores",
            [
                MDRaisedButton(
                    text="Continuar",
                    on_release=lambda x: self._start_multiplayer_game()
                )
            ]
        )
    
    def _start_multiplayer_game(self) -> None:
        """Inicia el juego multijugador"""
        # Configurar estado del juego
        self.state_manager.set_game_status(self.state_manager.get_state('status'))
        
        # Navegar a la pantalla de juego
        self.navigate_to_screen('game', 'up')
    
    def volver(self) -> None:
        """Regresa a la pantalla principal"""
        # Limpiar recursos
        network_service.cleanup()
        
        # Navegar de vuelta
        self.navigate_to_screen('main', 'right')
    
    def _update_ui(self) -> None:
        """Actualiza la interfaz de usuario"""
        self._update_connection_status()
        self._update_player_list()
        self._update_buttons()
    
    def _update_connection_status(self) -> None:
        """Actualiza el estado de conexión en la UI"""
        if hasattr(self.ids, 'connection_status'):
            if self.is_host:
                status_text = f"Host - Código: {self.room_code}"
            elif self.is_connected:
                status_text = "Conectado como jugador"
            else:
                status_text = "Desconectado"
            
            self.ids.connection_status.text = f"Estado: {status_text}"
    
    def _update_player_list(self) -> None:
        """Actualiza la lista de jugadores"""
        if hasattr(self.ids, 'players_list'):
            self.ids.players_list.clear_widgets()
            
            players = network_service.get_players()
            for player in players:
                player_card = self._create_player_card(player)
                self.ids.players_list.add_widget(player_card)
            
            # Actualizar contador
            self.player_count = f"{len(players)}/{network_service.max_players}"
            if hasattr(self.ids, 'players_count_label'):
                self.ids.players_count_label.text = f"Jugadores: {self.player_count}"
    
    def _create_player_card(self, player: Player) -> MDCard:
        """Crea una tarjeta para mostrar un jugador"""
        card = MDCard(
            orientation='horizontal',
            padding='8dp',
            spacing='8dp',
            size_hint_y=None,
            height='40dp'
        )
        
        # Icono de host si es host
        if player.is_host:
            host_label = MDLabel(
                text="👑",
                size_hint_x=None,
                width='30dp'
            )
            card.add_widget(host_label)
        
        # Nombre del jugador
        name_label = MDLabel(
            text=player.name,
            theme_text_color="Custom",
            text_color=Colors.TEXT_PRIMARY,
            size_hint_x=0.7
        )
        card.add_widget(name_label)
        
        # Puntaje
        score_label = MDLabel(
            text=str(player.score),
            theme_text_color="Custom",
            text_color=Colors.SUCCESS,
            size_hint_x=0.3
        )
        card.add_widget(score_label)
        
        return card
    
    def _update_buttons(self) -> None:
        """Actualiza el estado de los botones"""
        if hasattr(self.ids, 'start_game_button'):
            self.ids.start_game_button.disabled = not self.is_host
            self.ids.start_game_button.opacity = 1 if self.is_host else 0
    
    # Callbacks de red
    def _on_network_connected(self) -> None:
        """Callback cuando se establece conexión"""
        self.is_connected = True
        Clock.schedule_once(lambda dt: self._update_ui(), 0)
        print("[MULTIPLAYER] Conexión establecida")
    
    def _on_network_disconnected(self) -> None:
        """Callback cuando se pierde conexión"""
        self.is_connected = False
        Clock.schedule_once(lambda dt: self._update_ui(), 0)
        print("[MULTIPLAYER] Conexión perdida")
    
    # Manejadores de mensajes
    def _handle_player_join(self, message, client_socket=None) -> None:
        """Maneja cuando un jugador se une"""
        player_data = message.data
        player = Player(
            id=message.sender_id,
            name=player_data.get('player_name', 'Jugador'),
            ip=player_data.get('ip', ''),
            port=player_data.get('port', 0)
        )
        
        network_service.players[player.id] = player
        
        Clock.schedule_once(lambda dt: self._update_player_list(), 0)
        print(f"[MULTIPLAYER] Jugador unido: {player.name}")
    
    def _handle_player_leave(self, message, client_socket=None) -> None:
        """Maneja cuando un jugador se va"""
        if message.sender_id in network_service.players:
            player = network_service.players[message.sender_id]
            del network_service.players[message.sender_id]
            
            Clock.schedule_once(lambda dt: self._update_player_list(), 0)
            print(f"[MULTIPLAYER] Jugador se fue: {player.name}")
    
    def _handle_game_start(self, message, client_socket=None) -> None:
        """Maneja el inicio del juego"""
        game_config = message.data.get('game_config', {})
        
        # Configurar el juego con los datos recibidos
        self.state_manager.set_state('game_config', game_config)
        
        Clock.schedule_once(lambda dt: self._start_multiplayer_game(), 0)
        print("[MULTIPLAYER] Juego iniciado")
    
    def _handle_game_state(self, message, client_socket=None) -> None:
        """Maneja actualizaciones del estado del juego"""
        game_state = message.data
        
        # Actualizar estado local
        for key, value in game_state.items():
            self.state_manager.set_state(key, value)
        
        Clock.schedule_once(lambda dt: self._update_ui(), 0)
        print("[MULTIPLAYER] Estado del juego actualizado")
    
    def _handle_question(self, message, client_socket=None) -> None:
        """Maneja nuevas preguntas"""
        question_data = message.data
        
        # Actualizar pregunta actual
        self.state_manager.set_state('current_question', question_data)
        
        print("[MULTIPLAYER] Nueva pregunta recibida")
    
    def _handle_bingo(self, message, client_socket=None) -> None:
        """Maneja notificaciones de bingo"""
        bingo_data = message.data
        winner_name = bingo_data.get('winner_name', 'Jugador')
        
        self.show_dialog(
            "¡BINGO!",
            f"¡{winner_name} ha ganado el juego!",
            [
                MDRaisedButton(
                    text="Nuevo Juego",
                    on_release=lambda x: self._restart_game()
                ),
                MDRaisedButton(
                    text="Volver",
                    on_release=lambda x: self.volver()
                )
            ]
        )
        
        print(f"[MULTIPLAYER] Bingo anunciado: {winner_name}")
    
    def _restart_game(self) -> None:
        """Reinicia el juego"""
        # Limpiar estado
        self.state_manager.reset_state()
        
        # Volver a la pantalla de multijugador
        self.navigate_to_screen('multiplayer', 'left')
    
    # Callbacks del estado
    def _on_players_changed(self, key: str, value: Any) -> None:
        """Callback cuando cambian los jugadores"""
        Clock.schedule_once(lambda dt: self._update_player_list(), 0)
    
    def _on_game_status_changed(self, key: str, value: Any) -> None:
        """Callback cuando cambia el estado del juego"""
        Clock.schedule_once(lambda dt: self._update_ui(), 0) 