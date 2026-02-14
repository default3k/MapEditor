from django.contrib import admin
from .models import GameMap, MapDrawing

@admin.register(GameMap)
class GameMapAdmin(admin.ModelAdmin):
    list_display = ['name', 'get_mode_display', 'width', 'height', 'created_by', 'created_at']
    list_filter = ['mode', 'created_at', 'created_by']
    search_fields = ['name', 'created_by__username']
    readonly_fields = ['created_at']
    
    fieldsets = (
        ('Основная информация', {
            'fields': ('name', 'image', 'mode', 'created_by')
        }),
        ('Размеры (можно оставить 1000×1000, определятся автоматически при открытии)', {
            'fields': ('width', 'height')
        }),
        ('Даты', {
            'fields': ('created_at',)
        }),
    )
    
    def get_mode_display(self, obj):
        return obj.get_mode_display()
    get_mode_display.short_description = 'Режим'

@admin.register(MapDrawing)
class MapDrawingAdmin(admin.ModelAdmin):
    list_display = ['game_map', 'tool_type', 'color', 'created_by', 'created_at']
    list_filter = ['tool_type', 'created_at']
    search_fields = ['game_map__name', 'label']
    readonly_fields = ['created_at']
    
    fieldsets = (
        ('Основное', {
            'fields': ('game_map', 'tool_type', 'color', 'label')
        }),
        ('Данные', {
            'fields': ('coordinates',)
        }),
        ('Автор и дата', {
            'fields': ('created_by', 'created_at')
        }),
    )