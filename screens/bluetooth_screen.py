"""
Pantalla de Multijugador Bluetooth
Implementa la interfaz para jugar usando Bluetooth
"""

from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.scrollview import ScrollView
from kivy.uix.gridlayout import GridLayout
from kivy.uix.popup import Popup
from kivy.uix.progressbar import ProgressBar
from kivy.properties import StringProperty, BooleanProperty, ListProperty
from kivy.clock import Clock
from kivy.metrics import dp
from kivy.core.window import Window

from kivymd.uix.screen import MDScreen
from kivymd.uix.button import MDRaisedButton, MDFlatButton, MDIconButton
from kivymd.uix.card import MDCard
from kivymd.uix.label import MDLabel
from kivymd.uix.textfield import MDTextField
from kivymd.uix.list import MDList, OneLineListItem, TwoLineListItem
from kivymd.uix.dialog import MDDialog
from kivymd.uix.snackbar import Snackbar
from kivymd.uix.progressbar import MDProgressBar
from kivymd.uix.toolbar import MDTopAppBar
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.gridlayout import MDGridLayout
from kivymd.uix.scrollview import MDScrollView

import threading
import time
import json
from typing import List, Dict, Optional
from kivymd.app import MDApp

from services.bluetooth_service import AndroidBluetoothService, BLUETOOTH_UUID
from utils.constants import Colors


class BluetoothScreen(MDScreen):
    """
    Pantalla para multijugador Bluetooth
    """
    
    # Propiedades reactivas
    status_text = StringProperty("Desconectado")
    player_count = StringProperty("0 jugadores")
    is_connected = BooleanProperty(False)
    is_host = BooleanProperty(False)
    is_discovering = BooleanProperty(False)
    devices_list = ListProperty([])
    players_list = ListProperty([])
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.name = "bluetooth_screen"
        
        # Servicio Bluetooth
        self.bluetooth_service = AndroidBluetoothService()
        self.current_dialog = None
        self.discovery_thread = None
        self.player_name = ""
        
        # Configurar UI
        self._setup_ui()
        self._setup_bluetooth_handlers()
        
        # Timer para actualizar UI
        Clock.schedule_interval(self._update_ui, 1.0)
    
    def _setup_ui(self):
        """Configura la interfaz de usuario"""
        # Layout principal
        main_layout = MDBoxLayout(
            orientation='vertical',
            spacing=dp(16),
            padding=dp(16)
        )
        
        # Barra superior
        toolbar = MDTopAppBar(
            title="Multijugador Bluetooth",
            left_action_items=[["arrow-left", lambda x: self._go_back()]],
            right_action_items=[["bluetooth", lambda x: self._toggle_bluetooth()]],
            elevation=4
        )
        main_layout.add_widget(toolbar)
        
        # Contenido principal
        content_layout = MDBoxLayout(
            orientation='vertical',
            spacing=dp(16)
        )
        
        # Estado de conexión
        status_card = MDCard(
            size_hint_y=None,
            height=dp(80),
            padding=dp(16)
        )
        
        status_layout = MDBoxLayout(
            orientation='vertical',
            spacing=dp(8)
        )
        
        self.status_label = MDLabel(
            text="Estado: Desconectado",
            theme_text_color="Primary",
            font_style="H6"
        )
        
        self.player_count_label = MDLabel(
            text="Jugadores: 0",
            theme_text_color="Secondary"
        )
        
        status_layout.add_widget(self.status_label)
        status_layout.add_widget(self.player_count_label)
        status_card.add_widget(status_layout)
        content_layout.add_widget(status_card)
        
        # Botones de acción
        action_layout = MDBoxLayout(
            orientation='horizontal',
            spacing=dp(16),
            size_hint_y=None,
            height=dp(56)
        )
        
        self.create_room_btn = MDRaisedButton(
            text="Crear Sala",
            on_release=self._show_create_room_dialog,
            size_hint_x=0.5
        )
        
        self.join_room_btn = MDRaisedButton(
            text="Unirse a Sala",
            on_release=self._show_join_room_dialog,
            size_hint_x=0.5
        )
        
        action_layout.add_widget(self.create_room_btn)
        action_layout.add_widget(self.join_room_btn)
        content_layout.add_widget(action_layout)
        
        # Lista de dispositivos
        devices_card = MDCard(
            size_hint_y=None,
            height=dp(200)
        )
        
        devices_header = MDBoxLayout(
            orientation='horizontal',
            spacing=dp(16),
            padding=dp(16)
        )
        
        devices_header.add_widget(MDLabel(
            text="Dispositivos Disponibles",
            theme_text_color="Primary",
            font_style="H6"
        ))
        
        self.discover_btn = MDIconButton(
            icon="magnify",
            on_release=self._start_discovery
        )
        devices_header.add_widget(self.discover_btn)
        
        self.refresh_btn = MDIconButton(
            icon="refresh",
            on_release=self._refresh_devices
        )
        devices_header.add_widget(self.refresh_btn)
        
        devices_card.add_widget(devices_header)
        
        self.devices_list_view = MDList()
        devices_scroll = MDScrollView()
        devices_scroll.add_widget(self.devices_list_view)
        devices_card.add_widget(devices_scroll)
        
        content_layout.add_widget(devices_card)
        
        # Lista de jugadores
        players_card = MDCard(
            size_hint_y=None,
            height=dp(200)
        )
        
        players_header = MDBoxLayout(
            orientation='horizontal',
            spacing=dp(16),
            padding=dp(16)
        )
        
        players_header.add_widget(MDLabel(
            text="Jugadores Conectados",
            theme_text_color="Primary",
            font_style="H6"
        ))
        
        self.players_list_view = MDList()
        players_scroll = MDScrollView()
        players_scroll.add_widget(self.players_list_view)
        players_card.add_widget(players_scroll)
        
        content_layout.add_widget(players_card)
        
        # Agregar contenido al layout principal
        main_layout.add_widget(content_layout)
        self.add_widget(main_layout)
    
    def _setup_bluetooth_handlers(self):
        """Configura los manejadores de eventos Bluetooth"""
        # Configurar callbacks del servicio Bluetooth
        self.bluetooth_service.on_data_received = self._on_data_received
        self.bluetooth_service.on_client_connected = self._on_client_connected
        self.bluetooth_service.on_connected = self._on_connected
    
    def _on_data_received(self, data):
        """Maneja datos recibidos por Bluetooth"""
        try:
            if isinstance(data, bytes):
                # Intentar decodificar como JSON
                json_str = data.decode('utf-8')
                message = json.loads(json_str)
                self._process_message(message)
            else:
                print(f"[BLUETOOTH] Datos recibidos: {data}")
        except Exception as e:
            print(f"[BLUETOOTH] Error procesando datos: {e}")
    
    def _process_message(self, message):
        """Procesa mensajes recibidos"""
        try:
            msg_type = message.get('type')
            
            if msg_type == 'login':
                player_name = message.get('player_name', 'Jugador')
                self._add_player(player_name)
                
            elif msg_type == 'game_start':
                self._start_game(message)
                
            elif msg_type == 'question':
                self._show_question(message)
                
            elif msg_type == 'answer':
                self._show_answer(message)
                
            elif msg_type == 'bingo':
                winner = message.get('winner', 'Jugador')
                self._show_bingo(winner)
                
        except Exception as e:
            print(f"[BLUETOOTH] Error procesando mensaje: {e}")
    
    def _add_player(self, player_name):
        """Agrega un jugador a la lista"""
        if player_name not in self.players_list:
            self.players_list.append(player_name)
            self._update_players_list()
            self._show_snackbar(f"{player_name} se unió al juego")
    
    def _start_game(self, game_data):
        """Inicia el juego"""
        try:
            app = MDApp.get_running_app()
            if hasattr(app, 'cambiar_pantalla'):
                app.cambiar_pantalla('game', 'up')
            self._show_snackbar("¡El juego ha comenzado!")
        except Exception as e:
            print(f"[BLUETOOTH] Error iniciando juego: {e}")
    
    def _show_question(self, question_data):
        """Muestra una pregunta"""
        question = question_data.get('question', '')
        self._show_snackbar(f"Pregunta: {question}")
    
    def _show_answer(self, answer_data):
        """Muestra una respuesta"""
        player = answer_data.get('player', 'Jugador')
        is_correct = answer_data.get('correct', False)
        result = "Correcto" if is_correct else "Incorrecto"
        self._show_snackbar(f"{player}: {result}")
    
    def _show_bingo(self, winner):
        """Muestra el ganador del bingo"""
        self._show_snackbar(f"¡{winner} ha ganado el Bingo!")
    
    def _on_client_connected(self, client_socket):
        """Maneja la conexión de un cliente"""
        self._show_snackbar("Cliente conectado")
        self.is_connected = True
        self._update_status()
    
    def _on_connected(self, socket):
        """Maneja la conexión al servidor"""
        self._show_snackbar("Conectado al servidor")
        self.is_connected = True
        self._update_status()
    
    def _show_create_room_dialog(self, instance):
        """Muestra diálogo para crear sala"""
        content = MDBoxLayout(
            orientation='vertical',
            spacing=dp(16),
            size_hint_y=None,
            height=dp(120)
        )
        
        name_input = MDTextField(
            hint_text="Tu nombre",
            helper_text="Ingresa tu nombre para la sala",
            helper_text_mode="on_focus"
        )
        
        content.add_widget(name_input)
        
        def create_room(dialog):
            player_name = name_input.text.strip()
            if player_name:
                self._create_room(player_name)
            if dialog:
                dialog.dismiss()
        
        dialog = MDDialog(
            title="Crear Sala Bluetooth",
            type="custom",
            content_cls=content,
            buttons=[
                MDRaisedButton(
                    text="Crear",
                    on_release=lambda x: create_room(dialog)
                ),
                MDFlatButton(
                    text="Cancelar",
                    on_release=lambda x: dialog.dismiss()
                )
            ]
        )
        dialog.open()
    
    def _create_room(self, player_name):
        """Crea una sala Bluetooth"""
        try:
            self.player_name = player_name
            
            # Habilitar Bluetooth si es necesario
            if not self.bluetooth_service.is_bluetooth_enabled():
                if not self.bluetooth_service.enable_bluetooth():
                    self._show_snackbar("Error: No se pudo habilitar Bluetooth")
                    return
            
            # Iniciar servidor
            success = self.bluetooth_service.start_server(BLUETOOTH_UUID, self._on_client_connected)
            if success:
                self.is_host = True
                self._update_status()
                self._show_snackbar("Sala creada. Esperando jugadores...")
            else:
                self._show_snackbar("Error: No se pudo crear la sala")
                
        except Exception as e:
            print(f"[BLUETOOTH] Error creando sala: {e}")
            self._show_snackbar(f"Error: {str(e)}")
    
    def _show_join_room_dialog(self, instance):
        """Muestra diálogo para unirse a sala"""
        content = MDBoxLayout(
            orientation='vertical',
            spacing=dp(16),
            size_hint_y=None,
            height=dp(120)
        )
        
        name_input = MDTextField(
            hint_text="Tu nombre",
            helper_text="Ingresa tu nombre para unirte",
            helper_text_mode="on_focus"
        )
        
        content.add_widget(name_input)
        
        def join_room(dialog):
            player_name = name_input.text.strip()
            if player_name:
                self._join_room(player_name)
            if dialog:
                dialog.dismiss()
        
        dialog = MDDialog(
            title="Unirse a Sala Bluetooth",
            type="custom",
            content_cls=content,
            buttons=[
                MDRaisedButton(
                    text="Buscar y Conectar",
                    on_release=lambda x: join_room(dialog)
                ),
                MDFlatButton(
                    text="Cancelar",
                    on_release=lambda x: dialog.dismiss()
                )
            ]
        )
        dialog.open()
    
    def _join_room(self, player_name):
        """Se une a una sala Bluetooth"""
        try:
            self.player_name = player_name
            
            # Habilitar Bluetooth si es necesario
            if not self.bluetooth_service.is_bluetooth_enabled():
                if not self.bluetooth_service.enable_bluetooth():
                    self._show_snackbar("Error: No se pudo habilitar Bluetooth")
                    return
            
            # Buscar dispositivos emparejados
            devices = self.bluetooth_service.get_paired_devices()
            if not devices:
                self._show_snackbar("No hay dispositivos emparejados")
                return
            
            # Mostrar diálogo para seleccionar dispositivo
            self._show_device_selection_dialog(devices)
            
        except Exception as e:
            print(f"[BLUETOOTH] Error uniéndose a sala: {e}")
            self._show_snackbar(f"Error: {str(e)}")
    
    def _show_device_selection_dialog(self, devices):
        """Muestra diálogo para seleccionar dispositivo"""
        content = MDBoxLayout(
            orientation='vertical',
            spacing=dp(8),
            size_hint_y=None,
            height=dp(200)
        )
        
        devices_list = MDList()
        for name, address in devices:
            item = TwoLineListItem(
                text=name,
                secondary_text=address
            )
            item.bind(on_release=lambda x, addr=address: self._connect_to_device(addr))
            devices_list.add_widget(item)
        
        scroll = MDScrollView()
        scroll.add_widget(devices_list)
        content.add_widget(scroll)
        
        dialog = MDDialog(
            title="Seleccionar Dispositivo",
            type="custom",
            content_cls=content,
            buttons=[
                MDFlatButton(
                    text="Cancelar",
                    on_release=lambda x: dialog.dismiss()
                )
            ]
        )
        dialog.open()
    
    def _connect_to_device(self, device_address):
        """Conecta a un dispositivo específico"""
        try:
            success = self.bluetooth_service.connect_to_server(device_address, BLUETOOTH_UUID, self._on_connected)
            if success:
                self._show_snackbar("Conectando...")
                self._update_status()
                
                # Enviar mensaje de login
                login_message = {
                    'type': 'login',
                    'player_name': self.player_name
                }
                self.bluetooth_service.send_json(login_message)
            else:
                self._show_snackbar("Error: No se pudo conectar")
                
        except Exception as e:
            print(f"[BLUETOOTH] Error conectando: {e}")
            self._show_snackbar(f"Error: {str(e)}")
    
    def _start_discovery(self, instance):
        """Inicia la búsqueda de dispositivos"""
        if not self.bluetooth_service:
            self._show_snackbar("Bluetooth no disponible")
            return
        
        self.is_discovering = True
        self.discover_btn.disabled = True
        self.discover_btn.icon = "loading"
        
        def found(name, addr):
            device = {'name': name, 'address': addr}
            if device not in self.devices_list:
                self.devices_list.append(device)
                self._update_devices_list()
        
        success = self.bluetooth_service.discover_devices(found)
        if not success:
            self._show_snackbar("Error iniciando búsqueda")
            self._finish_discovery()
    
    def _finish_discovery(self):
        """Finaliza la búsqueda de dispositivos"""
        self.is_discovering = False
        self.discover_btn.disabled = False
        self.discover_btn.icon = "magnify"
    
    def _update_devices_list(self):
        """Actualiza la lista de dispositivos"""
        self.devices_list_view.clear_widgets()
        
        for device in self.devices_list:
            item = TwoLineListItem(
                text=device['name'],
                secondary_text=device['address']
            )
            item.bind(on_release=lambda x, dev=device: self._connect_to_device(dev['address']))
            self.devices_list_view.add_widget(item)
    
    def _update_players_list(self):
        """Actualiza la lista de jugadores"""
        self.players_list_view.clear_widgets()
        
        for player in self.players_list:
            item = OneLineListItem(
                text=player
            )
            self.players_list_view.add_widget(item)
        
        self.player_count = f"{len(self.players_list)} jugadores"
        self.player_count_label.text = f"Jugadores: {len(self.players_list)}"
    
    def _update_status(self):
        """Actualiza el estado de la conexión"""
        if self.is_connected:
            if self.is_host:
                self.status_text = "Host - Conectado"
                self.status_label.text = "Estado: Host - Conectado"
            else:
                self.status_text = "Cliente - Conectado"
                self.status_label.text = "Estado: Cliente - Conectado"
        else:
            self.status_text = "Desconectado"
            self.status_label.text = "Estado: Desconectado"
    
    def _update_ui(self, dt):
        """Actualiza la UI periódicamente"""
        self._update_status()
        self._update_players_list()
    
    def _refresh_devices(self, instance):
        """Actualiza la lista de dispositivos"""
        if not self.is_discovering:
            self._start_discovery(instance)
    
    def _toggle_bluetooth(self, instance=None):
        """Alterna el estado del Bluetooth"""
        if not self.bluetooth_service:
            self._show_snackbar("Bluetooth no disponible")
            return
        
        if self.bluetooth_service.is_bluetooth_enabled():
            self._show_snackbar("Bluetooth habilitado")
        else:
            self._show_snackbar("Bluetooth deshabilitado")
    
    def _go_back(self):
        """Regresa a la pantalla anterior"""
        # Limpiar recursos
        if self.bluetooth_service:
            self.bluetooth_service.cleanup()
        
        # Cambiar pantalla
        app = MDApp.get_running_app()
        if hasattr(app, 'cambiar_pantalla'):
            app.cambiar_pantalla('main', 'right')
        elif hasattr(self, 'manager') and self.manager:
            self.manager.current = 'main'
    
    def _show_snackbar(self, message):
        """Muestra un mensaje en snackbar"""
        Snackbar(
            text=message,
            duration=3.0
        ).open()
    
    def on_leave(self):
        """Se llama cuando se sale de la pantalla"""
        # Limpiar recursos
        if self.bluetooth_service:
            self.bluetooth_service.cleanup()
        
        # Cancelar timer
        Clock.unschedule(self._update_ui) 