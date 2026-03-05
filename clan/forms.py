from django import forms
from .models import Player, DuelSession


class PlayerForm(forms.ModelForm):
    class Meta:
        model = Player
        fields = [
            'nickname',
            'discord_nick',
            'average_damage',
            'commander_notes',
            'is_active'
        ]


class DuelSessionForm(forms.ModelForm):
    class Meta:
        model = DuelSession
        fields = [
            'player1',
            'player2',
            'tank1',
            'tank2',
            'player1_battle_damage',
            'player2_battle_damage',
            'player1_damage_change',
            'player2_damage_change',
            'winner',
            'notes'
        ]

    def clean(self):
        cleaned_data = super().clean()
        player1 = cleaned_data.get('player1')
        player2 = cleaned_data.get('player2')

        if player1 and player2 and player1 == player2:
            raise forms.ValidationError("Игроки не могут быть одинаковыми")

        return cleaned_data