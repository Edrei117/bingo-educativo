"""
Módulo de optimización de rendimiento para la aplicación de Bingo
"""
import os
from functools import lru_cache
from typing import Dict, Any
from kivy.core.image import Image as CoreImage
from kivy.properties import ObjectProperty
from kivy.cache import Cache

class PerformanceOptimizer:
    """Clase para optimizar el rendimiento de la aplicación"""
    
    def __init__(self):
        self.image_cache = {}
        self.texture_cache = {}
        self._setup_cache()
    
    def _setup_cache(self):
        """Configura el sistema de cache"""
        Cache.register('images', limit=100)
        Cache.register('textures', limit=50)
    
    @lru_cache(maxsize=128)
    def load_image(self, path: str) -> CoreImage:
        """Carga una imagen con cache"""
        if path not in self.image_cache:
            self.image_cache[path] = CoreImage(path)
        return self.image_cache[path]
    
    def preload_assets(self, asset_paths: list):
        """Precarga assets importantes"""
        for path in asset_paths:
            if os.path.exists(path):
                self.load_image(path)
    
    def clear_cache(self):
        """Limpia el cache"""
        self.image_cache.clear()
        self.texture_cache.clear()
        # Limpiar cache de Kivy de forma segura
        try:
            Cache.remove('images')
            Cache.remove('textures')
        except:
            pass
    
    def optimize_memory(self):
        """Optimiza el uso de memoria"""
        # Implementar limpieza de memoria no utilizada
        pass

# Instancia global
optimizer = PerformanceOptimizer()
