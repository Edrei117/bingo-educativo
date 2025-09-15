from kivymd.app import MDApp
from kivymd.uix.screen import MDScreen
from kivymd.uix.button import MDRaisedButton
from kivymd.uix.label import MDLabel
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.gridlayout import MDGridLayout
from kivymd.uix.card import MDCard
from kivymd.uix.dialog import MDDialog
from kivy.clock import Clock
from kivy.animation import Animation
# from models.bingo_game import BingoGame # Uncomment if needed
from models.game import Game # Keep if Game class is used elsewhere in this file
from main import BingoApp # Keep if BingoApp class is used for type checking
from typing import Dict, Any, Optional, List
from kivy.metrics import sp, dp

class GameScreen(MDScreen):
    dialog: Optional[MDDialog] = None
    app: Optional[BingoApp] = None
    pregunta_actual: Optional[Dict[str, Any]] = None
    current_carton_id: Optional[str] = None
    current_pregunta_id: Optional[str] = None

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        print("GameScreen: Inicializando")
        # Obtener la instancia de la aplicación al inicializar
        self.app = MDApp.get_running_app()
        if not isinstance(self.app, BingoApp):
            print("ERROR: La aplicación no es una instancia de BingoApp")
            self.app = None
        else:
            print("GameScreen: Aplicación inicializada correctamente")
            
    def show_win_dialog(self):
        if isinstance(self.app, BingoApp):
            if self.app.sounds and self.app.sounds.get('bingo'):
                self.app.sounds['bingo'].play()
            self.mostrar_dialogo(
                "¡Bingo!",
                "¡Felicidades! Has ganado el juego.",
            buttons=[
                MDRaisedButton(
                    text="Nuevo Juego",
                    on_release=self.start_new_game
                ),
                MDRaisedButton(
                    text="Salir",
                    on_release=self.go_home
                )
            ]
        )
        
    def start_new_game(self, *args):
        """Inicia un nuevo juego"""
        if self.app:
            self.app.game_in_progress = False
            self.clear_question_area()
            # Usar la nueva función de transición
            self.app.cambiar_pantalla('main', 'right')
            
    def go_home(self, *args):
        """Regresa a la pantalla principal"""
        if self.app:
            self.app.game_in_progress = False
            self.clear_question_area()
        self.app.cambiar_pantalla('main', 'right')
            
    def on_enter(self):
        """Se llama cuando la pantalla se activa."""
        print("GameScreen: on_enter - Iniciando pantalla de juego.")
        # Obtener la referencia a la aplicación si no existe
        if not self.app:
            self.app = MDApp.get_running_app()
            if not isinstance(self.app, BingoApp):
                print("ERROR: No se pudo obtener una referencia válida a BingoApp en on_enter")
                return
            print("GameScreen: Referencia a la aplicación obtenida en on_enter")
        
        # Asegurarse de que el cartón del jugador se muestre desde el inicio
        self.mostrar_cartones()
        print("GameScreen: Cartón del jugador mostrado al entrar.")

    def mostrar_cartones(self, update_ia_only: bool = False):
        """Actualiza la visualización del cartón del jugador"""
        print("GameScreen: Iniciando mostrar_cartones")
        
        if not self.app:
            print("GameScreen: No hay referencia a la aplicación")
            return

        # Solo actualizar el cartón del jugador
        if hasattr(self.ids, 'player_card_grid'):
            self.ids.player_card_grid.clear_widgets()
            print("GameScreen: Grid del cartón del jugador limpiado")

            # Mostrar cartón del jugador
            if self.app.cartones_jugador:
                carton_jugador = self.app.cartones_jugador[0]
                if isinstance(carton_jugador, Dict):
                    preguntas_jugador = carton_jugador.get('preguntas', [])
                    print(f"GameScreen: Poblando cartón del jugador con {len(preguntas_jugador)} preguntas")
                    self._populate_card_grid(self.ids.player_card_grid, preguntas_jugador)
                else:
                    print("GameScreen: Cartón del jugador no es un diccionario válido")
            else:
                print("GameScreen: No hay cartones del jugador o no se encontró el grid")

    def _populate_card_grid(self, grid_widget, preguntas: List[Dict[str, Any]], is_ia: bool = False):
        """Ayuda a poblar una cuadrícula de cartón con botones de preguntas"""
        if not grid_widget or not isinstance(preguntas, list):
            return

        # Asegurar que las preguntas estén ordenadas por su posición en el cartón si tienen un índice
        # O simplemente usar el orden en que aparecen en la lista si no hay índice explícito
        # Asumimos que la lista de preguntas ya está en el orden correcto (1 a 8)
        
        for i, pregunta in enumerate(preguntas):
            if isinstance(pregunta, Dict):
                # Usar el número de pregunta (i+1) como texto del botón
                btn_text = str(i + 1)
                bg_color = (0.2, 0.2, 0.2, 1) # Color por defecto (no respondida)
                text_color = (1, 1, 1, 1)

                if pregunta.get('respondida'):
                    if pregunta.get('correcta'):
                        bg_color = (0.2, 0.8, 0.2, 1) # Verde para correcta
                    else:
                        bg_color = (0.8, 0.2, 0.2, 1) # Rojo para incorrecta

                btn = MDRaisedButton(
                    text=btn_text,
                    md_bg_color=bg_color,
                    theme_text_color="Custom",
                    text_color=text_color,
                    size_hint=(1, 1),
                    font_size='22sp',
                    font_style='Button'
                )
                grid_widget.add_widget(btn)

    def set_pregunta(self, texto):
        label = self.ids.question_text
        
        # Configurar el texto
        label.text = texto
        
        # Ajustar tamaño de fuente basado en la longitud
        length = len(texto)
        if length < 80:
            label.font_size = sp(18)
        elif length < 120:
            label.font_size = sp(16)
        else:
            label.font_size = sp(14)
        
        # Configurar text_size para ajuste automático
        label.text_size = (self.width * 0.8, None)
        
        print(f"GameScreen: Pregunta configurada - Longitud: {length}, Font: {label.font_size}")

    def mostrar_pregunta_en_ui(self, pregunta_data: Dict[str, Any]):
        """Muestra una pregunta en la interfaz (categoría, pregunta, opciones) si está en el cartón del jugador."""
        print(f"GameScreen: Mostrando pregunta: {pregunta_data.get('pregunta', '')}")
        
        # Verificar que tenemos una referencia válida a la app
        if not self.app:
            self.app = MDApp.get_running_app()
            if not isinstance(self.app, BingoApp):
                print("ERROR: No se pudo obtener una referencia válida a BingoApp")
                return

        if not isinstance(pregunta_data, Dict) or not hasattr(self, 'ids'):
            print("GameScreen: Datos de pregunta inválidos o ids faltan.")
            return

        # Actualizar el texto de la pregunta con ajuste de tamaño
        if hasattr(self.ids, 'question_text'):
            self.set_pregunta(pregunta_data.get('pregunta', ''))
            print("GameScreen: Texto de la pregunta actualizado y font_size ajustado")

        # Verificar si la pregunta está en el cartón del jugador
        pregunta_en_carton_jugador = None
        if self.app.cartones_jugador:
            player_carton = self.app.cartones_jugador[0]
            if isinstance(player_carton, Dict):
                pregunta_en_carton_jugador = next((p for p in player_carton.get('preguntas', []) or [] 
                                                 if isinstance(p, Dict) and p.get('id') == pregunta_data.get('id')), None)

        # Limpiar opciones anteriores
        if hasattr(self.ids, 'options_container'):
            self.ids.options_container.clear_widgets()
            print("GameScreen: Contenedor de opciones limpiado")
            
            # Solo mostrar opciones si la pregunta está en el cartón del jugador
            if pregunta_en_carton_jugador:
                opciones = pregunta_data.get('opciones', [])
                if isinstance(opciones, list):
                    print(f"GameScreen: Agregando {len(opciones)} opciones")
                    for i, opcion in enumerate(opciones):
                        btn = MDRaisedButton(
                            text=opcion,
                            size_hint_x=1,
                            size_hint_y=None,
                            height='40dp',
                            md_bg_color=(0.3, 0.3, 0.3, 1),
                            text_color=(1, 1, 1, 1),
                            font_style='Button',
                            on_release=lambda x, idx=i: self.app.process_player_answer(pregunta_data, idx) if self.app else None
                        )
                        self.ids.options_container.add_widget(btn)
                        print(f"GameScreen: Opción {i+1} agregada: {opcion}")
            else:
                print("GameScreen: La pregunta no está en el cartón del jugador")
                if hasattr(self.ids, 'game_messages'):
                    self.ids.game_messages.text = "Esta pregunta no está en tu cartón"

    def clear_question_area(self):
        """Limpia el área de preguntas y opciones"""
        if hasattr(self, 'ids'):
            # Limpiar texto de pregunta y opciones.
            if hasattr(self.ids, 'question_text'):
                 self.ids.question_text.text = ""
            if hasattr(self.ids, 'options_container'):
                 self.ids.options_container.clear_widgets()
            # La categoría se queda fija, no se limpia aquí.
            # if hasattr(self.ids, 'current_category'):
            #      self.ids.current_category.text = "Categoría:"

    def mostrar_dialogo(self, titulo: str, mensaje: str, buttons: Optional[List[MDRaisedButton]] = None):
        """Muestra un diálogo con el mensaje especificado"""
        if self.dialog:
            self.dialog.dismiss()
            self.dialog = None
        
        self.dialog = MDDialog(
            title=titulo,
            text=mensaje,
            buttons=buttons or [
                MDRaisedButton(
                    text="OK",
                    on_release=lambda x: self.dialog.dismiss() if self.dialog else None
                )
            ]
        )
        if self.dialog:
            self.dialog.open()

    def animar_bingo(self, carton: Dict[str, Any]) -> None:
        """Anima el cartón cuando hay bingo"""
        # Create individual animations
        flash_in = Animation(md_bg_color=(0, 1, 0, 0.5), duration=0.5)
        flash_out = Animation(md_bg_color=(240/255, 240/255, 240/255, 1), duration=0.5)
        # Chain animations to create a sequence and repeat
        anim = flash_in + flash_out
        anim.repeat = True # Repeat indefinitely while animation is running
        # Repeating 3 times: flash_in + flash_out + flash_in + flash_out + flash_in + flash_out
        anim = flash_in + flash_out + flash_in + flash_out + flash_in + flash_out

        # Referenciar la cuadrícula del cartón del jugador usando self.ids
        if hasattr(self.ids, 'player_card_grid'):
            anim.start(self.ids.player_card_grid)

    def mostrar_carton_ia_bingo(self, ia_carton: Dict[str, Any]):
        """Muestra el cartón de una IA en la interfaz cuando hace bingo."""
        if not isinstance(ia_carton, Dict) or not hasattr(self.ids, 'ai_cards_container'):
            print("Error: Datos de cartón de IA inválidos o contenedor no encontrado.")
            return

        # Crear un nuevo MDCard para el cartón de la IA
        ai_card = MDCard(
            orientation='vertical',
            size_hint_y=None,
            height="200dp", # Altura fija o ajustarla según diseño
            padding='5dp',
            spacing='5dp',
            elevation=4 # Opcional: añadir elevación para resaltarlo
        )

        # Añadir un label para identificar a la IA (ej. por categoría o número)
        ia_name = ia_carton.get('categoria', f'IA {len(self.ids.ai_cards_container.children) + 1}').capitalize()
        ai_card_label = MDLabel(
            text=f"Cartón de la {ia_name}",
            halign='center',
            size_hint_y=None,
            height='30dp'
        )
        ai_card.add_widget(ai_card_label)

        # Crear la cuadrícula para los números del cartón de la IA
        ai_card_grid = MDGridLayout(
            cols=4,
            spacing='5dp',
            size_hint_y=1 # Permite que la cuadrícula llene el espacio restante de la tarjeta
        )
        ai_card.add_widget(ai_card_grid)

        # Poblar la cuadrícula con los números de la IA (marcados si están correctos)
        preguntas_ia = ia_carton.get('preguntas', [])
        if isinstance(preguntas_ia, list):
            self._populate_card_grid(ai_card_grid, preguntas_ia, is_ia=True)

        # Añadir el cartón de la IA al contenedor en la UI
        self.ids.ai_cards_container.add_widget(ai_card)
        # Asegurar que el contenedor de IAs ocupe espacio una vez que tiene contenido
        self.ids.ai_cards_container.size_hint_y = None # Ocupa el espacio necesario
        self.ids.ai_cards_container.height = "250dp" # Altura de ejemplo, ajustar si es necesario

    def verificar_bingo_manual(self):
        """Verifica manualmente si el cartón del jugador está completo y termina el juego si es así."""
        if not self.app or not self.app.cartones_jugador:
            self.mostrar_dialogo("Error", "No se encontró el cartón del jugador.")
            return
        carton_jugador = self.app.cartones_jugador[0]
        if self.app.verificar_bingo(carton_jugador):
            # Terminar el juego y mostrar estadísticas con opciones
            self.app.terminar_juego(winner="player")
        else:
            self.mostrar_dialogo("No hay Bingo", "Aún no has completado todas las preguntas correctamente.")

    def update_timer_label(self, seconds_left: int):
        """Actualiza el contador visual de tiempo en la UI."""
        if hasattr(self.ids, 'timer_label'):
            if seconds_left > 0:
                self.ids.timer_label.text = f"⏰ {seconds_left} s"
            else:
                self.ids.timer_label.text = ""

# Keep MainScreen and GameScreen classes as they define the UI structure based on the .kv file 