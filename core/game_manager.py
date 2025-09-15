"""
Gestor de Juego para Bingo Educativo
Maneja toda la lógica del juego de manera centralizada
"""

from typing import Dict, List, Optional, Any, Tuple
import random
import json
import os
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum

from .state_manager import state_manager, GameStatus, Player, GameState


class QuestionDifficulty(Enum):
    """Dificultades de preguntas"""
    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"


@dataclass
class Question:
    """Modelo de pregunta"""
    id: str
    text: str
    options: List[str]
    correct_answer: int
    category: str
    difficulty: QuestionDifficulty
    explanation: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'text': self.text,
            'options': self.options,
            'correct_answer': self.correct_answer,
            'category': self.category,
            'difficulty': self.difficulty.value,
            'explanation': self.explanation
        }


@dataclass
class BingoCard:
    """Modelo de cartón de bingo"""
    id: str
    questions: List[Question]
    player_id: str
    marked_questions: List[int] = field(default_factory=list)
    
    def mark_question(self, question_index: int) -> bool:
        """Marca una pregunta como respondida"""
        if 0 <= question_index < len(self.questions) and question_index not in self.marked_questions:
            self.marked_questions.append(question_index)
            return True
        return False
    
    def check_bingo(self) -> bool:
        """Verifica si hay bingo (3 en línea)"""
        if len(self.marked_questions) < 3:
            return False
        
        # Verificar líneas horizontales
        for row in range(3):
            row_questions = [row * 3 + col for col in range(3)]
            if all(q in self.marked_questions for q in row_questions):
                return True
        
        # Verificar líneas verticales
        for col in range(3):
            col_questions = [row * 3 + col for row in range(3)]
            if all(q in self.marked_questions for q in col_questions):
                return True
        
        # Verificar diagonales
        diagonal1 = [0, 4, 8]  # Diagonal principal
        diagonal2 = [2, 4, 6]  # Diagonal secundaria
        
        if all(q in self.marked_questions for q in diagonal1):
            return True
        if all(q in self.marked_questions for q in diagonal2):
            return True
        
        return False
    
    def get_completion_percentage(self) -> float:
        """Obtiene el porcentaje de completado del cartón"""
        return (len(self.marked_questions) / len(self.questions)) * 100


class GameManager:
    """
    Gestor principal del juego
    Maneja toda la lógica del bingo educativo
    """
    
    def __init__(self):
        self.state_manager = state_manager
        self.questions_database: Dict[str, List[Question]] = {}
        self.current_game_cards: Dict[str, BingoCard] = {}
        self.game_timer: Optional[datetime] = None
        self.question_timer: Optional[datetime] = None
        self.max_question_time = 30  # segundos
        
        # Cargar preguntas al inicializar
        self._load_questions()
        
        # Suscribirse a cambios de estado
        self.state_manager.subscribe('status', self._on_status_change)
        self.state_manager.subscribe('players', self._on_players_change)
    
    def _load_questions(self) -> None:
        """Carga todas las preguntas desde los archivos JSON"""
        categories_path = "cartones"
        
        if not os.path.exists(categories_path):
            print(f"Warning: Directorio {categories_path} no encontrado")
            return
        
        for category_dir in os.listdir(categories_path):
            category_path = os.path.join(categories_path, category_dir)
            if os.path.isdir(category_path):
                self._load_category_questions(category_dir, category_path)
    
    def _load_category_questions(self, category: str, category_path: str) -> None:
        """Carga preguntas de una categoría específica"""
        questions = []
        
        for filename in os.listdir(category_path):
            if filename.endswith('.json'):
                file_path = os.path.join(category_path, filename)
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        
                    if 'preguntas' in data:
                        for i, q_data in enumerate(data['preguntas']):
                            question = Question(
                                id=f"{category}_{filename}_{i}",
                                text=q_data['pregunta'],
                                options=q_data['opciones'],
                                correct_answer=q_data['opciones'].index(q_data['respuesta_correcta']),
                                category=category,
                                difficulty=QuestionDifficulty.MEDIUM  # Por defecto
                            )
                            questions.append(question)
                            
                except Exception as e:
                    print(f"Error cargando {file_path}: {e}")
        
        if questions:
            self.questions_database[category] = questions
            print(f"Cargadas {len(questions)} preguntas de categoría '{category}'")
    
    def start_game(self, config: Dict[str, Any]) -> bool:
        """
        Inicia un nuevo juego con la configuración especificada
        
        Args:
            config: Diccionario con configuración del juego
                - player_name: Nombre del jugador
                - num_ais: Número de IAs
                - ai_difficulty: Dificultad de las IAs
                - categories: Lista de categorías a usar
        """
        try:
            # Resetear estado
            self.state_manager.reset_state()
            
            # Configurar jugadores
            self._setup_players(config)
            
            # Generar cartones
            self._generate_cards(config.get('categories', []))
            
            # Iniciar juego
            self.state_manager.set_game_status(GameStatus.PLAYING)
            self.game_timer = datetime.now()
            
            # Configurar primera pregunta
            self._setup_next_question()
            
            return True
            
        except Exception as e:
            print(f"Error iniciando juego: {e}")
            self.state_manager.set_state('error_message', str(e))
            self.state_manager.set_game_status(GameStatus.ERROR)
            return False
    
    def _setup_players(self, config: Dict[str, Any]) -> None:
        """Configura los jugadores del juego"""
        player_name = config.get('player_name', 'Jugador')
        num_ais = config.get('num_ais', 1)
        ai_difficulty = config.get('ai_difficulty', 'normal')
        
        # Agregar jugador principal
        main_player = Player(
            id="player_1",
            name=player_name,
            is_ai=False
        )
        self.state_manager.add_player(main_player)
        
        # Agregar IAs
        for i in range(num_ais):
            ai_player = Player(
                id=f"ai_{i+1}",
                name=f"IA {i+1}",
                is_ai=True,
                difficulty=ai_difficulty
            )
            self.state_manager.add_player(ai_player)
    
    def _generate_cards(self, categories: List[str]) -> None:
        """Genera cartones para todos los jugadores"""
        if not categories:
            categories = list(self.questions_database.keys())
        
        for player in self.state_manager.get_state('players'):
            card_questions = self._select_questions_for_card(categories, 9)  # 3x3 cartón
            card = BingoCard(
                id=f"card_{player.id}",
                questions=card_questions,
                player_id=player.id
            )
            self.current_game_cards[player.id] = card
    
    def _select_questions_for_card(self, categories: List[str], num_questions: int) -> List[Question]:
        """Selecciona preguntas aleatorias para un cartón"""
        all_questions = []
        for category in categories:
            if category in self.questions_database:
                all_questions.extend(self.questions_database[category])
        
        if len(all_questions) < num_questions:
            # Si no hay suficientes preguntas, repetir algunas
            while len(all_questions) < num_questions:
                all_questions.extend(all_questions[:num_questions - len(all_questions)])
        
        return random.sample(all_questions, num_questions)
    
    def _setup_next_question(self) -> None:
        """Configura la siguiente pregunta del juego"""
        # Seleccionar pregunta aleatoria de todas las categorías
        all_questions = []
        for questions in self.questions_database.values():
            all_questions.extend(questions)
        
        if not all_questions:
            self.state_manager.set_state('error_message', 'No hay preguntas disponibles')
            return
        
        selected_question = random.choice(all_questions)
        self.state_manager.set_state('current_question', selected_question.to_dict())
        self.question_timer = datetime.now()
        
        # Notificar a la UI que hay una nueva pregunta
        self.state_manager._notify_listeners('current_question', selected_question.to_dict())
    
    def process_answer(self, player_id: str, answer_index: int) -> Dict[str, Any]:
        """
        Procesa la respuesta de un jugador
        
        Returns:
            Dict con información del resultado
        """
        current_question = self.state_manager.get_state('current_question')
        if not current_question:
            return {'success': False, 'error': 'No hay pregunta activa'}
        
        # Verificar si la pregunta está en el cartón del jugador
        player_card = self.current_game_cards.get(player_id)
        if not player_card:
            return {'success': False, 'error': 'Cartón no encontrado'}
        
        # Encontrar la pregunta en el cartón
        question_index = None
        for i, question in enumerate(player_card.questions):
            if question.id == current_question['id']:
                question_index = i
                break
        
        if question_index is None:
            return {'success': False, 'error': 'Pregunta no está en tu cartón'}
        
        # Verificar respuesta
        is_correct = answer_index == current_question['correct_answer']
        
        if is_correct:
            # Marcar pregunta como correcta
            player_card.mark_question(question_index)
            
            # Actualizar puntaje
            player = next((p for p in self.state_manager.get_state('players') if p.id == player_id), None)
            if player:
                player.score += 10
                self.state_manager.update_player_score(player_id, player.score)
            
            # Verificar bingo
            if player_card.check_bingo():
                return self._handle_bingo(player_id)
        
        # Avanzar al siguiente round
        self.state_manager.next_round()
        
        # Configurar siguiente pregunta
        self._setup_next_question()
        
        return {
            'success': True,
            'correct': is_correct,
            'score': player.score if player else 0,
            'bingo': player_card.check_bingo() if is_correct else False
        }
    
    def _handle_bingo(self, player_id: str) -> Dict[str, Any]:
        """Maneja cuando un jugador hace bingo"""
        player = next((p for p in self.state_manager.get_state('players') if p.id == player_id), None)
        
        if player:
            player.score += 50  # Bonus por bingo
            self.state_manager.update_player_score(player_id, player.score)
        
        # Determinar ganador
        players = self.state_manager.get_state('players')
        winner = max(players, key=lambda p: p.score)
        
        self.state_manager.set_state('winner', winner.id)
        self.state_manager.set_game_status(GameStatus.FINISHED)
        
        return {
            'success': True,
            'bingo': True,
            'winner': winner.name,
            'final_score': winner.score
        }
    
    def get_game_stats(self) -> Dict[str, Any]:
        """Obtiene estadísticas del juego actual"""
        players = self.state_manager.get_state('players')
        current_question = self.state_manager.get_state('current_question')
        
        stats = {
            'round': self.state_manager.get_state('round_number'),
            'max_rounds': self.state_manager.get_state('max_rounds'),
            'players': [
                {
                    'name': p.name,
                    'score': p.score,
                    'is_ai': p.is_ai,
                    'card_completion': self.current_game_cards.get(p.id, BingoCard('', [], '')).get_completion_percentage()
                }
                for p in players
            ],
            'current_question': current_question,
            'game_duration': None
        }
        
        if self.game_timer:
            duration = datetime.now() - self.game_timer
            stats['game_duration'] = str(duration).split('.')[0]
        
        return stats
    
    def pause_game(self) -> None:
        """Pausa el juego"""
        self.state_manager.set_game_status(GameStatus.PAUSED)
    
    def resume_game(self) -> None:
        """Reanuda el juego"""
        self.state_manager.set_game_status(GameStatus.PLAYING)
    
    def end_game(self) -> None:
        """Termina el juego"""
        self.state_manager.set_game_status(GameStatus.FINISHED)
        self.game_timer = None
        self.question_timer = None
    
    def _on_status_change(self, key: str, value: GameStatus) -> None:
        """Callback cuando cambia el estado del juego"""
        print(f"Estado del juego cambiado a: {value.value}")
    
    def _on_players_change(self, key: str, value: List[Player]) -> None:
        """Callback cuando cambian los jugadores"""
        print(f"Jugadores actualizados: {len(value)} jugadores")


# Instancia global del gestor de juego
game_manager = GameManager() 