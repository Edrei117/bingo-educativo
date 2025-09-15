"""
Utilidades para mejorar la interfaz de usuario
"""
from kivy.animation import Animation
from kivy.clock import Clock
from kivy.metrics import dp
from kivy.properties import NumericProperty, BooleanProperty
from kivy.uix.widget import Widget
from kivymd.uix.card import MDCard
from kivymd.uix.button import MDRaisedButton
from kivymd.uix.label import MDLabel
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.dialog import MDDialog
from kivymd.uix.snackbar import Snackbar
from typing import Callable, Optional

class AnimatedCard(MDCard):
    """Card con animaciones"""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.scale = NumericProperty(1.0)
        self.opacity = NumericProperty(1.0)
    
    def animate_in(self, delay: float = 0.0):
        """Anima la entrada del card"""
        self.scale = 0.0
        self.opacity = 0.0
        
        anim = Animation(
            scale=1.0, 
            opacity=1.0, 
            duration=0.3, 
            transition='out_back'
        )
        
        if delay > 0:
            Clock.schedule_once(lambda dt: anim.start(self), delay)
        else:
            anim.start(self)
    
    def animate_out(self, callback: Optional[Callable] = None):
        """Anima la salida del card"""
        anim = Animation(
            scale=0.0, 
            opacity=0.0, 
            duration=0.2, 
            transition='in_back'
        )
        
        if callback:
            anim.bind(on_complete=lambda *args: callback())
        
        anim.start(self)

class PulseButton(MDRaisedButton):
    """Botón con efecto de pulso"""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.scale = NumericProperty(1.0)
    
    def on_press(self):
        """Efecto de pulso al presionar"""
        anim = Animation(scale=0.95, duration=0.1) + Animation(scale=1.0, duration=0.1)
        anim.start(self)
        super().on_press()

class FadeLabel(MDLabel):
    """Label con efecto de fade"""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.opacity = NumericProperty(0.0)
    
    def fade_in(self, duration: float = 0.5):
        """Anima la aparición del texto"""
        anim = Animation(opacity=1.0, duration=duration)
        anim.start(self)
    
    def fade_out(self, duration: float = 0.3):
        """Anima la desaparición del texto"""
        anim = Animation(opacity=0.0, duration=duration)
        anim.start(self)

class NotificationManager:
    """Gestor de notificaciones y mensajes"""
    
    @staticmethod
    def show_success_message(text: str, duration: float = 3.0):
        """Muestra un mensaje de éxito"""
        snackbar = Snackbar(
            text=text,
            duration=duration,
            bg_color=(0.2, 0.8, 0.2, 1.0)  # Verde
        )
        snackbar.open()
    
    @staticmethod
    def show_error_message(text: str, duration: float = 4.0):
        """Muestra un mensaje de error"""
        snackbar = Snackbar(
            text=text,
            duration=duration,
            bg_color=(0.8, 0.2, 0.2, 1.0)  # Rojo
        )
        snackbar.open()
    
    @staticmethod
    def show_info_message(text: str, duration: float = 3.0):
        """Muestra un mensaje informativo"""
        snackbar = Snackbar(
            text=text,
            duration=duration,
            bg_color=(0.2, 0.6, 0.8, 1.0)  # Azul
        )
        snackbar.open()
    
    @staticmethod
    def show_achievement_dialog(achievement_name: str, points: int):
        """Muestra un diálogo de logro desbloqueado"""
        content = MDBoxLayout(
            orientation='vertical',
            spacing='10dp',
            padding='20dp'
        )
        
        content.add_widget(MDLabel(
            text="🎉 ¡Logro Desbloqueado! 🎉",
            halign="center",
            font_style="H5",
            bold=True
        ))
        
        content.add_widget(MDLabel(
            text=achievement_name,
            halign="center",
            font_style="H6"
        ))
        
        content.add_widget(MDLabel(
            text=f"+{points} puntos",
            halign="center",
            font_style="Body1",
            theme_text_color="Secondary"
        ))
        
        dialog = MDDialog(
            title="",
            type="custom",
            content_cls=content,
            buttons=[
                MDRaisedButton(
                    text="¡Genial!",
                    on_release=lambda x: dialog.dismiss()
                )
            ]
        )
        
        dialog.open()

class LoadingSpinner(Widget):
    """Spinner de carga personalizado"""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.angle = NumericProperty(0)
        self.is_spinning = BooleanProperty(False)
        self._animation = None
    
    def start_spinning(self):
        """Inicia la animación de giro"""
        if not self.is_spinning:
            self.is_spinning = True
            self._animation = Animation(angle=360, duration=1.0)
            self._animation.repeat = True
            self._animation.start(self)
    
    def stop_spinning(self):
        """Detiene la animación de giro"""
        if self.is_spinning:
            self.is_spinning = False
            if self._animation:
                self._animation.cancel(self)

class ConfettiEffect(Widget):
    """Efecto de confeti para celebraciones"""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.particles = []
    
    def create_confetti(self, x: float, y: float, count: int = 20):
        """Crea partículas de confeti"""
        colors = [(1, 0, 0), (0, 1, 0), (0, 0, 1), (1, 1, 0), (1, 0, 1), (0, 1, 1)]
        
        for i in range(count):
            particle = MDBoxLayout(
                size_hint=(None, None),
                size=(dp(8), dp(8)),
                pos=(x, y),
                md_bg_color=colors[i % len(colors)]
            )
            
            self.particles.append(particle)
            self.add_widget(particle)
            
            # Animación de caída
            anim = Animation(
                y=y - dp(200),
                x=x + (i - count/2) * dp(10),
                opacity=0,
                duration=2.0 + i * 0.1,
                transition='out_quad'
            )
            anim.start(particle)
            
            # Remover partícula después de la animación
            Clock.schedule_once(lambda dt, p=particle: self.remove_particle(p), 2.5)
    
    def remove_particle(self, particle):
        """Remueve una partícula"""
        if particle in self.particles:
            self.particles.remove(particle)
            self.remove_widget(particle)

class UIUtils:
    """Utilidades generales para la UI"""
    
    @staticmethod
    def create_gradient_background(color1: tuple, color2: tuple):
        """Crea un fondo con gradiente"""
        # Implementación del gradiente
        pass
    
    @staticmethod
    def add_shadow_to_widget(widget, elevation: float = 8.0):
        """Agrega sombra a un widget"""
        widget.elevation = elevation
    
    @staticmethod
    def create_ripple_effect(widget):
        """Agrega efecto de ondulación"""
        # Implementación del efecto ripple
        pass
    
    @staticmethod
    def animate_number_change(label, start_value: int, end_value: int, duration: float = 1.0):
        """Anima el cambio de un número"""
        def update_number(progress):
            current_value = int(start_value + (end_value - start_value) * progress)
            label.text = str(current_value)
        
        anim = Animation(duration=duration)
        anim.bind(on_progress=update_number)
        anim.start(label)

# Instancias globales
notification_manager = NotificationManager()
ui_utils = UIUtils()
