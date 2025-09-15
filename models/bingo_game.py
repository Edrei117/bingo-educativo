from typing import Optional
from kivy.uix.boxlayout import BoxLayout
from kivymd.uix.button import MDRaisedButton
from kivy.uix.label import Label
from kivy.clock import Clock
from .bingo_card import BingoCard
import random

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
        
        self.start_button = MDRaisedButton(
            text="Iniciar Juego",
            on_release=self.start_game
        )
        controls.add_widget(self.start_button)
        
        self.call_number_button = MDRaisedButton(
            text="Llamar Número",
            on_release=self.call_number,
            disabled=True
        )
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
            for child in card.children[1:]:  # Excluir el encabezado
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
            self.called_numbers_label.text = f"¡BINGO! Cartón {winner.card_number} ganó!"
        else:
            self.called_numbers_label.text = "¡Juego terminado! Todos los números han sido llamados." 