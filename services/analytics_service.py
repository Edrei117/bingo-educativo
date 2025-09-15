"""
Servicio de Analytics para el Bingo Educativo
"""
import json
import os
from datetime import datetime, timedelta
from typing import Dict, List, Any
from dataclasses import dataclass, asdict
from collections import defaultdict

@dataclass
class GameSession:
    """Datos de una sesión de juego"""
    session_id: str
    start_time: datetime
    end_time: Optional[datetime] = None
    category: str = ""
    questions_answered: int = 0
    correct_answers: int = 0
    wrong_answers: int = 0
    bingo_achieved: bool = False
    score: int = 0
    duration_minutes: float = 0.0

@dataclass
class UserStats:
    """Estadísticas del usuario"""
    total_games: int = 0
    total_score: int = 0
    total_correct: int = 0
    total_wrong: int = 0
    bingos_achieved: int = 0
    favorite_category: str = ""
    average_score: float = 0.0
    total_play_time: float = 0.0

class AnalyticsService:
    """Servicio para manejar analytics y estadísticas"""
    
    def __init__(self, data_file="analytics_data.json"):
        self.data_file = data_file
        self.current_session = None
        self.sessions: List[GameSession] = []
        self.user_stats = UserStats()
        self.load_data()
    
    def start_session(self, category: str = "") -> str:
        """Inicia una nueva sesión de juego"""
        session_id = f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        self.current_session = GameSession(
            session_id=session_id,
            start_time=datetime.now(),
            category=category
        )
        return session_id
    
    def end_session(self, score: int = 0, bingo_achieved: bool = False):
        """Finaliza la sesión actual"""
        if self.current_session:
            self.current_session.end_time = datetime.now()
            self.current_session.score = score
            self.current_session.bingo_achieved = bingo_achieved
            self.current_session.duration_minutes = (
                self.current_session.end_time - self.current_session.start_time
            ).total_seconds() / 60
            
            self.sessions.append(self.current_session)
            self.update_user_stats()
            self.save_data()
            self.current_session = None
    
    def record_answer(self, correct: bool):
        """Registra una respuesta del usuario"""
        if self.current_session:
            if correct:
                self.current_session.correct_answers += 1
            else:
                self.current_session.wrong_answers += 1
            self.current_session.questions_answered += 1
    
    def update_user_stats(self):
        """Actualiza las estadísticas del usuario"""
        if not self.sessions:
            return
        
        self.user_stats.total_games = len(self.sessions)
        self.user_stats.total_score = sum(s.score for s in self.sessions)
        self.user_stats.total_correct = sum(s.correct_answers for s in self.sessions)
        self.user_stats.total_wrong = sum(s.wrong_answers for s in self.sessions)
        self.user_stats.bingos_achieved = sum(1 for s in self.sessions if s.bingo_achieved)
        self.user_stats.total_play_time = sum(s.duration_minutes for s in self.sessions)
        
        if self.user_stats.total_games > 0:
            self.user_stats.average_score = self.user_stats.total_score / self.user_stats.total_games
        
        # Categoría favorita
        category_counts = defaultdict(int)
        for session in self.sessions:
            if session.category:
                category_counts[session.category] += 1
        
        if category_counts:
            self.user_stats.favorite_category = max(category_counts, key=category_counts.get)
    
    def get_weekly_stats(self) -> Dict[str, Any]:
        """Obtiene estadísticas de la última semana"""
        week_ago = datetime.now() - timedelta(days=7)
        recent_sessions = [s for s in self.sessions if s.start_time >= week_ago]
        
        return {
            'games_played': len(recent_sessions),
            'total_score': sum(s.score for s in recent_sessions),
            'bingos_achieved': sum(1 for s in recent_sessions if s.bingo_achieved),
            'play_time_hours': sum(s.duration_minutes for s in recent_sessions) / 60
        }
    
    def get_category_performance(self) -> Dict[str, Dict[str, Any]]:
        """Obtiene rendimiento por categoría"""
        category_stats = defaultdict(lambda: {
            'games': 0, 'total_score': 0, 'correct': 0, 'wrong': 0, 'bingos': 0
        })
        
        for session in self.sessions:
            if session.category:
                stats = category_stats[session.category]
                stats['games'] += 1
                stats['total_score'] += session.score
                stats['correct'] += session.correct_answers
                stats['wrong'] += session.wrong_answers
                if session.bingo_achieved:
                    stats['bingos'] += 1
        
        # Calcular promedios
        for category, stats in category_stats.items():
            if stats['games'] > 0:
                stats['avg_score'] = stats['total_score'] / stats['games']
                stats['accuracy'] = stats['correct'] / (stats['correct'] + stats['wrong']) * 100
        
        return dict(category_stats)
    
    def save_data(self):
        """Guarda los datos en archivo"""
        data = {
            'sessions': [asdict(session) for session in self.sessions],
            'user_stats': asdict(self.user_stats)
        }
        
        # Convertir datetime a string para JSON
        for session_data in data['sessions']:
            session_data['start_time'] = session_data['start_time'].isoformat()
            if session_data['end_time']:
                session_data['end_time'] = session_data['end_time'].isoformat()
        
        with open(self.data_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    
    def load_data(self):
        """Carga los datos desde archivo"""
        if not os.path.exists(self.data_file):
            return
        
        try:
            with open(self.data_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Convertir strings de datetime de vuelta a objetos datetime
            for session_data in data.get('sessions', []):
                session_data['start_time'] = datetime.fromisoformat(session_data['start_time'])
                if session_data.get('end_time'):
                    session_data['end_time'] = datetime.fromisoformat(session_data['end_time'])
                self.sessions.append(GameSession(**session_data))
            
            if 'user_stats' in data:
                self.user_stats = UserStats(**data['user_stats'])
                
        except Exception as e:
            print(f"Error loading analytics data: {e}")

# Instancia global
analytics = AnalyticsService()
