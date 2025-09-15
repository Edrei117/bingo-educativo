from kivy.uix.boxlayout import BoxLayout
from kivy.uix.image import Image
from kivy.uix.label import Label
from kivy.properties import NumericProperty, ListProperty
from kivy.graphics import Color, Rectangle
import random
import os

class BingoCard(BoxLayout):
    card_number = NumericProperty(0)  # Número del cartón
    numbers = ListProperty([])  # Lista de números del cartón
    marked_numbers = ListProperty([])  # Números marcados
    
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
        # Generar 5 columnas (B, I, N, G, O)
        b_numbers = random.sample(range(1, 16), 5)
        i_numbers = random.sample(range(16, 31), 5)
        n_numbers = random.sample(range(31, 46), 5)
        g_numbers = random.sample(range(46, 61), 5)
        o_numbers = random.sample(range(61, 76), 5)
        
        # Combinar todos los números
        self.numbers = b_numbers + i_numbers + n_numbers + g_numbers + o_numbers
        
    def create_card(self):
        """Crea la interfaz visual del cartón"""
        # Crear contenedor para la imagen de fondo y los números
        container = BoxLayout(orientation='vertical')
        
        # Agregar imagen de fondo
        image_path = f'app/src/main/assets/images/carton_{self.card_number}.png'
        if os.path.exists(image_path):
            background = Image(
                source=image_path,
                size_hint=(1, 1),
                allow_stretch=True,
                keep_ratio=True
            )
            container.add_widget(background)
        
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
                    size=(50, 50),
                    background_color=(1, 1, 1, 0.7)  # Color blanco semi-transparente
                )
                row_layout.add_widget(number_label)
            container.add_widget(row_layout)
            
        self.add_widget(container)
            
    def mark_number(self, number):
        """Marca un número en el cartón"""
        if number in self.numbers and number not in self.marked_numbers:
            self.marked_numbers.append(number)
            # Actualizar la visualización del número marcado
            index = self.numbers.index(number)
            row = index % 5
            col = index // 5
            number_widget = self.children[0].children[1:][row].children[4-col]
            number_widget.color = (1, 0, 0, 1)  # Color rojo para números marcados
            
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