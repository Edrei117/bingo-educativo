"""
Utilidades para el manejo del multijugador
"""
import socket
import threading
import json
import time
import random
from typing import Dict, List, Optional, Callable, Any
from kivy.clock import Clock
from kivy.metrics import dp
from kivymd.uix.dialog import MDDialog
from kivymd.uix.button import MDRaisedButton
from kivymd.uix.textfield import MDTextField

class MultiplayerUtils:
    """Clase con utilidades para el manejo del multijugador"""
    
    # Configuraciones
    DEFAULT_PORT = 5000
    TIMEOUT = 10  # segundos
    MAX_RETRIES = 3
    BUFFER_SIZE = 65536
    
    @staticmethod
    def get_local_ip() -> str:
        """Obtiene la IP local del dispositivo"""
        try:
            # Método 1: Conectar a un servidor externo
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.settimeout(3)
            s.connect(('8.8.8.8', 80))
            ip = s.getsockname()[0]
            s.close()
            return ip
        except Exception:
            try:
                # Método 2: Obtener hostname
                hostname = socket.gethostname()
                ip = socket.gethostbyname(hostname)
                return ip
            except Exception:
                return '127.0.0.1'
    
    @staticmethod
    def generate_room_code() -> str:
        """Genera un código de sala único"""
        return ''.join(random.choices('0123456789', k=6))
    
    @staticmethod
    def validate_ip(ip: str) -> bool:
        """Valida si una IP es válida"""
        try:
            parts = ip.split('.')
            if len(parts) != 4:
                return False
            for part in parts:
                if not 0 <= int(part) <= 255:
                    return False
            return True
        except:
            return False
    
    @staticmethod
    def create_server_socket(port: int = DEFAULT_PORT) -> Optional[socket.socket]:
        """Crea un socket de servidor con manejo de errores"""
        try:
            server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            server_socket.settimeout(1)  # Timeout para aceptar conexiones
            server_socket.bind(('0.0.0.0', port))
            server_socket.listen(10)
            return server_socket
        except Exception as e:
            print(f"[ERROR] No se pudo crear servidor en puerto {port}: {e}")
            return None
    
    @staticmethod
    def create_client_socket(host: str, port: int = DEFAULT_PORT) -> Optional[socket.socket]:
        """Crea un socket de cliente con manejo de errores"""
        try:
            client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            client_socket.settimeout(MultiplayerUtils.TIMEOUT)
            client_socket.connect((host, port))
            client_socket.settimeout(None)  # Sin timeout para recibir datos
            return client_socket
        except Exception as e:
            print(f"[ERROR] No se pudo conectar a {host}:{port}: {e}")
            return None
    
    @staticmethod
    def send_data(socket_obj: socket.socket, data: Dict[str, Any]) -> bool:
        """Envía datos de forma segura"""
        try:
            json_data = json.dumps(data, ensure_ascii=False)
            socket_obj.send(json_data.encode('utf-8'))
            return True
        except Exception as e:
            print(f"[ERROR] Error al enviar datos: {e}")
            return False
    
    @staticmethod
    def receive_data(socket_obj: socket.socket) -> Optional[Dict[str, Any]]:
        """Recibe datos de forma segura"""
        try:
            data = socket_obj.recv(MultiplayerUtils.BUFFER_SIZE)
            if not data:
                return None
            return json.loads(data.decode('utf-8'))
        except Exception as e:
            print(f"[ERROR] Error al recibir datos: {e}")
            return None
    
    @staticmethod
    def show_error_dialog(message: str, callback: Optional[Callable] = None):
        """Muestra un diálogo de error"""
        def dismiss_dialog(dialog_instance):
            dialog_instance.dismiss()
            if callback:
                callback()
        
        dialog = MDDialog(
            title="Error de Conexión",
            text=message,
            buttons=[
                MDRaisedButton(
                    text="OK",
                    on_release=dismiss_dialog
                )
            ]
        )
        dialog.open()
    
    @staticmethod
    def show_input_dialog(title: str, hint_text: str, callback: Callable):
        """Muestra un diálogo de entrada"""
        text_field = MDTextField(
            hint_text=hint_text,
            helper_text="",
            helper_text_mode="on_error"
        )
        
        def on_submit(dialog_instance):
            value = text_field.text.strip()
            dialog_instance.dismiss()
            if value:
                callback(value)
        
        dialog = MDDialog(
            title=title,
            type="custom",
            content_cls=text_field,
            buttons=[
                MDRaisedButton(
                    text="Aceptar",
                    on_release=on_submit
                ),
                MDRaisedButton(
                    text="Cancelar",
                    on_release=lambda x: dialog.dismiss()
                )
            ]
        )
        dialog.open()


class MultiplayerProtocol:
    """Protocolo estandarizado para comunicación multijugador"""
    
    # Tipos de mensajes
    MESSAGE_TYPES = {
        'LOGIN': 'login',
        'LOGOUT': 'logout',
        'GAME_START': 'game_start',
        'GAME_END': 'game_end',
        'QUESTION': 'question',
        'ANSWER': 'answer',
        'BINGO': 'bingo',
        'PLAYER_UPDATE': 'player_update',
        'GAME_STATE': 'game_state',
        'PING': 'ping',
        'PONG': 'pong',
        'ERROR': 'error'
    }
    
    @staticmethod
    def create_message(msg_type: str, data: Dict[str, Any], sender_id: str = None) -> Dict[str, Any]:
        """Crea un mensaje estandarizado"""
        return {
            'type': msg_type,
            'data': data,
            'timestamp': time.time(),
            'sender_id': sender_id or f"player_{random.randint(1000, 9999)}"
        }
    
    @staticmethod
    def create_login_message(player_name: str, player_id: str = None) -> Dict[str, Any]:
        """Crea mensaje de login"""
        return MultiplayerProtocol.create_message(
            MultiplayerProtocol.MESSAGE_TYPES['LOGIN'],
            {'player_name': player_name},
            player_id
        )
    
    @staticmethod
    def create_game_start_message(game_data: Dict[str, Any], host_id: str) -> Dict[str, Any]:
        """Crea mensaje de inicio de juego"""
        return MultiplayerProtocol.create_message(
            MultiplayerProtocol.MESSAGE_TYPES['GAME_START'],
            game_data,
            host_id
        )
    
    @staticmethod
    def create_question_message(question: Dict[str, Any], host_id: str) -> Dict[str, Any]:
        """Crea mensaje de pregunta"""
        return MultiplayerProtocol.create_message(
            MultiplayerProtocol.MESSAGE_TYPES['QUESTION'],
            question,
            host_id
        )
    
    @staticmethod
    def create_answer_message(player_name: str, answer: str, is_correct: bool, player_id: str) -> Dict[str, Any]:
        """Crea mensaje de respuesta"""
        return MultiplayerProtocol.create_message(
            MultiplayerProtocol.MESSAGE_TYPES['ANSWER'],
            {
                'player_name': player_name,
                'answer': answer,
                'correct': is_correct
            },
            player_id
        )
    
    @staticmethod
    def create_bingo_message(winner_name: str, winner_id: str) -> Dict[str, Any]:
        """Crea mensaje de bingo"""
        return MultiplayerProtocol.create_message(
            MultiplayerProtocol.MESSAGE_TYPES['BINGO'],
            {'winner': winner_name},
            winner_id
        )
    
    @staticmethod
    def create_player_update_message(players: List[Dict[str, Any]], host_id: str) -> Dict[str, Any]:
        """Crea mensaje de actualización de jugadores"""
        return MultiplayerProtocol.create_message(
            MultiplayerProtocol.MESSAGE_TYPES['PLAYER_UPDATE'],
            {'players': players},
            host_id
        )
    
    @staticmethod
    def create_error_message(error_msg: str, sender_id: str = None) -> Dict[str, Any]:
        """Crea mensaje de error"""
        return MultiplayerProtocol.create_message(
            MultiplayerProtocol.MESSAGE_TYPES['ERROR'],
            {'message': error_msg},
            sender_id
        )
    
    @staticmethod
    def validate_message(message: Dict[str, Any]) -> bool:
        """Valida que un mensaje tenga el formato correcto"""
        required_fields = ['type', 'data', 'timestamp', 'sender_id']
        return all(field in message for field in required_fields)
    
    @staticmethod
    def get_message_type(message: Dict[str, Any]) -> str:
        """Obtiene el tipo de mensaje"""
        return message.get('type', '')
    
    @staticmethod
    def get_message_data(message: Dict[str, Any]) -> Dict[str, Any]:
        """Obtiene los datos del mensaje"""
        return message.get('data', {})
    
    @staticmethod
    def get_sender_id(message: Dict[str, Any]) -> str:
        """Obtiene el ID del remitente"""
        return message.get('sender_id', '')


class ConnectionManager:
    """Gestor de conexiones para el multijugador"""
    
    def __init__(self):
        self.server_socket = None
        self.client_socket = None
        self.connected_players = []
        self.is_host = False
        self.is_connected = False
        self.room_code = None
        self.max_players = 10
        self.on_data_received = None
        self.on_player_connected = None
        self.on_player_disconnected = None
        self.on_connection_lost = None
        
        # Protocolo de comunicación
        self.protocol = MultiplayerProtocol()
    
    def start_server(self, port: int = 5000) -> bool:
        """Inicia el servidor"""
        try:
            self.server_socket = MultiplayerUtils.create_server_socket(port)
            if not self.server_socket:
                return False
            
            self.is_host = True
            self.room_code = MultiplayerUtils.generate_room_code()
            self.is_connected = True
            
            # Iniciar thread para aceptar conexiones
            threading.Thread(target=self._accept_connections, daemon=True).start()
            
            print(f"[DEBUG] Servidor iniciado en puerto {port}")
            return True
            
        except Exception as e:
            print(f"[ERROR] Error al iniciar servidor: {e}")
            return False
    
    def connect_to_server(self, host: str, port: int = 5000) -> bool:
        """Conecta al servidor"""
        try:
            self.client_socket = MultiplayerUtils.create_client_socket(host, port)
            if not self.client_socket:
                return False
            
            self.is_host = False
            self.is_connected = True
            
            # Iniciar thread para recibir datos
            threading.Thread(target=self._receive_data_client, daemon=True).start()
            
            print(f"[DEBUG] Conectado al servidor {host}:{port}")
            return True
            
        except Exception as e:
            print(f"[ERROR] Error al conectar al servidor: {e}")
            return False
    
    def send_to_all(self, data: Dict[str, Any]) -> bool:
        """Envía datos a todos los clientes conectados"""
        if not self.is_host:
            return False
        
        success = True
        disconnected_players = []
        
        for client, addr in self.connected_players:
            try:
                if not MultiplayerUtils.send_data(client, data):
                    disconnected_players.append((client, addr))
                    success = False
            except Exception as e:
                print(f"[ERROR] Error al enviar a {addr}: {e}")
                disconnected_players.append((client, addr))
                success = False
        
        # Remover jugadores desconectados
        for client, addr in disconnected_players:
            self._remove_player(client, addr)
        
        return success
    
    def send_to_server(self, data: Dict[str, Any]) -> bool:
        """Envía datos al servidor"""
        if not self.is_connected or self.is_host or not self.client_socket:
            return False
        
        return MultiplayerUtils.send_data(self.client_socket, data)
    
    def _accept_connections(self):
        """Acepta conexiones entrantes"""
        while self.is_host and self.server_socket:
            try:
                client, addr = self.server_socket.accept()
                print(f"[DEBUG] Cliente conectado desde {addr}")
                
                if len(self.connected_players) < self.max_players:
                    self.connected_players.append((client, addr))
                    if self.on_player_connected:
                        Clock.schedule_once(lambda dt: self.on_player_connected(addr), 0)
                    
                    # Iniciar thread para recibir datos de este cliente
                    threading.Thread(
                        target=self._receive_data_host, 
                        args=(client, addr), 
                        daemon=True
                    ).start()
                else:
                    client.close()
                    
            except socket.timeout:
                continue
            except Exception as e:
                print(f"[ERROR] Error al aceptar conexión: {e}")
                break
    
    def _receive_data_host(self, client: socket.socket, addr: tuple):
        """Recibe datos de un cliente específico"""
        while self.is_host and client:
            try:
                data = MultiplayerUtils.receive_data(client)
                if data is None:
                    break
                
                if self.on_data_received:
                    Clock.schedule_once(
                        lambda dt: self.on_data_received(data, addr), 0
                    )
                    
            except Exception as e:
                print(f"[ERROR] Error al recibir datos de {addr}: {e}")
                break
        
        self._remove_player(client, addr)
    
    def _receive_data_client(self):
        """Recibe datos del servidor"""
        while self.is_connected and self.client_socket:
            try:
                data = MultiplayerUtils.receive_data(self.client_socket)
                if data is None:
                    break
                
                if self.on_data_received:
                    Clock.schedule_once(
                        lambda dt: self.on_data_received(data, None), 0
                    )
                    
            except Exception as e:
                print(f"[ERROR] Error al recibir datos del servidor: {e}")
                break
        
        if self.on_connection_lost:
            Clock.schedule_once(lambda dt: self.on_connection_lost(), 0)
    
    def _remove_player(self, client: socket.socket, addr: tuple):
        """Remueve un jugador desconectado"""
        try:
            client.close()
        except:
            pass
        
        if (client, addr) in self.connected_players:
            self.connected_players.remove((client, addr))
            if self.on_player_disconnected:
                Clock.schedule_once(
                    lambda dt: self.on_player_disconnected(addr), 0
                )
    
    def disconnect(self):
        """Desconecta todas las conexiones"""
        self.is_connected = False
        
        # Cerrar servidor
        if self.server_socket:
            try:
                self.server_socket.close()
            except:
                pass
            self.server_socket = None
        
        # Cerrar cliente
        if self.client_socket:
            try:
                self.client_socket.close()
            except:
                pass
            self.client_socket = None
        
        # Cerrar conexiones de clientes
        for client, addr in self.connected_players:
            try:
                client.close()
            except:
                pass
        
        self.connected_players.clear()
        self.is_host = False
        self.room_code = None
        
        print("[DEBUG] Todas las conexiones cerradas")
    
    def get_player_count(self) -> int:
        """Obtiene el número de jugadores conectados"""
        return len(self.connected_players) + (1 if self.is_host else 0) 