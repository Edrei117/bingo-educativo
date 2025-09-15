"""
Pantalla de Estadísticas para el Bingo Educativo
"""
from kivymd.app import MDApp
from kivymd.uix.screen import MDScreen
from kivymd.uix.card import MDCard
from kivymd.uix.label import MDLabel
from kivymd.uix.button import MDRaisedButton, MDIconButton
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.gridlayout import MDGridLayout
from kivymd.uix.scrollview import ScrollView
from kivymd.uix.tab import MDTabsBase, MDTabs
from kivymd.uix.floatlayout import MDFloatLayout
from kivy.metrics import dp
from kivy.properties import StringProperty
from services.analytics_service import analytics, UserStats
from datetime import datetime

class StatsTab(MDFloatLayout, MDTabsBase):
    """Tab base para las estadísticas"""
    pass

class StatsScreen(MDScreen):
    """Pantalla de estadísticas del usuario"""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._app = MDApp.get_running_app()
        self.build_ui()
    
    def build_ui(self):
        """Construye la interfaz de usuario"""
        layout = MDBoxLayout(orientation='vertical', padding='10dp', spacing='10dp')
        
        # Header con título y botón de regreso
        header = MDBoxLayout(
            orientation='horizontal',
            size_hint_y=None,
            height='60dp',
            spacing='10dp'
        )
        
        back_btn = MDIconButton(
            icon='arrow-left',
            on_release=self.go_back
        )
        
        title = MDLabel(
            text="Mis Estadísticas",
            halign="center",
            font_style="H5",
            size_hint_x=0.8
        )
        
        header.add_widget(back_btn)
        header.add_widget(title)
        layout.add_widget(header)
        
        # Contenido principal con tabs
        self.tabs = MDTabs()
        self.tabs.add_widget(StatsTab(title="Resumen"))
        self.tabs.add_widget(StatsTab(title="Categorías"))
        self.tabs.add_widget(StatsTab(title="Progreso"))
        
        layout.add_widget(self.tabs)
        self.add_widget(layout)
    
    def on_enter(self):
        """Se ejecuta cuando la pantalla se muestra"""
        self.update_stats()
    
    def update_stats(self):
        """Actualiza las estadísticas mostradas"""
        # Limpiar contenido anterior
        for tab in self.tabs.tab_list:
            tab.clear_widgets()
        
        # Tab 1: Resumen general
        self.build_summary_tab()
        
        # Tab 2: Rendimiento por categoría
        self.build_categories_tab()
        
        # Tab 3: Progreso semanal
        self.build_progress_tab()
    
    def build_summary_tab(self):
        """Construye el tab de resumen"""
        tab = self.tabs.tab_list[0]
        scroll = ScrollView()
        content = MDBoxLayout(orientation='vertical', spacing='15dp', padding='10dp')
        
        # Estadísticas principales
        stats = analytics.user_stats
        weekly_stats = analytics.get_weekly_stats()
        
        # Card de resumen general
        summary_card = MDCard(
            orientation='vertical',
            padding='15dp',
            spacing='10dp'
        )
        
        summary_card.add_widget(MDLabel(
            text="Resumen General",
            halign="center",
            font_style="H6",
            bold=True
        ))
        
        stats_grid = MDGridLayout(cols=2, spacing='10dp')
        
        stats_data = [
            ("Juegos Totales", str(stats.total_games)),
            ("Puntuación Total", str(stats.total_score)),
            ("Promedio", f"{stats.average_score:.1f}"),
            ("Bingos Logrados", str(stats.bingos_achieved)),
            ("Respuestas Correctas", str(stats.total_correct)),
            ("Tiempo Total", f"{stats.total_play_time:.1f} min"),
            ("Esta Semana", str(weekly_stats['games_played'])),
            ("Bingos Semana", str(weekly_stats['bingos_achieved']))
        ]
        
        for label, value in stats_data:
            stats_grid.add_widget(MDLabel(text=label, size_hint_x=0.6))
            stats_grid.add_widget(MDLabel(text=value, halign="right", bold=True))
        
        summary_card.add_widget(stats_grid)
        content.add_widget(summary_card)
        
        # Card de categoría favorita
        if stats.favorite_category:
            favorite_card = MDCard(
                orientation='vertical',
                padding='15dp'
            )
            
            favorite_card.add_widget(MDLabel(
                text=f"Categoría Favorita: {stats.favorite_category}",
                halign="center",
                font_style="H6"
            ))
            
            content.add_widget(favorite_card)
        
        scroll.add_widget(content)
        tab.add_widget(scroll)
    
    def build_categories_tab(self):
        """Construye el tab de categorías"""
        tab = self.tabs.tab_list[1]
        scroll = ScrollView()
        content = MDBoxLayout(orientation='vertical', spacing='15dp', padding='10dp')
        
        category_performance = analytics.get_category_performance()
        
        for category, stats in category_performance.items():
            card = MDCard(
                orientation='vertical',
                padding='15dp',
                spacing='10dp'
            )
            
            card.add_widget(MDLabel(
                text=category.title(),
                halign="center",
                font_style="H6",
                bold=True
            ))
            
            stats_layout = MDBoxLayout(orientation='vertical', spacing='5dp')
            
            stats_text = f"""
            Juegos: {stats['games']}
            Puntuación Total: {stats['total_score']}
            Promedio: {stats.get('avg_score', 0):.1f}
            Precisión: {stats.get('accuracy', 0):.1f}%
            Bingos: {stats['bingos']}
            """
            
            stats_layout.add_widget(MDLabel(
                text=stats_text,
                halign="left"
            ))
            
            card.add_widget(stats_layout)
            content.add_widget(card)
        
        scroll.add_widget(content)
        tab.add_widget(scroll)
    
    def build_progress_tab(self):
        """Construye el tab de progreso"""
        tab = self.tabs.tab_list[2]
        scroll = ScrollView()
        content = MDBoxLayout(orientation='vertical', spacing='15dp', padding='10dp')
        
        weekly_stats = analytics.get_weekly_stats()
        
        # Card de progreso semanal
        progress_card = MDCard(
            orientation='vertical',
            padding='15dp',
            spacing='10dp'
        )
        
        progress_card.add_widget(MDLabel(
            text="Progreso de la Semana",
            halign="center",
            font_style="H6",
            bold=True
        ))
        
        progress_data = [
            ("Juegos Jugados", str(weekly_stats['games_played'])),
            ("Puntuación Total", str(weekly_stats['total_score'])),
            ("Bingos Logrados", str(weekly_stats['bingos_achieved'])),
            ("Tiempo Jugado", f"{weekly_stats['play_time_hours']:.1f} horas")
        ]
        
        for label, value in progress_data:
            row = MDBoxLayout(orientation='horizontal', spacing='10dp')
            row.add_widget(MDLabel(text=label, size_hint_x=0.7))
            row.add_widget(MDLabel(text=value, halign="right", bold=True))
            progress_card.add_widget(row)
        
        content.add_widget(progress_card)
        
        # Botón para reiniciar estadísticas
        reset_btn = MDRaisedButton(
            text="Reiniciar Estadísticas",
            on_release=self.reset_stats,
            pos_hint={'center_x': 0.5}
        )
        
        content.add_widget(reset_btn)
        
        scroll.add_widget(content)
        tab.add_widget(scroll)
    
    def reset_stats(self, *args):
        """Reinicia las estadísticas del usuario"""
        # Aquí se podría agregar un diálogo de confirmación
        analytics.sessions.clear()
        analytics.user_stats = UserStats()
        analytics.save_data()
        self.update_stats()
    
    def go_back(self, *args):
        """Regresa a la pantalla anterior"""
        self.manager.current = 'home'
