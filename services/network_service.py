"""
Servicio de Red para Multijugador
Maneja toda la comunicación de red de manera robusta y confiable
"""

import socket
import threading
import json
import time
import random
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass
from enum import Enum
from kivy.clock import Clock
from kivy.properties import BooleanProperty, StringProperty

from utils.constants import NetworkConfig


class MessageType(Enum):
    """Tipos de mensajes de red"""
    JOIN_GAME = "join_game"
    LEAVE_GAME = "leave_game"
    START_GAME = "start_game"
    END_GAME = "end_game"
    QUESTION = "question"
    ANSWER = "answer"
    BINGO = "bingo"
    CHAT = "chat"
    PLAYER_UPDATE = "player_update"
    GAME_STATE = "game_state"
    PING = "ping"
    PONG = "pong"


@dataclass
class NetworkMessage:
    """Mensaje de red estructurado"""
    type: MessageType
    data: Dict[str, Any]
    timestamp: float
    sender_id: str
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'type': self.type.value,
            'data': self.data,
            'timestamp': self.timestamp,
            'sender_id': self.sender_id
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'NetworkMessage':
        return cls(
            type=MessageType(data['type']),
            data=data['data'],
            timestamp=data['timestamp'],
            sender_id=data['sender_id']
        )


@dataclass
class Player:
    """Información de un jugador en red"""
    id: str
    name: str
    ip: str
    port: int
    connected: bool = True
    last_seen: float = 0
    score: int = 0
    is_host: bool = False


class NetworkService:
    """
    Servicio de red para manejar comunicación multijugador
    """
    
    def __init__(self):
        self.server_socket: Optional[socket.socket] = None
        self.client_socket: Optional[socket.socket] = None
        self.is_host = BooleanProperty(False)
        self.is_connected = BooleanProperty(False)
        self.room_code = StringProperty('')
        self.local_ip = StringProperty('')
        
        self.players: Dict[str, Player] = {}
        self.message_handlers: Dict[MessageType, List[Callable]] = {}
        self.connection_callbacks: List[Callable] = []
        self.disconnection_callbacks: List[Callable] = []
        
        self.server_thread: Optional[threading.Thread] = None
        self.client_thread: Optional[threading.Thread] = None
        self.heartbeat_thread: Optional[threading.Thread] = None
        
        self.running = False
        self.heartbeat_interval = 5.0  # segundos
        
        # Configuración
        self.port = NetworkConfig.DEFAULT_PORT
        self.max_players = NetworkConfig.MAX_CONNECTIONS
        self.timeout = NetworkConfig.TIMEOUT
        self.buffer_size = NetworkConfig.BUFFER_SIZE
    
    def get_local_ip(self) -> str:
        """Obtiene la IP local del dispositivo"""
        try:
            # Crear socket temporal para obtener IP
            with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
                s.connect(('8.8.8.8', 80))
                ip = s.getsockname()[0]
                return ip
        except Exception as e:
            print(f"Error obteniendo IP local: {e}")
            return '127.0.0.1'
    
    def generate_room_code(self) -> str:
        """Genera un código de sala único"""
        return ''.join(random.choices('0123456789', k=6))
    
    def register_message_handler(self, message_type: MessageType, handler: Callable) -> None:
        """Registra un manejador para un tipo de mensaje"""
        if message_type not in self.message_handlers:
            self.message_handlers[message_type] = []
        self.message_handlers[message_type].append(handler)
    
    def register_connection_callback(self, callback: Callable) -> None:
        """Registra un callback para eventos de conexión"""
        self.connection_callbacks.append(callback)
    
    def register_disconnection_callback(self, callback: Callable) -> None:
        """Registra un callback para eventos de desconexión"""
        self.disconnection_callbacks.append(callback)
    
    def start_server(self, player_name: str) -> bool:
        """
        Inicia el servidor para crear una sala
        
        Args:
            player_name: Nombre del jugador host
            
        Returns:
            bool: True si el servidor se inició correctamente
        """
        try:
            # Crear socket del servidor
            self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.server_socket.bind(('0.0.0.0', self.port))
            self.server_socket.listen(self.max_players)
            
            # Configurar como host
            self.is_host = True
            self.room_code = self.generate_room_code()
            self.local_ip = self.get_local_ip()
            
            # Agregar jugador host
            host_player = Player(
                id=f"host_{int(time.time())}",
                name=player_name,
                ip=self.local_ip,
                port=self.port,
                is_host=True
            )
            self.players[host_player.id] = host_player
            
            # Iniciar thread del servidor
            self.running = True
            self.server_thread = threading.Thread(target=self._server_loop, daemon=True)
            self.server_thread.start()
            
            # Iniciar heartbeat
            self.heartbeat_thread = threading.Thread(target=self._heartbeat_loop, daemon=True)
            self.heartbeat_thread.start()
            
            print(f"[SERVER] Servidor iniciado en {self.local_ip}:{self.port}")
            print(f"[SERVER] Código de sala: {self.room_code}")
            
            return True
            
        except Exception as e:
            print(f"[ERROR] Error iniciando servidor: {e}")
            self.cleanup()
            return False
    
    def connect_to_server(self, server_ip: str, player_name: str) -> bool:
        """
        Conecta a un servidor como cliente
        
        Args:
            server_ip: IP del servidor
            player_name: Nombre del jugador
            
        Returns:
            bool: True si la conexión fue exitosa
        """
        try:
            # Crear socket del cliente
            self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.client_socket.settimeout(self.timeout)
            self.client_socket.connect((server_ip, self.port))
            
            # Configurar como cliente
            self.is_host = False
            self.local_ip = self.get_local_ip()
            
            # Enviar mensaje de unión
            join_message = NetworkMessage(
                type=MessageType.JOIN_GAME,
                data={'player_name': player_name},
                timestamp=time.time(),
                sender_id=f"client_{int(time.time())}"
            )
            self._send_message(join_message)
            
            # Iniciar thread del cliente
            self.running = True
            self.client_thread = threading.Thread(target=self._client_loop, daemon=True)
            self.client_thread.start()
            
            print(f"[CLIENT] Conectado a servidor {server_ip}:{self.port}")
            
            return True
            
        except Exception as e:
            print(f"[ERROR] Error conectando al servidor: {e}")
            self.cleanup()
            return False
    
    def _server_loop(self) -> None:
        """Loop principal del servidor"""
        while self.running and self.server_socket:
            try:
                client_socket, address = self.server_socket.accept()
                print(f"[SERVER] Cliente conectado desde {address}")
                
                # Manejar nueva conexión
                client_thread = threading.Thread(
                    target=self._handle_client_connection,
                    args=(client_socket, address),
                    daemon=True
                )
                client_thread.start()
                
            except Exception as e:
                if self.running:
                    print(f"[ERROR] Error en servidor: {e}")
                break
    
    def _handle_client_connection(self, client_socket: socket.socket, address: tuple) -> None:
        """Maneja la conexión de un cliente"""
        try:
            while self.running:
                data = client_socket.recv(self.buffer_size)
                if not data:
                    break
                
                # Procesar mensaje
                message_data = json.loads(data.decode('utf-8'))
                message = NetworkMessage.from_dict(message_data)
                self._process_message(message, client_socket)
                
        except Exception as e:
            print(f"[ERROR] Error manejando cliente {address}: {e}")
        finally:
            client_socket.close()
    
    def _client_loop(self) -> None:
        """Loop principal del cliente"""
        while self.running and self.client_socket:
            try:
                data = self.client_socket.recv(self.buffer_size)
                if not data:
                    break
                
                # Procesar mensaje
                message_data = json.loads(data.decode('utf-8'))
                message = NetworkMessage.from_dict(message_data)
                self._process_message(message)
                
            except Exception as e:
                if self.running:
                    print(f"[ERROR] Error en cliente: {e}")
                break
        
        # Notificar desconexión
        self._notify_disconnection()
    
    def _process_message(self, message: NetworkMessage, client_socket: Optional[socket.socket] = None) -> None:
        """Procesa un mensaje recibido"""
        print(f"[NETWORK] Procesando mensaje: {message.type.value}")
        
        # Actualizar timestamp del jugador
        if message.sender_id in self.players:
            self.players[message.sender_id].last_seen = time.time()
        
        # Ejecutar manejadores registrados
        if message.type in self.message_handlers:
            for handler in self.message_handlers[message.type]:
                try:
                    handler(message, client_socket)
                except Exception as e:
                    print(f"[ERROR] Error en manejador de mensaje: {e}")
    
    def _send_message(self, message: NetworkMessage, client_socket: Optional[socket.socket] = None) -> bool:
        """Envía un mensaje"""
        try:
            message_data = json.dumps(message.to_dict()).encode('utf-8')
            
            if client_socket:
                client_socket.send(message_data)
            elif self.client_socket:
                self.client_socket.send(message_data)
            elif self.server_socket:
                # Broadcast a todos los clientes
                self._broadcast_message(message)
            else:
                return False
                
            return True
            
        except Exception as e:
            print(f"[ERROR] Error enviando mensaje: {e}")
            return False
    
    def _broadcast_message(self, message: NetworkMessage) -> None:
        """Envía un mensaje a todos los clientes conectados"""
        # Esta implementación simplificada
        # En una implementación real, mantendrías una lista de clientes conectados
        pass
    
    def _heartbeat_loop(self) -> None:
        """Loop de heartbeat para mantener conexiones activas"""
        while self.running:
            try:
                time.sleep(self.heartbeat_interval)
                
                if self.is_host:
                    # Enviar heartbeat como servidor
                    heartbeat = NetworkMessage(
                        type=MessageType.PING,
                        data={},
                        timestamp=time.time(),
                        sender_id="server"
                    )
                    self._broadcast_message(heartbeat)
                
            except Exception as e:
                print(f"[ERROR] Error en heartbeat: {e}")
    
    def send_game_state(self, game_state: Dict[str, Any]) -> None:
        """Envía el estado del juego a todos los jugadores"""
        message = NetworkMessage(
            type=MessageType.GAME_STATE,
            data=game_state,
            timestamp=time.time(),
            sender_id="server" if self.is_host else "client"
        )
        self._send_message(message)
    
    def send_question(self, question: Dict[str, Any]) -> None:
        """Envía una pregunta a todos los jugadores"""
        message = NetworkMessage(
            type=MessageType.QUESTION,
            data=question,
            timestamp=time.time(),
            sender_id="server" if self.is_host else "client"
        )
        self._send_message(message)
    
    def send_answer(self, player_id: str, answer: Dict[str, Any]) -> None:
        """Envía una respuesta de un jugador"""
        message = NetworkMessage(
            type=MessageType.ANSWER,
            data=answer,
            timestamp=time.time(),
            sender_id=player_id
        )
        self._send_message(message)
    
    def send_bingo(self, player_id: str, bingo_data: Dict[str, Any]) -> None:
        """Envía notificación de bingo"""
        message = NetworkMessage(
            type=MessageType.BINGO,
            data=bingo_data,
            timestamp=time.time(),
            sender_id=player_id
        )
        self._send_message(message)
    
    def _notify_connection(self) -> None:
        """Notifica eventos de conexión"""
        self.is_connected = True
        for callback in self.connection_callbacks:
            try:
                callback()
            except Exception as e:
                print(f"[ERROR] Error en callback de conexión: {e}")
    
    def _notify_disconnection(self) -> None:
        """Notifica eventos de desconexión"""
        self.is_connected = False
        for callback in self.disconnection_callbacks:
            try:
                callback()
            except Exception as e:
                print(f"[ERROR] Error en callback de desconexión: {e}")
    
    def get_players(self) -> List[Player]:
        """Obtiene la lista de jugadores conectados"""
        return list(self.players.values())
    
    def get_player_count(self) -> int:
        """Obtiene el número de jugadores conectados"""
        return len(self.players)
    
    def is_server_full(self) -> bool:
        """Verifica si el servidor está lleno"""
        return len(self.players) >= self.max_players
    
    def cleanup(self) -> None:
        """Limpia recursos de red"""
        self.running = False
        
        # Cerrar sockets
        if self.server_socket:
            self.server_socket.close()
            self.server_socket = None
        
        if self.client_socket:
            self.client_socket.close()
            self.client_socket = None
        
        # Esperar threads
        if self.server_thread and self.server_thread.is_alive():
            self.server_thread.join(timeout=1)
        
        if self.client_thread and self.client_thread.is_alive():
            self.client_thread.join(timeout=1)
        
        if self.heartbeat_thread and self.heartbeat_thread.is_alive():
            self.heartbeat_thread.join(timeout=1)
        
        # Limpiar jugadores
        self.players.clear()
        self.is_host = False
        self.is_connected = False
        self.room_code = ''
        
        print("[NETWORK] Recursos de red limpiados")


# Instancia global del servicio de red
network_service = NetworkService() 