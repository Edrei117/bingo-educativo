"""
Utilidades para manejo de pantallas y configuraciones de imagen
"""
from kivy.metrics import dp, sp
from kivy.utils import platform
from kivy.core.window import Window
from typing import Tuple, Optional

class ScreenUtils:
    """Clase para manejar configuraciones de pantalla y densidad"""
    
    @staticmethod
    def get_screen_density() -> float:
        """Obtiene la densidad de pantalla del dispositivo"""
        try:
            if platform == 'android':
                from jnius import autoclass
                activity = autoclass('org.kivy.android.PythonActivity').mActivity
                display_metrics = activity.getResources().getDisplayMetrics()
                return display_metrics.density
            else:
                # Para desarrollo en PC, usar densidad estándar
                return 1.0
        except Exception as e:
            print(f"[WARNING] No se pudo obtener densidad de pantalla: {e}")
            return 1.0
    
    @staticmethod
    def get_screen_size() -> Tuple[int, int]:
        """Obtiene el tamaño de la pantalla"""
        return Window.size
    
    @staticmethod
    def get_screen_orientation() -> str:
        """Obtiene la orientación de la pantalla"""
        width, height = Window.size
        return 'portrait' if height > width else 'landscape'
    
    @staticmethod
    def adjust_size_for_density(size: float, use_sp: bool = False) -> float:
        """Ajusta el tamaño según la densidad de pantalla"""
        density = ScreenUtils.get_screen_density()
        if use_sp:
            return sp(size * density)
        else:
            return dp(size * density)
    
    @staticmethod
    def get_optimal_image_size(base_size: float, max_size: Optional[float] = None) -> float:
        """Calcula el tamaño óptimo para imágenes según la densidad de pantalla"""
        density = ScreenUtils.get_screen_density()
        optimal_size = base_size * density
        
        if max_size is not None and optimal_size > max_size:
            return max_size
        
        return optimal_size
    
    @staticmethod
    def configure_window_for_device():
        """Configura la ventana para diferentes dispositivos"""
        try:
            # Configurar tamaño mínimo para evitar problemas en pantallas pequeñas
            Window.minimum_width = 320
            Window.minimum_height = 480
            
            # Configurar para diferentes orientaciones
            Window.softinput_mode = 'below_target'
            
            # Configurar para pantallas de alta densidad
            density = ScreenUtils.get_screen_density()
            if density > 2.0:
                # Pantalla de alta densidad, ajustar configuraciones
                print(f"[DEBUG] Pantalla de alta densidad detectada: {density}")
            
        except Exception as e:
            print(f"[WARNING] Error al configurar ventana: {e}")

class ImageConfig:
    """Clase para configuraciones específicas de imágenes"""
    
    @staticmethod
    def get_image_properties() -> dict:
        """Retorna propiedades recomendadas para imágenes"""
        return {
            'allow_stretch': True,
            'keep_ratio': True,
            'fit_mode': 'contain'
        }
    
    @staticmethod
    def get_background_properties() -> dict:
        """Retorna propiedades recomendadas para imágenes de fondo"""
        return {
            'allow_stretch': True,
            'keep_ratio': False,  # Para fondos, permitir estiramiento
            'fit_mode': 'cover'
        }
    
    @staticmethod
    def get_logo_properties() -> dict:
        """Retorna propiedades recomendadas para logos"""
        return {
            'allow_stretch': True,
            'keep_ratio': True,
            'fit_mode': 'contain'
        } 