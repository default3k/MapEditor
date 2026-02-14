from django.db import models
from django.contrib.auth.models import User

class GameMap(models.Model):
    # УБИРАЕМ 'other' из выбора
    MODE_CHOICES = [
        ('random', 'Случайный бой'),
        ('attack_defense', 'Атака/Оборона'),
        ('encounter', 'Встречный бой'),
        ('assault', 'Штурм'),
        ('grand_battle', 'Генеральное сражение'),
        ('clash', 'Столкновение'),
    ]
    
    name = models.CharField(max_length=200)
    image = models.ImageField(upload_to='maps/')
    width = models.IntegerField(default=1000)
    height = models.IntegerField(default=1000)
    
    mode = models.CharField(
        max_length=20, 
        choices=MODE_CHOICES, 
        default='random',
        verbose_name='Режим игры'
    )
    
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.name
    
    def get_mode_display_name(self):
        """Красивое отображение режима"""
        display_names = {
            'random': '🎲 Случайный бой',
            'attack_defense': '⚔️ Атака/Оборона',
            'encounter': '🏁 Встречный бой',
            'assault': '💥 Штурм',
            'grand_battle': '👑 Генеральное сражение',
            'clash': '⚡ Столкновение',
        }
        return display_names.get(self.mode, self.get_mode_display())

class MapDrawing(models.Model):
    TOOL_CHOICES = [
        ('marker', 'Маркер'),
        ('polyline', 'Линия'),
        ('polygon', 'Область'),
        ('rectangle', 'Прямоугольник'),
        ('circle', 'Круг'),
        ('text', 'Текст'),
    ]
    
    game_map = models.ForeignKey(GameMap, on_delete=models.CASCADE, related_name='drawings')
    tool_type = models.CharField(max_length=20, choices=TOOL_CHOICES)
    color = models.CharField(max_length=7, default='#ff0000')
    coordinates = models.JSONField()
    label = models.CharField(max_length=100, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.get_tool_type_display()} на {self.game_map.name}"