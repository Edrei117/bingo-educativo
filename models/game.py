from dataclasses import dataclass
from typing import List, Dict, Optional
import random
from datetime import datetime
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.clock import Clock
from kivy.properties import NumericProperty, ListProperty

@dataclass
class Question:
    id: str
    question: str
    answer: str
    category: str
    options: List[str]
    correct_answer: int

    def to_dict(self) -> Dict:
        return {
            'id': self.id,
            'question': self.question,
            'answer': self.answer,
            'category': self.category,
            'options': self.options,
            'correct_answer': self.correct_answer
        }

    @classmethod
    def from_dict(cls, data: Dict) -> 'Question':
        return cls(
            id=data['id'],
            question=data['question'],
            answer=data['answer'],
            category=data['category'],
            options=data['options'],
            correct_answer=data['correct_answer']
        )

class BingoCard(BoxLayout):
    card_number = NumericProperty(0)
    numbers = ListProperty([])
    marked_numbers = ListProperty([])
    
    def __init__(self, card_number=0, **kwargs):
        super(BingoCard, self).__init__(**kwargs)
        self.card_number = card_number
        self.orientation = 'vertical'
        self.spacing = 5
        self.padding = 10
        self.generate_numbers()
        self.create_card()
        
    def generate_numbers(self):
        """Genera los números aleatorios para el cartón"""
        b_numbers = random.sample(range(1, 16), 5)
        i_numbers = random.sample(range(16, 31), 5)
        n_numbers = random.sample(range(31, 46), 5)
        g_numbers = random.sample(range(46, 61), 5)
        o_numbers = random.sample(range(61, 76), 5)
        self.numbers = b_numbers + i_numbers + n_numbers + g_numbers + o_numbers
        
    def create_card(self):
        """Crea la interfaz visual del cartón"""
        container = BoxLayout(orientation='vertical')
        
        # Crear encabezado con letras BINGO
        header = BoxLayout(size_hint_y=None, height=40)
        for letter in ['B', 'I', 'N', 'G', 'O']:
            header.add_widget(Label(text=letter, font_size=24, bold=True))
        container.add_widget(header)
        
        # Crear grid de números
        for row in range(5):
            row_layout = BoxLayout(spacing=5)
            for col in range(5):
                number = self.numbers[row + col * 5]
                number_label = Label(
                    text=str(number),
                    font_size=20,
                    size_hint=(None, None),
                    size=(50, 50)
                )
                row_layout.add_widget(number_label)
            container.add_widget(row_layout)
            
        self.add_widget(container)
            
    def mark_number(self, number):
        """Marca un número en el cartón"""
        if number in self.numbers and number not in self.marked_numbers:
            self.marked_numbers.append(number)
            index = self.numbers.index(number)
            row = index % 5
            col = index // 5
            number_widget = self.children[0].children[1:][row].children[4-col]
            number_widget.color = (1, 0, 0, 1)
            
    def check_bingo(self):
        """Verifica si hay bingo"""
        # Verificar líneas horizontales
        for row in range(5):
            if all(self.numbers[row + col * 5] in self.marked_numbers for col in range(5)):
                return True
                
        # Verificar líneas verticales
        for col in range(5):
            if all(self.numbers[row + col * 5] in self.marked_numbers for row in range(5)):
                return True
                
        # Verificar diagonal principal
        if all(self.numbers[i * 6] in self.marked_numbers for i in range(5)):
            return True
            
        # Verificar diagonal secundaria
        if all(self.numbers[i * 4 + 4] in self.marked_numbers for i in range(5)):
            return True
            
        return False

class Game:
    def __init__(self):
        self.categories = {
            'historia': [],
            'cultura': [],
            'deporte': [],
            'ciencia': [],
            'arte': []
        }
        self.players = {}
        self.current_questions = []
        self.is_online = False
        self.game_id = None
        self.host = None
        self.created_at = datetime.now()
        
    def add_question(self, question: Question) -> bool:
        if question.category in self.categories:
            self.categories[question.category].append(question)
            return True
        return False

    def create_card(self, category: str, player_id: str) -> Optional[BingoCard]:
        if category not in self.categories:
            return None
        
        card = BingoCard(card_number=len(self.players.get(player_id, [])) + 1)
        questions = self.categories[category].copy()
        random.shuffle(questions)
        
        if player_id not in self.players:
            self.players[player_id] = []
        
        self.players[player_id].append(card)
        return card

    def get_random_question(self, category: Optional[str] = None) -> Optional[Question]:
        if category:
            if category not in self.categories or not self.categories[category]:
                return None
            questions = self.categories[category]
        else:
            questions = [q for cat in self.categories.values() for q in cat]
            if not questions:
                return None
        
        available_questions = [q for q in questions if q not in self.current_questions]
        if not available_questions:
            return None
        
        question = random.choice(available_questions)
        self.current_questions.append(question)
        return question

    def check_answer(self, player_id: str, card_index: int, row: int, col: int, answer: int) -> bool:
        if player_id not in self.players or card_index >= len(self.players[player_id]):
            return False
        
        card = self.players[player_id][card_index]
        question = card.get_question(row, col)
        
        if not question or question.answered:
            return False
        
        is_correct = question.answer(answer)
        if is_correct:
            card.mark_question(question.id)
        
        return is_correct

    def start_online_game(self, player_id: str) -> str:
        self.is_online = True
        self.game_id = f"game_{random.randint(1000, 9999)}"
        self.host = player_id
        return self.game_id

    def join_online_game(self, game_id: str, player_id: str) -> bool:
        if self.game_id == game_id and player_id != self.host:
            return True
        return False

    def to_dict(self) -> Dict:
        return {
            'categories': {cat: [q.to_dict() for q in questions] 
                         for cat, questions in self.categories.items()},
            'players': {pid: [card.to_dict() for card in cards] 
                       for pid, cards in self.players.items()},
            'current_questions': [q.to_dict() for q in self.current_questions],
            'is_online': self.is_online,
            'game_id': self.game_id,
            'host': self.host,
            'created_at': self.created_at
        }

    @classmethod
    def from_dict(cls, data: Dict) -> 'Game':
        game = cls()
        game.categories = {cat: [Question.from_dict(q) for q in questions] 
                         for cat, questions in data['categories'].items()}
        game.players = {pid: [BingoCard.from_dict(card) for card in cards] 
                       for pid, cards in data['players'].items()}
        game.current_questions = [Question.from_dict(q) for q in data['current_questions']]
        game.is_online = data['is_online']
        game.game_id = data['game_id']
        game.host = data['host']
        game.created_at = data['created_at']
        return game 

class BingoGame(BoxLayout):
    def __init__(self, **kwargs):
        super(BingoGame, self).__init__(**kwargs)
        self.orientation = 'vertical'
        self.spacing = 10
        self.padding = 10
        
        # Configuración del juego
        self.cards = []
        self.called_numbers = []
        self.game_active = False
        self.current_number = None
        
        # Crear interfaz
        self.create_interface()
        
    def create_interface(self):
        """Crea la interfaz del juego"""
        # Área de números llamados
        self.called_numbers_label = Label(
            text="Números llamados: ",
            size_hint_y=None,
            height=40
        )
        self.add_widget(self.called_numbers_label)
        
        # Área de cartones
        self.cards_container = BoxLayout(spacing=10)
        self.add_widget(self.cards_container)
        
        # Controles del juego
        controls = BoxLayout(size_hint_y=None, height=50)
        
        self.start_button = Button(text="Iniciar Juego")
        self.start_button.bind(on_press=self.start_game)
        controls.add_widget(self.start_button)
        
        self.call_number_button = Button(text="Llamar Número")
        self.call_number_button.bind(on_press=self.call_number)
        self.call_number_button.disabled = True
        controls.add_widget(self.call_number_button)
        
        self.add_widget(controls)
        
    def add_card(self) -> Optional[BingoCard]:
        """Agrega un nuevo cartón al juego"""
        if len(self.cards) < 4:  # Límite de 4 cartones
            card = BingoCard(card_number=len(self.cards) + 1)
            self.cards.append(card)
            self.cards_container.add_widget(card)
            return card
        return None
        
    def start_game(self, instance):
        """Inicia el juego"""
        if not self.cards:
            self.add_card()  # Agregar al menos un cartón
            
        self.game_active = True
        self.called_numbers = []
        self.current_number = None
        self.start_button.disabled = True
        self.call_number_button.disabled = False
        self.called_numbers_label.text = "Números llamados: "
        
        # Reiniciar cartones
        for card in self.cards:
            card.marked_numbers = []
            for child in card.children[0].children[1:]:  # Excluir el encabezado
                for number_label in child.children:
                    number_label.color = (0, 0, 0, 1)  # Color negro para números no marcados
                    
    def call_number(self, instance):
        """Llama un nuevo número"""
        if not self.game_active:
            return
            
        # Generar número que no haya sido llamado
        available_numbers = [n for n in range(1, 76) if n not in self.called_numbers]
        if not available_numbers:
            self.end_game()
            return
            
        self.current_number = random.choice(available_numbers)
        self.called_numbers.append(self.current_number)
        
        # Actualizar interfaz
        self.called_numbers_label.text = f"Números llamados: {', '.join(map(str, self.called_numbers))}"
        
        # Marcar número en los cartones
        for card in self.cards:
            card.mark_number(self.current_number)
            if card.check_bingo():
                self.end_game(winner=card)
                
    def end_game(self, winner=None):
        """Termina el juego"""
        self.game_active = False
        self.start_button.disabled = False
        self.call_number_button.disabled = True
        
        if winner:
            self.called_numbers_label.text = f"¡Bingo! Cartón {winner.card_number} ha ganado"
        else:
            self.called_numbers_label.text = "¡Juego terminado!" 