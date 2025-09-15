"""
Gestor de Estado para Bingo Educativo
Maneja el estado global de la aplicación de manera reactiva
"""

from typing import Any, Dict, List, Callable, Optional
from dataclasses import dataclass, field
from enum import Enum
import json
from datetime import datetime


class GameStatus(Enum):
    """Estados posibles del juego"""
    IDLE = "idle"
    LOADING = "loading"
    PLAYING = "playing"
    PAUSED = "paused"
    FINISHED = "finished"
    ERROR = "error"


@dataclass
class Player:
    """Modelo de jugador"""
    id: str
    name: str
    score: int = 0
    is_ai: bool = False
    difficulty: str = "normal"
    connected: bool = True


@dataclass
class GameState:
    """Estado completo del juego"""
    status: GameStatus = GameStatus.IDLE
    current_player: Optional[str] = None
    players: List[Player] = field(default_factory=list)
    current_question: Optional[Dict[str, Any]] = None
    game_start_time: Optional[datetime] = None
    round_number: int = 0
    max_rounds: int = 25
    winner: Optional[str] = None
    error_message: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convierte el estado a diccionario para serialización"""
        return {
            'status': self.status.value,
            'current_player': self.current_player,
            'players': [player.__dict__ for player in self.players],
            'current_question': self.current_question,
            'game_start_time': self.game_start_time.isoformat() if self.game_start_time else None,
            'round_number': self.round_number,
            'max_rounds': self.max_rounds,
            'winner': self.winner,
            'error_message': self.error_message
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'GameState':
        """Crea un estado desde diccionario"""
        return cls(
            status=GameStatus(data.get('status', 'idle')),
            current_player=data.get('current_player'),
            players=[Player(**p) for p in data.get('players', [])],
            current_question=data.get('current_question'),
            game_start_time=datetime.fromisoformat(data['game_start_time']) if data.get('game_start_time') else None,
            round_number=data.get('round_number', 0),
            max_rounds=data.get('max_rounds', 25),
            winner=data.get('winner'),
            error_message=data.get('error_message')
        )


class StateManager:
    """
    Gestor de estado reactivo para la aplicación
    Implementa el patrón Observer para notificar cambios
    """
    
    def __init__(self):
        self._state = GameState()
        self._listeners: Dict[str, List[Callable]] = {}
        self._history: List[GameState] = []
        self._max_history = 50
    
    def subscribe(self, key: str, callback: Callable) -> None:
        """Suscribe un callback a cambios en una clave específica"""
        if key not in self._listeners:
            self._listeners[key] = []
        self._listeners[key].append(callback)
    
    def unsubscribe(self, key: str, callback: Callable) -> None:
        """Desuscribe un callback"""
        if key in self._listeners and callback in self._listeners[key]:
            self._listeners[key].remove(callback)
    
    def _notify_listeners(self, key: str, value: Any) -> None:
        """Notifica a todos los listeners de un cambio"""
        if key in self._listeners:
            for callback in self._listeners[key]:
                try:
                    callback(key, value)
                except Exception as e:
                    print(f"Error en callback para {key}: {e}")
    
    def set_state(self, key: str, value: Any) -> None:
        """Establece un valor en el estado y notifica"""
        if hasattr(self._state, key):
            old_value = getattr(self._state, key)
            setattr(self._state, key, value)
            if old_value != value:
                self._notify_listeners(key, value)
        else:
            print(f"Warning: Clave '{key}' no existe en GameState")
    
    def get_state(self, key: str, default: Any = None) -> Any:
        """Obtiene un valor del estado"""
        return getattr(self._state, key, default)
    
    def get_full_state(self) -> GameState:
        """Obtiene el estado completo"""
        return self._state
    
    def update_state(self, updates: Dict[str, Any]) -> None:
        """Actualiza múltiples valores del estado"""
        for key, value in updates.items():
            self.set_state(key, value)
    
    def save_state(self) -> None:
        """Guarda el estado actual en el historial"""
        import copy
        self._history.append(copy.deepcopy(self._state))
        if len(self._history) > self._max_history:
            self._history.pop(0)
    
    def undo(self) -> bool:
        """Deshace el último cambio de estado"""
        if self._history:
            self._state = self._history.pop()
            return True
        return False
    
    def reset_state(self) -> None:
        """Resetea el estado a valores iniciales"""
        self._state = GameState()
        self._history.clear()
        # Notificar reset a todos los listeners
        for key in self._listeners:
            self._notify_listeners(key, getattr(self._state, key, None))
    
    def export_state(self) -> str:
        """Exporta el estado como JSON"""
        return json.dumps(self._state.to_dict(), indent=2)
    
    def import_state(self, json_data: str) -> bool:
        """Importa estado desde JSON"""
        try:
            data = json.loads(json_data)
            self._state = GameState.from_dict(data)
            # Notificar a todos los listeners
            for key in self._listeners:
                self._notify_listeners(key, getattr(self._state, key, None))
            return True
        except Exception as e:
            print(f"Error importando estado: {e}")
            return False
    
    # Métodos específicos del juego
    def add_player(self, player: Player) -> None:
        """Agrega un jugador al estado"""
        self._state.players.append(player)
        self._notify_listeners('players', self._state.players)
    
    def remove_player(self, player_id: str) -> None:
        """Remueve un jugador del estado"""
        self._state.players = [p for p in self._state.players if p.id != player_id]
        self._notify_listeners('players', self._state.players)
    
    def update_player_score(self, player_id: str, score: int) -> None:
        """Actualiza el puntaje de un jugador"""
        for player in self._state.players:
            if player.id == player_id:
                player.score = score
                self._notify_listeners('players', self._state.players)
                break
    
    def next_round(self) -> None:
        """Avanza al siguiente round"""
        self._state.round_number += 1
        self._notify_listeners('round_number', self._state.round_number)
    
    def set_game_status(self, status: GameStatus) -> None:
        """Establece el estado del juego"""
        self._state.status = status
        self._notify_listeners('status', status)
        
        if status == GameStatus.PLAYING and not self._state.game_start_time:
            self._state.game_start_time = datetime.now()
            self._notify_listeners('game_start_time', self._state.game_start_time)


# Instancia global del gestor de estado
state_manager = StateManager() 