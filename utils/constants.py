"""
Constantes para Bingo Educativo
Centraliza todas las constantes y configuraciones de la aplicación
"""

from enum import Enum
from typing import Dict, List, Tuple

# Configuración de la aplicación
APP_NAME = "Bingo Educativo"
APP_VERSION = "1.0.0"
APP_AUTHOR = "Tu Nombre"

# Configuración de colores (Material Design)
class Colors:
    """Paleta de colores de la aplicación"""
    PRIMARY = (0.2, 0.6, 0.8, 1)      # Azul principal
    SECONDARY = (0.8, 0.2, 0.2, 1)     # Rojo secundario
    SUCCESS = (0.2, 0.8, 0.2, 1)       # Verde éxito
    WARNING = (0.8, 0.6, 0.2, 1)       # Naranja advertencia
    ERROR = (0.8, 0.2, 0.2, 1)         # Rojo error
    INFO = (0.2, 0.6, 0.8, 1)          # Azul información
    
    # Colores de fondo
    BACKGROUND_PRIMARY = (0.1, 0.1, 0.1, 1)    # Fondo principal oscuro
    BACKGROUND_SECONDARY = (0.15, 0.15, 0.15, 1) # Fondo secundario
    BACKGROUND_CARD = (0.2, 0.2, 0.2, 1)       # Fondo de tarjetas
    
    # Colores de texto
    TEXT_PRIMARY = (1, 1, 1, 1)        # Texto principal blanco
    TEXT_SECONDARY = (0.8, 0.8, 0.8, 1) # Texto secundario gris
    TEXT_DISABLED = (0.5, 0.5, 0.5, 1) # Texto deshabilitado


# Configuración de sonidos
class SoundFiles:
    """Archivos de sonido de la aplicación"""
    BINGO = "sounds/bingo.wav"
    CORRECT = "sounds/correct.wav"
    WRONG = "sounds/wrong.wav"
    CLICK = "sounds/click.wav"
    BACKGROUND = "sounds/background.mp3"


# Configuración de imágenes
class ImageFiles:
    """Archivos de imágenes de la aplicación"""
    BACKGROUND_MAIN = "assets/images/fondo_principal.jpg"
    BACKGROUND_WOOD = "assets/images/backgrounds/fondo_madera.jpg"
    LOGO = "assets/proedu.png"
    SPLASH = "assets/proedu.png"


# Configuración del juego
class GameConfig:
    """Configuración del juego"""
    MAX_PLAYERS = 10
    MIN_PLAYERS = 1
    MAX_ROUNDS = 25
    QUESTION_TIME_LIMIT = 30  # segundos
    BINGO_BONUS_POINTS = 50
    CORRECT_ANSWER_POINTS = 10
    CARD_SIZE = 9  # 3x3 cartón
    
    # Categorías disponibles
    CATEGORIES = [
        "animales",
        "deportes", 
        "geografia",
        "historia",
        "literatura",
        "medicina",
        "mujeres",
        "arte",
        "ciencia",
        "matematicas",
        "teologia",
        "transporte",
        "inventos",
        "frases_celebres",
        "monumentos"
    ]
    
    # Dificultades
    DIFFICULTIES = ["facil", "moderado", "dificil"]
    
    # Configuración de IA
    AI_DIFFICULTY_ACCURACY = {
        "facil": 0.6,      # 60% de acierto
        "moderado": 0.75,   # 75% de acierto
        "dificil": 0.9      # 90% de acierto
    }


# Configuración de red
class NetworkConfig:
    """Configuración de red para multijugador"""
    DEFAULT_PORT = 5000
    MAX_CONNECTIONS = 10
    TIMEOUT = 30  # segundos
    BUFFER_SIZE = 65536
    
    # Tipos de mensajes
    MESSAGE_TYPES = {
        "JOIN_GAME": "join_game",
        "LEAVE_GAME": "leave_game",
        "START_GAME": "start_game",
        "END_GAME": "end_game",
        "QUESTION": "question",
        "ANSWER": "answer",
        "BINGO": "bingo",
        "CHAT": "chat"
    }


# Configuración de base de datos
class DatabaseConfig:
    """Configuración de base de datos"""
    SQLITE_DB = "bingo_quiz.db"
    MONGODB_URI = "mongodb://localhost:27017"
    MONGODB_DB = "bingo_educativo"
    
    # Colecciones
    COLLECTIONS = {
        "questions": "questions",
        "games": "games",
        "players": "players",
        "statistics": "statistics"
    }


# Configuración de UI
class UIConfig:
    """Configuración de la interfaz de usuario"""
    # Tamaños de fuente
    FONT_SIZES = {
        "small": "12sp",
        "medium": "16sp", 
        "large": "20sp",
        "xlarge": "24sp",
        "title": "32sp",
        "heading": "28sp"
    }
    
    # Espaciado
    SPACING = {
        "xs": "4dp",
        "sm": "8dp",
        "md": "16dp",
        "lg": "24dp",
        "xl": "32dp"
    }
    
    # Padding
    PADDING = {
        "xs": "4dp",
        "sm": "8dp", 
        "md": "16dp",
        "lg": "24dp",
        "xl": "32dp"
    }
    
    # Alturas de botones
    BUTTON_HEIGHTS = {
        "small": "32dp",
        "medium": "48dp",
        "large": "56dp"
    }


# Configuración de animaciones
class AnimationConfig:
    """Configuración de animaciones"""
    DURATIONS = {
        "fast": 0.2,
        "normal": 0.3,
        "slow": 0.5,
        "very_slow": 1.0
    }
    
    EASINGS = {
        "linear": "linear",
        "ease_in": "ease_in",
        "ease_out": "ease_out",
        "ease_in_out": "ease_in_out",
        "bounce": "bounce"
    }


# Configuración de textos
class TextConfig:
    """Textos de la aplicación"""
    # Títulos de pantallas
    SCREEN_TITLES = {
        "main": "BINGO CULTURAL",
        "game": "JUEGO EN CURSO",
        "settings": "CONFIGURACIÓN",
        "multiplayer": "MULTIJUGADOR",
        "instructions": "INSTRUCCIONES"
    }
    
    # Mensajes de error
    ERROR_MESSAGES = {
        "network_error": "Error de conexión. Verifica tu conexión a internet.",
        "database_error": "Error de base de datos. Reinicia la aplicación.",
        "game_error": "Error en el juego. Intenta de nuevo.",
        "invalid_input": "Entrada inválida. Verifica los datos ingresados.",
        "timeout": "Tiempo de espera agotado. Intenta de nuevo."
    }
    
    # Mensajes de éxito
    SUCCESS_MESSAGES = {
        "game_saved": "Juego guardado exitosamente.",
        "settings_saved": "Configuración guardada.",
        "connection_success": "Conexión establecida.",
        "bingo": "¡BINGO! ¡Felicidades!"
    }
    
    # Instrucciones
    INSTRUCTIONS = {
        "main": "Selecciona una opción para comenzar",
        "game": "Responde las preguntas para marcar tu cartón",
        "multiplayer": "Conecta con otros jugadores para jugar en equipo",
        "settings": "Personaliza tu experiencia de juego"
    }


# Configuración de rutas de archivos
class FilePaths:
    """Rutas de archivos importantes"""
    # Directorios principales
    ASSETS_DIR = "assets"
    SOUNDS_DIR = "sounds"
    IMAGES_DIR = "assets/images"
    CARDS_DIR = "cartones"
    DATA_DIR = "data"
    
    # Archivos de configuración
    CONFIG_FILE = "config.json"
    SETTINGS_FILE = "settings.json"
    STATISTICS_FILE = "statistics.json"
    
    # Archivos de datos
    QUESTIONS_FILE = "preguntas.json"
    CARDS_DATA_DIR = "cartones"
    
    # Archivos de build
    BUILD_FILE = "buildozer.spec"
    REQUIREMENTS_FILE = "requirements.txt"
    README_FILE = "README.md"


# Configuración de desarrollo
class DevConfig:
    """Configuración para desarrollo"""
    DEBUG = True
    LOG_LEVEL = "INFO"
    AUTO_SAVE = True
    AUTO_SAVE_INTERVAL = 300  # 5 minutos
    
    # Configuración de testing
    TEST_MODE = False
    MOCK_DATA = False
    
    # Configuración de performance
    ENABLE_PROFILING = False
    ENABLE_MEMORY_MONITORING = False


# Configuración de plataforma
class PlatformConfig:
    """Configuración específica de plataforma"""
    # Android
    ANDROID = {
        "api_level": 34,
        "min_api": 24,
        "archs": ["arm64-v8a", "armeabi-v7a"],
        "permissions": [
            "INTERNET",
            "BLUETOOTH", 
            "BLUETOOTH_ADMIN",
            "BLUETOOTH_CONNECT",
            "BLUETOOTH_SCAN"
        ]
    }
    
    # iOS
    IOS = {
        "deployment_target": "12.0",
        "archs": ["arm64", "x86_64"]
    }
    
    # Windows
    WINDOWS = {
        "python_version": "3.8",
        "archs": ["x64"]
    }


# Configuración de analytics
class AnalyticsConfig:
    """Configuración de analytics"""
    ENABLED = False
    TRACK_EVENTS = [
        "game_started",
        "game_finished", 
        "question_answered",
        "bingo_achieved",
        "error_occurred"
    ]


# Exportar todas las configuraciones
__all__ = [
    'Colors',
    'SoundFiles', 
    'ImageFiles',
    'GameConfig',
    'NetworkConfig',
    'DatabaseConfig',
    'UIConfig',
    'AnimationConfig',
    'TextConfig',
    'FilePaths',
    'DevConfig',
    'PlatformConfig',
    'AnalyticsConfig'
] 