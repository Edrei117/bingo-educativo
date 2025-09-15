from kivy.uix.screenmanager import Screen
from kivy.properties import StringProperty
from kivy.clock import Clock
import socket
import json
import threading
import asyncio
from bleak import BleakScanner, BleakClient
from kivy.app import App
from kivymd.uix.list import OneLineListItem
from kivymd.uix.button import MDFlatButton
from kivymd.uix.dialog import MDDialog
from kivymd.uix.textfield import MDTextField
from kivymd.uix.spinner import MDSpinner
from kivymd.uix.label import MDLabel
from kivymd.uix.button import MDRaisedButton
# --- INICIO: Importar pyjnius para Bluetooth clásico ---
from jnius import autoclass, cast
from android import mActivity
# --- FIN: Importar pyjnius ---

class NetworkScreen(Screen):
    status_text = StringProperty("")
    is_host = False
    socket = None
    connected_players = []
    bluetooth_devices = []
    selected_device = None
    dialog = None
    spinner = None

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.dialog = None
        self.spinner = None
        self.bluetooth_client = None

    def mostrar_dialogo(self, titulo, mensaje):
        if self.dialog:
            self.dialog.dismiss()
            self.dialog = None
            
        dialog = MDDialog(
            title=titulo,
            text=mensaje,
            buttons=[
                MDFlatButton(
                    text="OK",
                    on_release=lambda x: dialog.dismiss()
                )
            ]
        )
        self.dialog = dialog
        dialog.open()

    def mostrar_spinner(self, mensaje):
        if self.spinner:
            self.spinner.dismiss()
        self.spinner = MDDialog(
            title="",
            type="custom",
            content_cls=MDLabel(
                text=mensaje,
                halign="center"
            ),
            buttons=[]
        )
        self.spinner.open()

    def ocultar_spinner(self):
        if self.spinner:
            self.spinner.dismiss()
            self.spinner = None

    def crear_sala(self):
        """Crea una sala de juego como host"""
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.bind(('0.0.0.0', 5000))
            self.socket.listen(4)  # Máximo 4 jugadores
            self.is_host = True
            self.status_text = "Esperando jugadores..."
            
            # Iniciar thread para aceptar conexiones
            threading.Thread(target=self.aceptar_conexiones_wifi, daemon=True).start()
            
            # Mostrar diálogo para ingresar nombre de sala
            self.mostrar_dialogo_crear_sala()
            
        except Exception as e:
            self.mostrar_dialogo("Error", f"No se pudo crear la sala: {str(e)}")
            self.status_text = "Error al crear sala"

    def mostrar_dialogo_crear_sala(self):
        """Muestra diálogo para crear sala con nombre y número de jugadores"""
        content = MDTextField(
            hint_text="Nombre de la sala",
            helper_text="Ingresa un nombre para tu sala",
            helper_text_mode="on_error",
        )
        
        dialog = MDDialog(
            title="Crear Sala",
            type="custom",
            content_cls=content,
            buttons=[
                MDFlatButton(
                    text="CANCELAR",
                    on_release=lambda x: dialog.dismiss()
                ),
                MDFlatButton(
                    text="CREAR",
                    on_release=lambda x: self.confirmar_crear_sala(content.text)
                ),
            ],
        )
        self.dialog = dialog
        dialog.open()

    def confirmar_crear_sala(self, nombre_sala):
        """Confirma la creación de la sala con el nombre ingresado"""
        if not nombre_sala:
            self.mostrar_dialogo("Error", "Debes ingresar un nombre para la sala")
            return
            
        # Cerrar el diálogo actual
        if hasattr(self, 'dialog') and self.dialog is not None:
            self.dialog.dismiss()
            self.dialog = None
            
        self.status_text = f"Sala '{nombre_sala}' creada. Esperando jugadores..."
        # Aquí puedes guardar el nombre de la sala y usarlo cuando se conecten jugadores

    def unirse_sala(self):
        """Muestra diálogo para ingresar nombre y luego IP del host (WiFi)"""
        self.mostrar_dialogo_nombre_wifi()

    def mostrar_dialogo_nombre_wifi(self):
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
                    on_release=lambda x: self.mostrar_dialogo_ip_wifi(content.text)
                ),
                MDRaisedButton(
                    text="Cancelar",
                    on_release=lambda x: dialog.dismiss()
                )
            ],
        )
        self.dialog = dialog
        dialog.open()

    def mostrar_dialogo_ip_wifi(self, nombre_jugador):
        if not nombre_jugador:
            self.mostrar_dialogo("Error", "Debes ingresar tu nombre")
            return
        self.nombre_jugador_wifi = nombre_jugador
        content = MDTextField(
            hint_text="IP del host",
            helper_text="Ingresa la IP del host",
            helper_text_mode="on_error",
        )
        dialog = MDDialog(
            title="Unirse a Sala",
            type="custom",
            content_cls=content,
            buttons=[
                MDRaisedButton(
                    text="Conectar",
                    on_release=lambda x: self.confirmar_unirse_sala_wifi(content.text, nombre_jugador)
                ),
                MDRaisedButton(
                    text="Cancelar",
                    on_release=lambda x: dialog.dismiss()
                )
            ],
        )
        self.dialog = dialog
        dialog.open()

    def confirmar_unirse_sala_wifi(self, ip_host, nombre_jugador):
        if not ip_host:
            self.mostrar_dialogo("Error", "Debes ingresar la IP del host")
            return
        if not nombre_jugador:
            self.mostrar_dialogo("Error", "Debes ingresar tu nombre")
            return
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.connect((ip_host, 5000))
            self.is_host = False
            self.status_text = "Conectado a la sala"
            # Enviar nombre al host
            import json
            mensaje = json.dumps({'tipo': 'login', 'nombre': nombre_jugador})
            self.socket.send(mensaje.encode('utf-8'))
            # Iniciar thread para recibir mensajes
            threading.Thread(target=self.recibir_mensajes_wifi, daemon=True).start()
            # Cerrar el diálogo actual
            if hasattr(self, 'dialog') and self.dialog is not None:
                self.dialog.dismiss()
                self.dialog = None
        except Exception as e:
            self.mostrar_dialogo("Error", f"No se pudo conectar a la sala: {str(e)}")
            self.status_text = "Error al conectar"

    def aceptar_conexiones_wifi(self):
        if self.socket is None:
            return
        while True:
            try:
                client, addr = self.socket.accept()
                # Esperar a recibir el mensaje de login antes de agregar a la lista
                data = client.recv(1024)
                if not data:
                    client.close()
                    continue
                import json
                datos = json.loads(data.decode())
                if datos.get('tipo') == 'login' and 'nombre' in datos:
                    if not hasattr(self, 'nombres_jugadores'):
                        self.nombres_jugadores = []
                    if not hasattr(self, 'connected_players'):
                        self.connected_players = []
                    self.nombres_jugadores.append(datos['nombre'])
                    self.connected_players.append((client, datos['nombre']))
                    self.status_text = f"Jugador conectado: {datos['nombre']}"
                    self.actualizar_lista_jugadores()
                else:
                    client.close()
            except Exception as e:
                print(f"Error aceptando conexión: {e}")
                break

    def recibir_mensajes_wifi(self):
        """Recibe mensajes del host cuando es cliente"""
        if self.socket is None:
            return
            
        while True:
            try:
                data = self.socket.recv(1024)
                if not data:
                    break
                import json
                datos = json.loads(data.decode())
                if datos.get('tipo') == 'bingo':
                    ganador = datos.get('jugador', 'Desconocido')
                    self.mostrar_dialogo("¡Bingo!", f"¡{ganador} ha ganado el juego!")
                elif datos.get('tipo') == 'login':
                    # El host agrega el nombre a la lista de jugadores
                    if self.is_host:
                        if not hasattr(self, 'nombres_jugadores'):
                            self.nombres_jugadores = []
                        self.nombres_jugadores.append(datos['nombre'])
                        print(f"Jugador conectado: {datos['nombre']}")
                        self.actualizar_lista_jugadores() # Actualizar la UI
                else:
                    self.procesar_mensaje(datos)
            except Exception as e:
                print(f"Error recibiendo mensaje: {e}")
                break

    def enviar_estado_juego(self, client):
        """Envía el estado actual del juego a un cliente"""
        if not self.is_host:
            return
            
        try:
            estado = self.manager.get_screen('game').obtener_estado_juego()
            client.send(json.dumps(estado).encode())
        except Exception as e:
            print(f"Error enviando estado: {e}")

    def procesar_mensaje(self, datos):
        """Procesa mensajes recibidos de la red"""
        if not self.is_host:
            self.manager.get_screen('game').actualizar_estado_juego(datos)

    def on_leave(self):
        """Limpia recursos al salir de la pantalla"""
        if self.socket:
            self.socket.close()
            self.socket = None
        self.connected_players.clear()
        self.status_text = ""

    # --- INICIO: Buscar dispositivos Bluetooth clásicos emparejados ---
    def buscar_dispositivos_bluetooth(self):
        """Busca dispositivos Bluetooth clásicos emparejados y los muestra en la UI"""
        try:
            BluetoothAdapter = autoclass('android.bluetooth.BluetoothAdapter')
            adapter = BluetoothAdapter.getDefaultAdapter()
            if not adapter:
                self.mostrar_dialogo("Error", "Bluetooth no soportado en este dispositivo.")
                return
            if not adapter.isEnabled():
                # Solicitar al usuario que active Bluetooth
                intent = autoclass('android.content.Intent')(BluetoothAdapter.ACTION_REQUEST_ENABLE)
                mActivity.startActivity(intent)
                self.mostrar_dialogo("Bluetooth", "Por favor, activa Bluetooth y vuelve a intentar.")
                return
            # Limpiar lista en la UI
            if hasattr(self.ids, 'bluetooth_devices'):
                self.ids.bluetooth_devices.clear_widgets()
            # Obtener dispositivos emparejados
            paired_devices = adapter.getBondedDevices().toArray()
            self.bluetooth_devices = []
            for device in paired_devices:
                name = device.getName()
                address = device.getAddress()
                self.bluetooth_devices.append(device)
                if hasattr(self.ids, 'bluetooth_devices'):
                    self.ids.bluetooth_devices.add_widget(
                        OneLineListItem(
                            text=f"{name} ({address})",
                            on_release=lambda x, d=device: self.seleccionar_dispositivo_bluetooth(d)
                        )
                    )
            if not paired_devices:
                self.mostrar_dialogo("Bluetooth", "No hay dispositivos emparejados. Empareja uno en la configuración de Android.")
        except Exception as e:
            print(f"Error al buscar dispositivos Bluetooth: {e}")
            self.mostrar_dialogo("Error", f"No se pudo buscar dispositivos Bluetooth: {e}")
    # --- FIN: Buscar dispositivos Bluetooth clásicos emparejados ---

    def seleccionar_dispositivo_bluetooth(self, device):
        """Selecciona un dispositivo Bluetooth para conectar"""
        self.selected_device = device
        self.mostrar_dialogo("Bluetooth", f"Dispositivo seleccionado: {device.getName()} ({device.getAddress()})")

    def crear_partida_bluetooth(self):
        """Crea una partida como host por Bluetooth (servidor RFCOMM)"""
        try:
            BluetoothAdapter = autoclass('android.bluetooth.BluetoothAdapter')
            adapter = BluetoothAdapter.getDefaultAdapter()
            uuid = "00001101-0000-1000-8000-00805F9B34FB"
            BluetoothServerSocket = autoclass('android.bluetooth.BluetoothServerSocket')
            server_socket = adapter.listenUsingRfcommWithServiceRecord("BingoQuiz", autoclass('java.util.UUID').fromString(uuid))
            self.socket = server_socket
            self.is_host = True
            self.status_text = "Esperando conexión Bluetooth..."
            self.mostrar_dialogo("Bluetooth", "Esperando que un jugador se conecte por Bluetooth...")
            # Iniciar hilo para aceptar conexiones entrantes
            threading.Thread(target=self.aceptar_conexiones_bluetooth, daemon=True).start()
        except Exception as e:
            print(f"Error al crear partida Bluetooth: {e}")
            self.mostrar_dialogo("Error", f"No se pudo crear la partida Bluetooth: {e}")

    def aceptar_conexiones_bluetooth(self):
        """Acepta conexiones entrantes por Bluetooth (solo host)"""
        try:
            if self.socket is None:
                print("[Bluetooth] Error: server_socket es None")
                return
            client_socket = self.socket.accept()[0]  # accept() devuelve (socket, address)
            self.connected_players.append(client_socket)
            self.status_text = "Jugador conectado por Bluetooth"
            self.mostrar_dialogo("Bluetooth", "¡Jugador conectado por Bluetooth!")
            # Iniciar hilo para recibir mensajes
            threading.Thread(target=self.recibir_mensajes_bluetooth, args=(client_socket,), daemon=True).start()
            # Aquí puedes cambiar a la pantalla de juego si es necesario
            # self.manager.get_screen('game').iniciar_juego_multijugador(True)
            # self.manager.current = 'game'
        except Exception as e:
            print(f"Error aceptando conexión Bluetooth: {e}")
            self.mostrar_dialogo("Error", f"No se pudo aceptar la conexión Bluetooth: {e}")

    def conectar_como_cliente_bluetooth(self):
        """Conecta al dispositivo Bluetooth seleccionado como cliente (RFCOMM)"""
        try:
            if not hasattr(self, 'selected_device') or self.selected_device is None:
                self.mostrar_dialogo("Error", "Selecciona un dispositivo Bluetooth primero.")
                return
            uuid = "00001101-0000-1000-8000-00805F9B34FB"
            BluetoothSocket = autoclass('android.bluetooth.BluetoothSocket')
            socket = self.selected_device.createRfcommSocketToServiceRecord(
                autoclass('java.util.UUID').fromString(uuid)
            )
            BluetoothAdapter = autoclass('android.bluetooth.BluetoothAdapter')
            adapter = BluetoothAdapter.getDefaultAdapter()
            if adapter.isDiscovering():
                adapter.cancelDiscovery()
            socket.connect()
            self.socket = socket
            self.is_host = False
            self.status_text = f"Conectado a {self.selected_device.getName()}"
            # Iniciar hilo para recibir mensajes
            threading.Thread(target=self.recibir_mensajes_bluetooth, args=(socket,), daemon=True).start()
            self.mostrar_dialogo("Bluetooth", f"¡Conectado a {self.selected_device.getName()}!")
            # Cambiar a la pantalla de juego si es necesario
            # self.manager.get_screen('game').iniciar_juego_multijugador(False)
            # self.manager.current = 'game'
        except Exception as e:
            print(f"Error al conectar como cliente Bluetooth: {e}")
            self.mostrar_dialogo("Error", f"No se pudo conectar: {e}")

    def recibir_mensajes_bluetooth(self, sock):
        """Recibe mensajes por Bluetooth (tanto host como cliente)"""
        try:
            while True:
                data = sock.recv(1024)
                if not data:
                    break
                # Aquí puedes procesar el mensaje recibido (por ejemplo, decodificar JSON)
                try:
                    mensaje = data.decode('utf-8')
                    print(f"[Bluetooth] Mensaje recibido: {mensaje}")
                    datos = json.loads(mensaje)
                    if datos['tipo'] == 'login':
                        # El host agrega el nombre a la lista de jugadores
                        if self.is_host:
                            if not hasattr(self, 'nombres_jugadores'):
                                self.nombres_jugadores = []
                            self.nombres_jugadores.append(datos['nombre'])
                            print(f"Jugador conectado: {datos['nombre']}")
                            self.actualizar_lista_jugadores() # Actualizar la UI
                    elif datos['tipo'] == 'bingo':
                        # Mostrar quién ganó
                        ganador = datos['jugador']
                        self.mostrar_dialogo("¡Bingo!", f"¡{ganador} ha ganado el juego!")
                except Exception as e:
                    print(f"Error procesando mensaje Bluetooth: {e}")
        except Exception as e:
            print(f"Error recibiendo mensajes Bluetooth: {e}") 

    def enviar_mensaje_bluetooth(self, mensaje, sock=None):
        """Envía un mensaje por Bluetooth (host: a todos los clientes, cliente: al host)"""
        try:
            if self.is_host:
                # Enviar a todos los clientes conectados
                for client in self.connected_players:
                    client.send(mensaje.encode('utf-8'))
            else:
                # Enviar al host (si sock no se pasa, usar self.socket)
                target_sock = sock if sock else self.socket
                if target_sock:
                    target_sock.send(mensaje.encode('utf-8'))
        except Exception as e:
            print(f"Error enviando mensaje Bluetooth: {e}")

    def enviar_login_bluetooth(self, nombre_jugador):
        """Envía el nombre del jugador al host al conectarse (mensaje tipo 'login')"""
        import json
        mensaje = json.dumps({'tipo': 'login', 'nombre': nombre_jugador})
        self.enviar_mensaje_bluetooth(mensaje)

    def enviar_bingo_bluetooth(self, nombre_ganador):
        """El host envía un mensaje de bingo a todos los jugadores con el nombre del ganador"""
        import json
        mensaje = json.dumps({'tipo': 'bingo', 'jugador': nombre_ganador})
        self.enviar_mensaje_bluetooth(mensaje)

    # Ejemplo de uso en el flujo de juego:
    # self.enviar_mensaje_bluetooth(json.dumps({'tipo': 'pregunta', 'contenido': '¿Cuánto es 2+2?'}))
    # O para enviar desde el cliente:
    # self.enviar_mensaje_bluetooth(json.dumps({'tipo': 'respuesta', 'opcion': 1})) 

    def unirse_sala_bluetooth(self):
        """Muestra diálogo para ingresar nombre antes de buscar y conectar por Bluetooth"""
        self.mostrar_dialogo_nombre_bluetooth()

    def mostrar_dialogo_nombre_bluetooth(self):
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
                    text="Buscar y conectar",
                    on_release=lambda x: self.buscar_y_conectar_bluetooth(content.text)
                ),
                MDRaisedButton(
                    text="Cancelar",
                    on_release=lambda x: dialog.dismiss()
                )
            ],
        )
        self.dialog = dialog
        dialog.open()

    def buscar_y_conectar_bluetooth(self, nombre_jugador):
        if not nombre_jugador:
            self.mostrar_dialogo("Error", "Debes ingresar tu nombre")
            return
        self.nombre_jugador_bluetooth = nombre_jugador
        # Aquí llamas a la función de búsqueda y conexión Bluetooth
        # Por ejemplo, mostrar la lista de dispositivos y al conectar enviar el login:
        self.buscar_dispositivos_bluetooth()
        # Cuando se conecte, enviar el login:
        # self.enviar_login_bluetooth(nombre_jugador) 

    def actualizar_lista_jugadores(self):
        """Actualiza la lista de nombres de jugadores en la UI (incluyendo el host)"""
        if not hasattr(self, 'nombres_jugadores'):
            self.nombres_jugadores = []
        # Incluir el host como primer jugador
        nombres = [getattr(self, 'nombre_jugador_wifi', None) or getattr(self, 'nombre_jugador_bluetooth', None) or 'Host']
        nombres += self.nombres_jugadores
        if hasattr(self.ids, 'players_list'):
            self.ids.players_list.clear_widgets()
            for i, nombre in enumerate(nombres, 1):
                label = MDLabel(
                    text=f"Jugador {i}: {nombre}",
                    theme_text_color="Custom",
                    text_color=(1, 1, 1, 1)
                )
                self.ids.players_list.add_widget(label)
        # Actualizar contador
        if hasattr(self.ids, 'players_count_label'):
            self.ids.players_count_label.text = f"Jugadores conectados: {len(nombres)}/10" 

    def asignar_cartones_y_enviar_wifi(self, cartones, preguntas_globales):
        """Asigna el cartón correcto a cada jugador por nombre y lo envía por su socket."""
        # El host es el primer cartón
        if not hasattr(self, 'connected_players'):
            print("No hay jugadores conectados para asignar cartones.")
            return
        for idx, (client, nombre) in enumerate(self.connected_players, 1):
            try:
                data = {
                    'carton': cartones[idx],
                    'preguntas_globales': preguntas_globales
                }
                client.send(json.dumps(data).encode('utf-8'))
                print(f"[DEBUG] Cartón enviado a {nombre}")
            except Exception as e:
                print(f"[ERROR] No se pudo enviar cartón a {nombre}: {e}") 

    def seleccionar_modo(self, modo):
        self.modo_seleccionado = modo
        print(f"[DEBUG] Modo multijugador seleccionado: {modo}")
        if hasattr(self, 'ids'):
            if modo == 'wifi':
                self.ids.wifi_options.opacity = 1
                self.ids.wifi_options.disabled = False
                self.ids.bluetooth_options.opacity = 0
                self.ids.bluetooth_options.disabled = True
            elif modo == 'bluetooth':
                self.ids.wifi_options.opacity = 0
                self.ids.wifi_options.disabled = True
                self.ids.bluetooth_options.opacity = 1
                self.ids.bluetooth_options.disabled = False 