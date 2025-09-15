"""
Pantalla Base para Bingo Educativo
Proporciona funcionalidades comunes para todas las pantallas
"""

from typing import Optional, Dict, Any, Callable
from kivymd.uix.screen import MDScreen
from kivymd.uix.dialog import MDDialog
from kivymd.uix.button import MDRaisedButton
from kivy.clock import Clock
from kivy.animation import Animation
from kivy.metrics import dp

from core.state_manager import state_manager, GameStatus


class BaseScreen(MDScreen):
    """
    Pantalla base que proporciona funcionalidades comunes
    para todas las pantallas de la aplicación
    """
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.dialog: Optional[MDDialog] = None
        self.animations: Dict[str, Animation] = {}
        self.state_listeners: Dict[str, Callable] = {}
        self._setup_state_listeners()
    
    def _setup_state_listeners(self) -> None:
        """Configura los listeners del estado que necesita esta pantalla"""
        # Cada pantalla puede sobrescribir este método para suscribirse
        # a cambios específicos del estado
        pass
    
    def on_enter(self) -> None:
        """Se llama cuando la pantalla se activa"""
        super().on_enter()
        self._subscribe_to_state()
        self._on_screen_enter()
    
    def on_leave(self) -> None:
        """Se llama cuando la pantalla se desactiva"""
        super().on_leave()
        self._unsubscribe_from_state()
        self._on_screen_leave()
    
    def _subscribe_to_state(self) -> None:
        """Suscribe esta pantalla a cambios del estado"""
        for key, callback in self.state_listeners.items():
            state_manager.subscribe(key, callback)
    
    def _unsubscribe_from_state(self) -> None:
        """Desuscribe esta pantalla de cambios del estado"""
        for key, callback in self.state_listeners.items():
            state_manager.unsubscribe(key, callback)
    
    def _on_screen_enter(self) -> None:
        """Método que las pantallas hijas pueden sobrescribir"""
        pass
    
    def _on_screen_leave(self) -> None:
        """Método que las pantallas hijas pueden sobrescribir"""
        pass
    
    def show_dialog(self, title: str, text: str, buttons: Optional[list] = None) -> None:
        """Muestra un diálogo con el título y texto especificados"""
        if self.dialog:
            self.dialog.dismiss()
        
        if buttons is None:
            buttons = [
                MDRaisedButton(
                    text="OK",
                    on_release=self._dismiss_dialog
                )
            ]
        
        self.dialog = MDDialog(
            title=title,
            text=text,
            buttons=buttons
        )
        self.dialog.open()
    
    def _dismiss_dialog(self, *args) -> None:
        """Cierra el diálogo actual"""
        if self.dialog:
            self.dialog.dismiss()
            self.dialog = None
    
    def show_loading_dialog(self, message: str = "Cargando...") -> None:
        """Muestra un diálogo de carga"""
        self.show_dialog("Cargando", message, [])
    
    def hide_loading_dialog(self) -> None:
        """Oculta el diálogo de carga"""
        if self.dialog:
            self.dialog.dismiss()
            self.dialog = None
    
    def show_error_dialog(self, error_message: str) -> None:
        """Muestra un diálogo de error"""
        self.show_dialog(
            "Error",
            error_message,
            [
                MDRaisedButton(
                    text="OK",
                    on_release=self._dismiss_dialog
                )
            ]
        )
    
    def show_confirmation_dialog(
        self, 
        title: str, 
        message: str, 
        on_confirm: Callable,
        on_cancel: Optional[Callable] = None
    ) -> None:
        """Muestra un diálogo de confirmación"""
        buttons = [
            MDRaisedButton(
                text="Cancelar",
                on_release=lambda x: self._handle_confirmation_cancel(on_cancel)
            ),
            MDRaisedButton(
                text="Confirmar",
                on_release=lambda x: self._handle_confirmation_ok(on_confirm)
            )
        ]
        
        self.show_dialog(title, message, buttons)
    
    def _handle_confirmation_ok(self, callback: Callable) -> None:
        """Maneja la confirmación positiva"""
        self._dismiss_dialog()
        if callback:
            callback()
    
    def _handle_confirmation_cancel(self, callback: Optional[Callable]) -> None:
        """Maneja la cancelación"""
        self._dismiss_dialog()
        if callback:
            callback()
    
    def animate_widget(self, widget, animation_type: str, **kwargs) -> None:
        """Aplica una animación a un widget"""
        if animation_type == "fade_in":
            anim = Animation(opacity=1, duration=kwargs.get('duration', 0.5))
        elif animation_type == "fade_out":
            anim = Animation(opacity=0, duration=kwargs.get('duration', 0.5))
        elif animation_type == "slide_in":
            direction = kwargs.get('direction', 'left')
            if direction == 'left':
                anim = Animation(x=0, duration=kwargs.get('duration', 0.3))
            elif direction == 'right':
                anim = Animation(x=0, duration=kwargs.get('duration', 0.3))
            elif direction == 'up':
                anim = Animation(y=0, duration=kwargs.get('duration', 0.3))
            elif direction == 'down':
                anim = Animation(y=0, duration=kwargs.get('duration', 0.3))
        elif animation_type == "bounce":
            anim = Animation(scale=1.1, duration=0.1) + Animation(scale=1, duration=0.1)
        elif animation_type == "pulse":
            anim = Animation(scale=1.05, duration=0.2) + Animation(scale=1, duration=0.2)
        else:
            return
        
        anim.start(widget)
        self.animations[widget] = anim
    
    def stop_animation(self, widget) -> None:
        """Detiene la animación de un widget"""
        if widget in self.animations:
            self.animations[widget].stop()
            del self.animations[widget]
    
    def schedule_once(self, callback: Callable, delay: float = 0) -> None:
        """Programa una función para ejecutarse después de un delay"""
        Clock.schedule_once(callback, delay)
    
    def schedule_interval(self, callback: Callable, interval: float) -> None:
        """Programa una función para ejecutarse periódicamente"""
        return Clock.schedule_interval(callback, interval)
    
    def unschedule(self, callback: Callable) -> None:
        """Cancela una función programada"""
        Clock.unschedule(callback)
    
    def get_game_status(self) -> GameStatus:
        """Obtiene el estado actual del juego"""
        return state_manager.get_state('status', GameStatus.IDLE)
    
    def is_game_playing(self) -> bool:
        """Verifica si el juego está en curso"""
        return self.get_game_status() == GameStatus.PLAYING
    
    def is_game_paused(self) -> bool:
        """Verifica si el juego está pausado"""
        return self.get_game_status() == GameStatus.PAUSED
    
    def is_game_finished(self) -> bool:
        """Verifica si el juego ha terminado"""
        return self.get_game_status() == GameStatus.FINISHED
    
    def get_current_question(self) -> Optional[Dict[str, Any]]:
        """Obtiene la pregunta actual del juego"""
        return state_manager.get_state('current_question')
    
    def get_players(self) -> list:
        """Obtiene la lista de jugadores"""
        return state_manager.get_state('players', [])
    
    def get_current_player(self) -> Optional[str]:
        """Obtiene el ID del jugador actual"""
        return state_manager.get_state('current_player')
    
    def get_round_number(self) -> int:
        """Obtiene el número de round actual"""
        return state_manager.get_state('round_number', 0)
    
    def get_error_message(self) -> Optional[str]:
        """Obtiene el mensaje de error actual"""
        return state_manager.get_state('error_message')
    
    def clear_error_message(self) -> None:
        """Limpia el mensaje de error"""
        state_manager.set_state('error_message', None)
    
    def navigate_to_screen(self, screen_name: str, direction: str = 'left') -> None:
        """Navega a otra pantalla"""
        if hasattr(self, 'manager') and self.manager:
            self.manager.transition.direction = direction
            self.manager.current = screen_name
    
    def go_back(self) -> None:
        """Regresa a la pantalla anterior"""
        if hasattr(self, 'manager') and self.manager:
            # Implementar lógica de navegación hacia atrás
            # Por ahora, ir a la pantalla principal
            self.navigate_to_screen('main', 'right')
    
    def update_ui(self) -> None:
        """Actualiza la interfaz de usuario"""
        # Las pantallas hijas pueden sobrescribir este método
        pass
    
    def on_state_change(self, key: str, value: Any) -> None:
        """Callback cuando cambia el estado"""
        # Las pantallas hijas pueden sobrescribir este método
        pass 