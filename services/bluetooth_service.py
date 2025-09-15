"""
Servicio de Bluetooth para Android usando Pyjnius (API nativa Java)
Compatible con APKs generados con Buildozer
"""

import sys
import json
import threading
from kivy.utils import platform
from kivy.clock import Clock
from typing import Optional, Callable, List, Tuple

if platform == 'android':
    try:
        from jnius import autoclass, cast
        from android import mActivity
        
        class AndroidBluetoothService:
            def __init__(self):
                if platform != 'android':
                    raise NotImplementedError("Este servicio solo funciona en Android real.")
                
                # Clases de Android Bluetooth
                self.BluetoothAdapter = autoclass('android.bluetooth.BluetoothAdapter')
                self.BluetoothDevice = autoclass('android.bluetooth.BluetoothDevice')
                self.BluetoothSocket = autoclass('android.bluetooth.BluetoothSocket')
                self.UUID = autoclass('java.util.UUID')
                self.OutputStream = autoclass('java.io.OutputStream')
                self.InputStream = autoclass('java.io.InputStream')
                self.DataOutputStream = autoclass('java.io.DataOutputStream')
                self.DataInputStream = autoclass('java.io.DataInputStream')
                
                # Obtener el adaptador Bluetooth
                self.adapter = self.BluetoothAdapter.getDefaultAdapter()
                self.server_socket = None
                self.client_socket = None
                self.is_server = False
                self.is_connected = False
                self.found_devices = []
                self.on_device_found = None
                self.on_client_connected = None
                self.on_connected = None
                self.on_data_received = None
                
                print("[BLUETOOTH] Servicio inicializado correctamente")

            def is_bluetooth_enabled(self):
                """Verifica si Bluetooth está habilitado"""
                return self.adapter is not None and self.adapter.isEnabled()

            def enable_bluetooth(self):
                """Solicita habilitar Bluetooth"""
                if not self.is_bluetooth_enabled():
                    try:
                        PythonActivity = autoclass('org.kivy.android.PythonActivity')
                        Intent = autoclass('android.content.Intent')
                        activity = PythonActivity.mActivity
                        intent = Intent(self.BluetoothAdapter.ACTION_REQUEST_ENABLE)
                        activity.startActivity(intent)
                        return True
                    except Exception as e:
                        print(f"[BLUETOOTH] Error habilitando Bluetooth: {e}")
                        return False
                return True

            def get_paired_devices(self) -> List[Tuple[str, str]]:
                """Devuelve una lista de dispositivos emparejados (nombre, dirección)"""
                try:
                    if not self.adapter:
                        return []
                    
                    devices = self.adapter.getBondedDevices().toArray()
                    result = []
                    for device in devices:
                        name = device.getName() or "Dispositivo Desconocido"
                        address = device.getAddress()
                        result.append((name, address))
                    return result
                except Exception as e:
                    print(f"[BLUETOOTH] Error obteniendo dispositivos emparejados: {e}")
                    return []

            def discover_devices(self, callback: Callable[[str, str], None]):
                """Inicia la búsqueda de dispositivos"""
                try:
                    self.on_device_found = callback
                    
                    if not self.adapter:
                        return False
                    
                    # Detener búsqueda anterior si está activa
                    if self.adapter.isDiscovering():
                        self.adapter.cancelDiscovery()
                    
                    # Iniciar nueva búsqueda
                    success = self.adapter.startDiscovery()
                    if success:
                        print("[BLUETOOTH] Búsqueda iniciada")
                        # Programar finalización de búsqueda
                        Clock.schedule_once(self._finish_discovery, 12.0)  # 12 segundos
                        return True
                    else:
                        print("[BLUETOOTH] No se pudo iniciar la búsqueda")
                        return False
                        
                except Exception as e:
                    print(f"[BLUETOOTH] Error iniciando búsqueda: {e}")
                    return False

            def _finish_discovery(self, dt):
                """Finaliza la búsqueda de dispositivos"""
                try:
                    if self.adapter and self.adapter.isDiscovering():
                        self.adapter.cancelDiscovery()
                        print("[BLUETOOTH] Búsqueda finalizada")
                except Exception as e:
                    print(f"[BLUETOOTH] Error finalizando búsqueda: {e}")

            def start_server(self, uuid_str: str, on_client_connected: Callable):
                """Inicia un servidor Bluetooth (espera conexiones entrantes)"""
                try:
                    self.is_server = True
                    self.on_client_connected = on_client_connected
                    uuid = self.UUID.fromString(uuid_str)
                    
                    # Crear socket de servidor
                    self.server_socket = self.adapter.listenUsingRfcommWithServiceRecord("BingoServer", uuid)
                    print("[BLUETOOTH] Servidor iniciado, esperando conexiones...")
                    
                    # Iniciar thread para aceptar conexiones
                    threading.Thread(target=self._accept_connections, daemon=True).start()
                    return True
                    
                except Exception as e:
                    print(f"[BLUETOOTH] Error iniciando servidor: {e}")
                    self.is_server = False
                    return False

            def _accept_connections(self):
                """Acepta conexiones entrantes"""
                while self.is_server and self.server_socket:
                    try:
                        print("[BLUETOOTH] Esperando conexión de cliente...")
                        client_socket = self.server_socket.accept()
                        self.client_socket = client_socket
                        self.is_connected = True
                        print("[BLUETOOTH] Cliente conectado!")
                        
                        # Llamar callback
                        if self.on_client_connected:
                            Clock.schedule_once(lambda dt: self.on_client_connected(client_socket), 0)
                        
                        # Iniciar thread para recibir datos
                        threading.Thread(target=self._receive_data, daemon=True).start()
                        
                    except Exception as e:
                        print(f"[BLUETOOTH] Error aceptando conexión: {e}")
                        break

            def connect_to_server(self, address: str, uuid_str: str, on_connected: Callable):
                """Conecta como cliente a un servidor Bluetooth"""
                try:
                    self.on_connected = on_connected
                    uuid = self.UUID.fromString(uuid_str)
                    device = self.adapter.getRemoteDevice(address)
                    
                    # Crear socket de cliente
                    socket = device.createRfcommSocketToServiceRecord(uuid)
                    
                    # Conectar en thread separado
                    threading.Thread(target=self._connect_to_device, args=(socket,), daemon=True).start()
                    return True
                    
                except Exception as e:
                    print(f"[BLUETOOTH] Error conectando a {address}: {e}")
                    return False

            def _connect_to_device(self, socket):
                """Conecta al dispositivo en thread separado"""
                try:
                    print(f"[BLUETOOTH] Conectando...")
                    socket.connect()
                    self.client_socket = socket
                    self.is_connected = True
                    print("[BLUETOOTH] Conectado al servidor!")
                    
                    # Llamar callback
                    if self.on_connected:
                        Clock.schedule_once(lambda dt: self.on_connected(socket), 0)
                    
                    # Iniciar thread para recibir datos
                    threading.Thread(target=self._receive_data, daemon=True).start()
                    
                except Exception as e:
                    print(f"[BLUETOOTH] Error en conexión: {e}")
                    self.is_connected = False

            def _receive_data(self):
                """Recibe datos del socket"""
                while self.is_connected and self.client_socket:
                    try:
                        data = self.receive_data()
                        if data and self.on_data_received:
                            Clock.schedule_once(lambda dt: self.on_data_received(data), 0)
                    except Exception as e:
                        print(f"[BLUETOOTH] Error recibiendo datos: {e}")
                        break
                
                self.is_connected = False

            def send_data(self, data: bytes) -> bool:
                """Envía datos por Bluetooth"""
                try:
                    if not self.client_socket or not self.is_connected:
                        return False
                    
                    output_stream = self.client_socket.getOutputStream()
                    output_stream.write(data)
                    output_stream.flush()
                    return True
                    
                except Exception as e:
                    print(f"[BLUETOOTH] Error enviando datos: {e}")
                    return False

            def send_json(self, data: dict) -> bool:
                """Envía datos JSON por Bluetooth"""
                try:
                    json_str = json.dumps(data, ensure_ascii=False)
                    json_bytes = json_str.encode('utf-8')
                    
                    # Enviar longitud primero
                    length_bytes = len(json_bytes).to_bytes(4, 'big')
                    if not self.send_data(length_bytes):
                        return False
                    
                    # Enviar datos JSON
                    return self.send_data(json_bytes)
                    
                except Exception as e:
                    print(f"[BLUETOOTH] Error enviando JSON: {e}")
                    return False

            def receive_data(self, bufsize: int = 1024) -> Optional[bytes]:
                """Recibe datos del socket"""
                try:
                    if not self.client_socket or not self.is_connected:
                        return None
                    
                    input_stream = self.client_socket.getInputStream()
                    buffer = bytearray(bufsize)
                    n = input_stream.read(buffer)
                    
                    if n > 0:
                        return bytes(buffer[:n])
                    return None
                    
                except Exception as e:
                    print(f"[BLUETOOTH] Error recibiendo datos: {e}")
                    return None

            def receive_json(self) -> Optional[dict]:
                """Recibe datos JSON del socket"""
                try:
                    # Recibir longitud
                    length_data = self.receive_data(4)
                    if not length_data:
                        return None
                    
                    length = int.from_bytes(length_data, 'big')
                    
                    # Recibir datos JSON
                    json_data = self.receive_data(length)
                    if not json_data:
                        return None
                    
                    json_str = json_data.decode('utf-8')
                    return json.loads(json_str)
                    
                except Exception as e:
                    print(f"[BLUETOOTH] Error recibiendo JSON: {e}")
                    return None

            def close(self):
                """Cierra todas las conexiones"""
                self.is_connected = False
                self.is_server = False
                
                try:
                    if self.client_socket:
                        self.client_socket.close()
                        self.client_socket = None
                except:
                    pass
                
                try:
                    if self.server_socket:
                        self.server_socket.close()
                        self.server_socket = None
                except:
                    pass
                
                print("[BLUETOOTH] Conexiones cerradas")

            def cleanup(self):
                """Limpia recursos"""
                self.close()

    except ImportError as e:
        print(f"[BLUETOOTH] Error importando módulos de Android: {e}")
        # Fallback para desarrollo
        class AndroidBluetoothService:
            def __init__(self):
                print("[BLUETOOTH] Modo desarrollo: Bluetooth no disponible")
                self.is_connected = False
                self.is_server = False
            
            def is_bluetooth_enabled(self): return False
            def enable_bluetooth(self): return False
            def get_paired_devices(self): return []
            def discover_devices(self, callback): return False
            def start_server(self, uuid_str, on_client_connected): return False
            def connect_to_server(self, address, uuid_str, on_connected): return False
            def send_data(self, data): return False
            def send_json(self, data): return False
            def receive_data(self, bufsize=1024): return None
            def receive_json(self): return None
            def close(self): pass
            def cleanup(self): pass

else:
    # Implementación para desarrollo (no Android)
    class AndroidBluetoothService:
        def __init__(self):
            print("[BLUETOOTH] Modo desarrollo: Bluetooth no disponible")
            self.is_connected = False
            self.is_server = False
        
        def is_bluetooth_enabled(self): return False
        def enable_bluetooth(self): return False
        def get_paired_devices(self): return []
        def discover_devices(self, callback): return False
        def start_server(self, uuid_str, on_client_connected): return False
        def connect_to_server(self, address, uuid_str, on_connected): return False
        def send_data(self, data): return False
        def send_json(self, data): return False
        def receive_data(self, bufsize=1024): return None
        def receive_json(self): return None
        def close(self): pass
        def cleanup(self): pass

# UUID estándar para SPP (Serial Port Profile)
BLUETOOTH_UUID = "00001101-0000-1000-8000-00805F9B34FB" 