from django.contrib import admin
from .models import Player, DuelSession


@admin.register(Player)
class PlayerAdmin(admin.ModelAdmin):
    list_display = [
        'position',
        'nickname',
        'average_damage',
        'total_battles',
        'is_active'
    ]
    list_display_links = ['nickname']
    list_editable = ['average_damage', 'is_active']
    search_fields = ['nickname', 'discord_nick']
    list_filter = ['is_active']
    ordering = ['position']
    readonly_fields = ['position', 'total_battles', 'position_history']

    fieldsets = (
        ('Основная информация', {
            'fields': ('nickname', 'discord_nick', 'is_active')
        }),
        ('Рейтинг', {
            'fields': ('position', 'average_damage', 'commander_notes')
        }),
        ('Статистика', {
            'fields': ('total_battles',)
        }),
        ('История', {
            'fields': ('position_history',),
            'classes': ('collapse',)
        })
    )


@admin.register(DuelSession)
class DuelSessionAdmin(admin.ModelAdmin):
    list_display = [
        'session_date',
        'player1',
        'player2',
        'tank1',
        'tank2',
        'player1_battle_damage',
        'player2_battle_damage',
        'player1_damage_change',
        'player2_damage_change',
        'winner',
        'position_changed'
    ]

    list_filter = ['session_date', 'position_changed']
    search_fields = ['player1__nickname', 'player2__nickname']
    readonly_fields = [
        'old_position_player1',
        'old_position_player2',
        'new_position_player1',
        'new_position_player2'
    ]