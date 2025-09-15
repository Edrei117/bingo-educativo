"""
Utilidades para el manejo de imágenes de fondo
"""
from kivy.uix.image import Image
from kivy.properties import NumericProperty, BooleanProperty
from kivy.metrics import dp
from typing import Tuple, Optional

class BackgroundImage(Image):
    """
    Widget de imagen de fondo optimizado para diferentes densidades de pantalla
    """
    
    # Propiedades configurables
    stretch_mode = NumericProperty(0)  # 0: none, 1: stretch, 2: keep_ratio
    opacity_level = NumericProperty(1.0)
    blur_radius = NumericProperty(0)
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        
        # Configuración por defecto para imágenes de fondo
        self.allow_stretch = True
        self.keep_ratio = False
        self.opacity = self.opacity_level
        
        # Configurar según el modo de estiramiento
        self._update_stretch_mode()
    
    def _update_stretch_mode(self):
        """Actualiza el modo de estiramiento según la propiedad"""
        if self.stretch_mode == 0:
            self.allow_stretch = False
            self.keep_ratio = True
        elif self.stretch_mode == 1:
            self.allow_stretch = True
            self.keep_ratio = False
        elif self.stretch_mode == 2:
            self.allow_stretch = True
            self.keep_ratio = True
    
    def on_stretch_mode(self, instance, value):
        """Se llama cuando cambia el modo de estiramiento"""
        self._update_stretch_mode()
    
    def on_opacity_level(self, instance, value):
        """Se llama cuando cambia el nivel de opacidad"""
        self.opacity = value

class ResponsiveImage(Image):
    """
    Widget de imagen responsiva que se adapta a diferentes tamaños de pantalla
    """
    
    # Propiedades para configuración responsiva
    min_width = NumericProperty(100)
    min_height = NumericProperty(100)
    max_width = NumericProperty(800)
    max_height = NumericProperty(600)
    aspect_ratio = NumericProperty(1.0)
    maintain_aspect = BooleanProperty(True)
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        
        # Configuración por defecto
        self.allow_stretch = True
        self.keep_ratio = self.maintain_aspect
        
        # Bind para cambios en propiedades
        self.bind(
            maintain_aspect=self._on_maintain_aspect,
            size=self._on_size_change
        )
    
    def _on_maintain_aspect(self, instance, value):
        """Se llama cuando cambia la propiedad maintain_aspect"""
        self.keep_ratio = value
    
    def _on_size_change(self, instance, value):
        """Se llama cuando cambia el tamaño"""
        if self.maintain_aspect:
            self._adjust_size_for_aspect()
    
    def _adjust_size_for_aspect(self):
        """Ajusta el tamaño para mantener la proporción"""
        width, height = self.size
        
        # Calcular nuevo tamaño manteniendo proporción
        if width / height > self.aspect_ratio:
            # Demasiado ancho, ajustar altura
            new_height = width / self.aspect_ratio
            if new_height <= self.max_height:
                self.size = (width, new_height)
        else:
            # Demasiado alto, ajustar ancho
            new_width = height * self.aspect_ratio
            if new_width <= self.max_width:
                self.size = (new_width, height)

def create_background_image(source: str, 
                          stretch_mode: int = 1, 
                          opacity: float = 1.0,
                          **kwargs) -> BackgroundImage:
    """
    Crea una imagen de fondo con configuración optimizada
    
    Args:
        source: Ruta de la imagen
        stretch_mode: 0=none, 1=stretch, 2=keep_ratio
        opacity: Nivel de opacidad (0.0 a 1.0)
        **kwargs: Propiedades adicionales
    
    Returns:
        BackgroundImage configurada
    """
    return BackgroundImage(
        source=source,
        stretch_mode=stretch_mode,
        opacity_level=opacity,
        **kwargs
    )

def create_responsive_image(source: str,
                          aspect_ratio: float = 1.0,
                          maintain_aspect: bool = True,
                          **kwargs) -> ResponsiveImage:
    """
    Crea una imagen responsiva
    
    Args:
        source: Ruta de la imagen
        aspect_ratio: Proporción de aspecto (ancho/alto)
        maintain_aspect: Si mantener la proporción
        **kwargs: Propiedades adicionales
    
    Returns:
        ResponsiveImage configurada
    """
    return ResponsiveImage(
        source=source,
        aspect_ratio=aspect_ratio,
        maintain_aspect=maintain_aspect,
        **kwargs
    )

def get_optimal_image_size(original_size: Tuple[int, int],
                          container_size: Tuple[int, int],
                          mode: str = 'fit') -> Tuple[int, int]:
    """
    Calcula el tamaño óptimo para una imagen
    
    Args:
        original_size: Tamaño original de la imagen (ancho, alto)
        container_size: Tamaño del contenedor (ancho, alto)
        mode: 'fit', 'fill', 'stretch'
    
    Returns:
        Tamaño óptimo (ancho, alto)
    """
    orig_width, orig_height = original_size
    cont_width, cont_height = container_size
    
    if mode == 'fit':
        # Mantener proporción, ajustar para que quepa
        scale_x = cont_width / orig_width
        scale_y = cont_height / orig_height
        scale = min(scale_x, scale_y)
        
        return (int(orig_width * scale), int(orig_height * scale))
    
    elif mode == 'fill':
        # Mantener proporción, llenar todo el contenedor
        scale_x = cont_width / orig_width
        scale_y = cont_height / orig_height
        scale = max(scale_x, scale_y)
        
        return (int(orig_width * scale), int(orig_height * scale))
    
    else:  # stretch
        # Estirar para llenar exactamente
        return container_size 