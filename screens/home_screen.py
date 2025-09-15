from kivymd.app import MDApp
from kivymd.uix.screen import MDScreen
from kivymd.uix.button import MDRaisedButton
from kivymd.uix.label import MDLabel
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.gridlayout import MDGridLayout
from kivymd.uix.card import MDCard
from kivy.uix.scrollview import ScrollView
from kivy.metrics import dp
from kivy.lang import Builder
from kivymd.uix.dialog import MDDialog
from models.game import Game

class HomeScreen(MDScreen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._app = MDApp.get_running_app()
        self.dialog = None
        self.build_ui()

    def build_ui(self):
        layout = MDBoxLayout(orientation='vertical', padding='10dp', spacing='10dp')
        
        # Título
        title = MDLabel(
            text="Bingo Cultural",
            halign="center",
            font_style="H4",
            size_hint_y=None,
            height='100dp'
        )
        layout.add_widget(title)
        
        # Categorías
        categories_scroll = ScrollView()
        categories_grid = MDGridLayout(cols=2, spacing='10dp', padding='10dp', size_hint_y=None)
        categories_grid.bind(minimum_height=categories_grid.setter('height'))
        
        categories = [
            ('Historia', 'history'),
            ('Cultura', 'book'),
            ('Deporte', 'soccer'),
            ('Ciencia', 'flask'),
            ('Arte', 'palette')
        ]
        
        for category, icon in categories:
            card = MDCard(
                orientation='vertical',
                padding='10dp',
                size_hint=(None, None),
                size=('150dp', '150dp')
            )
            
            card.add_widget(MDLabel(
                text=category,
                halign='center',
                font_style='H6'
            ))
            
            card.add_widget(MDRaisedButton(
                text="Jugar",
                on_release=lambda x, cat=category: self.start_game(cat),
                pos_hint={'center_x': 0.5}
            ))
            
            categories_grid.add_widget(card)
        
        categories_scroll.add_widget(categories_grid)
        layout.add_widget(categories_scroll)
        
        # Botones de acción
        action_layout = MDBoxLayout(spacing='10dp', size_hint_y=None, height='50dp')
        
        new_game_btn = MDRaisedButton(
            text="Nuevo Juego",
            on_release=self.start_new_game
        )
        
        settings_btn = MDRaisedButton(
            text="Configuración",
            on_release=self.show_settings
        )
        
        action_layout.add_widget(new_game_btn)
        action_layout.add_widget(settings_btn)
        layout.add_widget(action_layout)
        
        self.add_widget(layout)

    def start_game(self, category):
        self._app.current_game = self._app.game.create_card(category, "player1")
        self.manager.current = 'game'

    def start_new_game(self, *args):
        """Inicia un nuevo juego"""
        self._app.game = Game()
        self.manager.current = 'game'

    def show_settings(self, *args):
        """Muestra la pantalla de configuración"""
        self.manager.current = 'settings'

    def on_enter(self):
        """Se ejecuta cuando la pantalla se muestra"""
        # Actualizar la interfaz cuando se entra a la pantalla
        self.ids.score_label.text = f"Puntuación: {self._app.get_current_game().score if self._app.get_current_game() else 0}"

    @property
    def app(self):
        return self.manager.app 