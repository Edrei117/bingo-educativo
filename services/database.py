from typing import Optional, Dict, List, Any, Union, cast, TypeVar, Tuple, NoReturn, Type
import sqlite3
import os
from datetime import datetime
# from pymongo import MongoClient  # Comentado para compatibilidad con APK
# from dotenv import load_dotenv    # Comentado para compatibilidad con APK
import random
# from models.question import Question  # Comentado temporalmente

T = TypeVar('T')

class Database:
    def __init__(self, db_path: str = "bingo_quiz.db"):
        self.db_path = db_path
        self.conn: Optional[sqlite3.Connection] = None
        self.cursor: Optional[sqlite3.Cursor] = None
        self.connect()
        # mongodb_uri = os.getenv('MONGODB_URI', '')  # Comentado para compatibilidad con APK
        # mongodb_db = os.getenv('MONGODB_DB', '')    # Comentado para compatibilidad con APK
        # self.client = MongoClient(mongodb_uri)      # Comentado para compatibilidad con APK
        # self.db = self.client[mongodb_db]           # Comentado para compatibilidad con APK
        # self.questions = self.db.questions          # Comentado para compatibilidad con APK
        # self.games = self.db.games                  # Comentado para compatibilidad con APK
        self.client = None
        self.db = None
        self.questions = None
        self.games = None
        
    def connect(self) -> None:
        """Establece la conexión con la base de datos"""
        self.conn = sqlite3.connect(self.db_path)
        self.cursor = self.conn.cursor()
        self.create_tables()
        
    def create_tables(self) -> None:
        """Crea las tablas necesarias si no existen"""
        if not self.cursor or not self.conn:
            return
            
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS games (
                id TEXT PRIMARY KEY,
                created_at TIMESTAMP,
                is_online BOOLEAN,
                host_id TEXT
            )
        """)
        
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS players (
                id TEXT PRIMARY KEY,
                game_id TEXT,
                score INTEGER,
                FOREIGN KEY (game_id) REFERENCES games (id)
            )
        """)
        
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS questions (
                id TEXT PRIMARY KEY,
                question TEXT,
                answer TEXT,
                category TEXT,
                options TEXT,
                correct_answer INTEGER
            )
        """)
        
        self.conn.commit()
        
    def save_game(self, game_data: Dict[str, Any]) -> str:
        """Guarda un juego en la base de datos"""
        if not self.cursor or not self.conn:
            return ""
            
        game_id = game_data.get('game_id')
        if not game_id:
            game_id = f"game_{datetime.now().strftime('%Y%m%d%H%M%S')}"
            
        self.cursor.execute("""
            INSERT OR REPLACE INTO games (id, created_at, is_online, host_id)
            VALUES (?, ?, ?, ?)
        """, (
            game_id,
            game_data.get('created_at', datetime.now()),
            game_data.get('is_online', False),
            game_data.get('host')
        ))
        
        self.conn.commit()
        return game_id
        
    def get_game(self, game_id: str) -> Optional[Dict[str, Any]]:
        """Obtiene un juego de la base de datos"""
        if not self.cursor:
            return None
            
        self.cursor.execute("SELECT * FROM games WHERE id = ?", (game_id,))
        game = self.cursor.fetchone()
        
        if not game:
            return None
            
        return {
            'id': cast(str, game[0]),
            'created_at': cast(datetime, game[1]),
            'is_online': cast(bool, game[2]),
            'host': cast(str, game[3])
        }
        
    def save_question(self, question_data: Dict[str, Any]) -> str:
        """Guarda una pregunta en la base de datos"""
        if not self.cursor or not self.conn:
            return ""
            
        question_id = question_data.get('id')
        if not question_id:
            question_id = f"q_{datetime.now().strftime('%Y%m%d%H%M%S')}"
            
        self.cursor.execute("""
            INSERT OR REPLACE INTO questions 
            (id, question, answer, category, options, correct_answer)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            question_id,
            question_data.get('question'),
            question_data.get('answer'),
            question_data.get('category'),
            str(question_data.get('options', [])),
            question_data.get('correct_answer')
        ))
        
        self.conn.commit()
        return question_id
        
    def get_questions(self, category: Optional[str] = None) -> List[Dict[str, Any]]:
        """Obtiene preguntas de la base de datos"""
        if not self.cursor:
            return []
            
        if category:
            self.cursor.execute("SELECT * FROM questions WHERE category = ?", (category,))
        else:
            self.cursor.execute("SELECT * FROM questions")
            
        questions: List[Dict[str, Any]] = []
        for row in self.cursor.fetchall():
            questions.append({
                'id': cast(str, row[0]),
                'question': cast(str, row[1]),
                'answer': cast(str, row[2]),
                'category': cast(str, row[3]),
                'options': eval(cast(str, row[4])),
                'correct_answer': cast(int, row[5])
            })
            
        return questions
        
    def close(self) -> None:
        """Cierra la conexión con la base de datos"""
        if self.conn:
            self.conn.close()
        # self.client.close()  # Comentado para compatibilidad con APK

    def get_questions_by_category(self, category: str) -> List[Dict]:
        """Obtener preguntas por categoría (SQLite solo)"""
        # Función simplificada para compatibilidad con APK
        return []
        
    def add_question(self, question_data) -> str:
        """Agregar una nueva pregunta (SQLite solo)"""
        # Función simplificada para compatibilidad con APK
        return ""
        
    def update_question(self, question_id: str, question_data: Dict) -> bool:
        """Actualizar una pregunta existente (SQLite solo)"""
        # Función simplificada para compatibilidad con APK
        return False
        
    def delete_question(self, question_id: str) -> bool:
        """Eliminar una pregunta (SQLite solo)"""
        # Función simplificada para compatibilidad con APK
        return False
        
    def get_random_question(self, category: Optional[str] = None) -> Dict[str, Any]:
        """Obtener una pregunta aleatoria (SQLite solo)"""
        # Función simplificada para compatibilidad con APK
        return {}

    def update_game(self, game_id, game_data):
        """Actualizar juego (SQLite solo)"""
        # Función simplificada para compatibilidad con APK
        return False

    def delete_game(self, game_id):
        """Eliminar juego (SQLite solo)"""
        # Función simplificada para compatibilidad con APK
        return False

    def get_online_games(self):
        """Obtener juegos en línea (SQLite solo)"""
        # Función simplificada para compatibilidad con APK
        return [] 