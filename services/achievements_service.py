"""
Sistema de Logros y Gamificación para el Bingo Educativo
"""
import json
import os
from typing import Dict, List, Set, Optional, Any
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from services.analytics_service import analytics

@dataclass
class Achievement:
    """Clase para representar un logro"""
    id: str
    name: str
    description: str
    icon: str
    points: int
    category: str
    condition_type: str  # 'games_played', 'score_reached', 'bingos_achieved', etc.
    condition_value: int
    unlocked: bool = False
    unlocked_date: Optional[str] = None

class AchievementsService:
    """Servicio para manejar logros y gamificación"""
    
    def __init__(self, data_file="achievements_data.json"):
        self.data_file = data_file
        self.achievements: Dict[str, Achievement] = {}
        self.unlocked_achievements: Set[str] = set()
        self.total_points = 0
        self.load_achievements()
        self.load_progress()
    
    def load_achievements(self):
        """Carga la definición de logros"""
        self.achievements = {
            # Logros por juegos jugados
            'first_game': Achievement(
                id='first_game',
                name='Primer Juego',
                description='Completa tu primer juego de bingo',
                icon='🎯',
                points=10,
                category='beginner',
                condition_type='games_played',
                condition_value=1
            ),
            'game_master': Achievement(
                id='game_master',
                name='Maestro del Juego',
                description='Juega 50 partidas',
                icon='👑',
                points=100,
                category='expert',
                condition_type='games_played',
                condition_value=50
            ),
            
            # Logros por puntuación
            'score_starter': Achievement(
                id='score_starter',
                name='Puntuador Inicial',
                description='Alcanza 100 puntos en total',
                icon='⭐',
                points=20,
                category='beginner',
                condition_type='total_score',
                condition_value=100
            ),
            'score_champion': Achievement(
                id='score_champion',
                name='Campeón de Puntuación',
                description='Alcanza 1000 puntos en total',
                icon='🏆',
                points=200,
                category='expert',
                condition_type='total_score',
                condition_value=1000
            ),
            
            # Logros por bingos
            'first_bingo': Achievement(
                id='first_bingo',
                name='Primer Bingo',
                description='Logra tu primer bingo',
                icon='🎉',
                points=50,
                category='beginner',
                condition_type='bingos_achieved',
                condition_value=1
            ),
            'bingo_master': Achievement(
                id='bingo_master',
                name='Maestro del Bingo',
                description='Logra 10 bingos',
                icon='🎊',
                points=300,
                category='expert',
                condition_type='bingos_achieved',
                condition_value=10
            ),
            
            # Logros por precisión
            'accuracy_beginner': Achievement(
                id='accuracy_beginner',
                name='Precisión Básica',
                description='Responde correctamente 10 preguntas',
                icon='🎯',
                points=30,
                category='beginner',
                condition_type='correct_answers',
                condition_value=10
            ),
            'accuracy_expert': Achievement(
                id='accuracy_expert',
                name='Precisión Experta',
                description='Responde correctamente 100 preguntas',
                icon='🎯',
                points=150,
                category='expert',
                condition_type='correct_answers',
                condition_value=100
            ),
            
            # Logros por tiempo
            'dedicated_player': Achievement(
                id='dedicated_player',
                name='Jugador Dedicado',
                description='Juega durante 1 hora en total',
                icon='⏰',
                points=80,
                category='intermediate',
                condition_type='play_time_minutes',
                condition_value=60
            ),
            'marathon_player': Achievement(
                id='marathon_player',
                name='Jugador Maratón',
                description='Juega durante 10 horas en total',
                icon='🏃',
                points=400,
                category='expert',
                condition_type='play_time_minutes',
                condition_value=600
            ),
            
            # Logros por categorías
            'category_explorer': Achievement(
                id='category_explorer',
                name='Explorador de Categorías',
                description='Juega en 3 categorías diferentes',
                icon='🗺️',
                points=60,
                category='intermediate',
                condition_type='categories_played',
                condition_value=3
            ),
            'category_master': Achievement(
                id='category_master',
                name='Maestro de Categorías',
                description='Juega en todas las categorías disponibles',
                icon='🌟',
                points=250,
                category='expert',
                condition_type='categories_played',
                condition_value=5
            )
        }
    
    def check_achievements(self):
        """Verifica si se han desbloqueado nuevos logros"""
        stats = analytics.user_stats
        new_achievements = []
        
        # Obtener categorías jugadas
        categories_played = len(set(
            session.category for session in analytics.sessions 
            if session.category
        ))
        
        for achievement in self.achievements.values():
            if achievement.id in self.unlocked_achievements:
                continue
            
            unlocked = False
            
            if achievement.condition_type == 'games_played':
                unlocked = stats.total_games >= achievement.condition_value
            elif achievement.condition_type == 'total_score':
                unlocked = stats.total_score >= achievement.condition_value
            elif achievement.condition_type == 'bingos_achieved':
                unlocked = stats.bingos_achieved >= achievement.condition_value
            elif achievement.condition_type == 'correct_answers':
                unlocked = stats.total_correct >= achievement.condition_value
            elif achievement.condition_type == 'play_time_minutes':
                unlocked = stats.total_play_time >= achievement.condition_value
            elif achievement.condition_type == 'categories_played':
                unlocked = categories_played >= achievement.condition_value
            
            if unlocked:
                self.unlock_achievement(achievement.id)
                new_achievements.append(achievement)
        
        return new_achievements
    
    def unlock_achievement(self, achievement_id: str):
        """Desbloquea un logro"""
        if achievement_id in self.achievements:
            achievement = self.achievements[achievement_id]
            achievement.unlocked = True
            achievement.unlocked_date = datetime.now().isoformat()
            self.unlocked_achievements.add(achievement_id)
            self.total_points += achievement.points
            self.save_progress()
    
    def get_achievements_by_category(self, category: str) -> List[Achievement]:
        """Obtiene logros por categoría"""
        return [
            achievement for achievement in self.achievements.values()
            if achievement.category == category
        ]
    
    def get_progress_percentage(self, achievement_id: str) -> float:
        """Obtiene el porcentaje de progreso para un logro"""
        if achievement_id not in self.achievements:
            return 0.0
        
        achievement = self.achievements[achievement_id]
        stats = analytics.user_stats
        
        current_value = 0
        if achievement.condition_type == 'games_played':
            current_value = stats.total_games
        elif achievement.condition_type == 'total_score':
            current_value = stats.total_score
        elif achievement.condition_type == 'bingos_achieved':
            current_value = stats.bingos_achieved
        elif achievement.condition_type == 'correct_answers':
            current_value = stats.total_correct
        elif achievement.condition_type == 'play_time_minutes':
            current_value = stats.total_play_time
        elif achievement.condition_type == 'categories_played':
            current_value = len(set(
                session.category for session in analytics.sessions 
                if session.category
            ))
        
        return min(100.0, (current_value / achievement.condition_value) * 100)
    
    def get_leaderboard_data(self) -> Dict[str, Any]:
        """Obtiene datos para el leaderboard"""
        return {
            'total_points': self.total_points,
            'achievements_unlocked': len(self.unlocked_achievements),
            'total_achievements': len(self.achievements),
            'completion_percentage': (len(self.unlocked_achievements) / len(self.achievements)) * 100
        }
    
    def save_progress(self):
        """Guarda el progreso de logros"""
        data = {
            'unlocked_achievements': list(self.unlocked_achievements),
            'total_points': self.total_points,
            'achievements': {
                aid: asdict(achievement) 
                for aid, achievement in self.achievements.items()
            }
        }
        
        with open(self.data_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    
    def load_progress(self):
        """Carga el progreso de logros"""
        if not os.path.exists(self.data_file):
            return
        
        try:
            with open(self.data_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            self.unlocked_achievements = set(data.get('unlocked_achievements', []))
            self.total_points = data.get('total_points', 0)
            
            # Actualizar estado de logros
            for aid, achievement_data in data.get('achievements', {}).items():
                if aid in self.achievements:
                    self.achievements[aid].unlocked = achievement_data.get('unlocked', False)
                    self.achievements[aid].unlocked_date = achievement_data.get('unlocked_date')
                    
        except Exception as e:
            print(f"Error loading achievements data: {e}")

# Instancia global
achievements = AchievementsService()
