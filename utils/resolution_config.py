"""
Configuraciones para diferentes resoluciones de pantalla
"""
from typing import Dict, Any, Tuple
from kivy.metrics import dp, sp

class ResolutionConfig:
    """Configuraciones específicas para diferentes resoluciones de pantalla"""
    
    # Configuraciones para diferentes densidades de pantalla
    DENSITY_CONFIGS = {
        'ldpi': {
            'scale_factor': 0.75,
            'font_scale': 0.8,
            'padding_scale': 0.8,
            'button_height': 40,
            'card_padding': 8
        },
        'mdpi': {
            'scale_factor': 1.0,
            'font_scale': 1.0,
            'padding_scale': 1.0,
            'button_height': 48,
            'card_padding': 12
        },
        'hdpi': {
            'scale_factor': 1.5,
            'font_scale': 1.1,
            'padding_scale': 1.1,
            'button_height': 56,
            'card_padding': 16
        },
        'xhdpi': {
            'scale_factor': 2.0,
            'font_scale': 1.2,
            'padding_scale': 1.2,
            'button_height': 64,
            'card_padding': 20
        },
        'xxhdpi': {
            'scale_factor': 3.0,
            'font_scale': 1.3,
            'padding_scale': 1.3,
            'button_height': 72,
            'card_padding': 24
        }
    }
    
    @staticmethod
    def get_density_category(density: float) -> str:
        """Determina la categoría de densidad basada en el valor de densidad"""
        if density < 0.75:
            return 'ldpi'
        elif density < 1.0:
            return 'mdpi'
        elif density < 1.5:
            return 'hdpi'
        elif density < 2.0:
            return 'xhdpi'
        else:
            return 'xxhdpi'
    
    @staticmethod
    def get_config_for_density(density: float) -> Dict[str, Any]:
        """Obtiene la configuración para una densidad específica"""
        category = ResolutionConfig.get_density_category(density)
        return ResolutionConfig.DENSITY_CONFIGS.get(category, ResolutionConfig.DENSITY_CONFIGS['mdpi'])
    
    @staticmethod
    def get_scaled_size(base_size: float, density: float, use_sp: bool = False) -> float:
        """Calcula el tamaño escalado para una densidad específica"""
        config = ResolutionConfig.get_config_for_density(density)
        scale_factor = config['scale_factor']
        
        if use_sp:
            return sp(base_size * scale_factor)
        else:
            return dp(base_size * scale_factor)
    
    @staticmethod
    def get_image_config_for_density(density: float) -> Dict[str, Any]:
        """Obtiene configuración específica para imágenes según la densidad"""
        config = ResolutionConfig.get_config_for_density(density)
        
        return {
            'allow_stretch': True,
            'keep_ratio': True,
            'fit_mode': 'contain',
            'scale_factor': config['scale_factor']
        }

class LayoutConfig:
    """Configuraciones específicas para layouts"""
    
    @staticmethod
    def get_button_config(density: float) -> Dict[str, Any]:
        """Configuración para botones según la densidad"""
        config = ResolutionConfig.get_config_for_density(density)
        
        return {
            'height': dp(config['button_height']),
            'padding': dp(config['card_padding']),
            'font_size': sp(18 * config['font_scale'])
        }
    
    @staticmethod
    def get_card_config(density: float) -> Dict[str, Any]:
        """Configuración para tarjetas según la densidad"""
        config = ResolutionConfig.get_config_for_density(density)
        
        return {
            'padding': dp(config['card_padding']),
            'spacing': dp(config['card_padding'] * 0.5),
            'elevation': 2
        }
    
    @staticmethod
    def get_text_config(density: float, text_type: str = 'normal') -> Dict[str, Any]:
        """Configuración para texto según la densidad y tipo"""
        config = ResolutionConfig.get_config_for_density(density)
        
        base_sizes = {
            'small': 12,
            'normal': 16,
            'large': 20,
            'title': 24,
            'heading': 28
        }
        
        return {
            'font_size': sp(base_sizes.get(text_type, 16) * config['font_scale'])
        } 