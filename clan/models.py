from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from datetime import datetime

class Player(models.Model):
    """Модель игрока клана"""
    nickname = models.CharField('Ник в игре', max_length=100, unique=True)
    discord_nick = models.CharField('Discord', max_length=100, blank=True, null=True)
    
    # Только то, что нужно вводить
    average_damage = models.IntegerField('Средний урон', default=0)
    commander_notes = models.TextField('Заметки командира', blank=True)
    
    # Автоматические поля
    position = models.IntegerField('Позиция в рейтинге', default=0)
    total_battles = models.IntegerField('Всего боев', default=0)
    
    # Для истории позиций
    position_history = models.JSONField('История позиций', default=list, blank=True)
    
    # Статистика
    wins = models.IntegerField('Побед', default=0)
    losses = models.IntegerField('Поражений', default=0)

    # Метаданные
    created_at = models.DateTimeField('Дата добавления', auto_now_add=True)
    updated_at = models.DateTimeField('Обновлено', auto_now=True)
    is_active = models.BooleanField('Активный игрок', default=True)
    
    class Meta:
        verbose_name = 'Игрок'
        verbose_name_plural = 'Игроки'
        ordering = ['-average_damage']
    
    def win_rate(self):
        """Процент побед"""
        if self.total_battles == 0:
            return 0
        return round((self.wins / self.total_battles) * 100, 1)
    
    def __str__(self):
        return f"{self.nickname} (урон: {self.average_damage})"
    
    def save(self, *args, **kwargs):
        """Автоматическое сохранение истории позиций"""
        if self.pk:
            old = Player.objects.get(pk=self.pk)
            if old.position != self.position:
                history_entry = {
                    'date': datetime.now().isoformat(),
                    'old_position': old.position,
                    'new_position': self.position
                }
                if not self.position_history:
                    self.position_history = []
                self.position_history.append(history_entry)
                if len(self.position_history) > 20:
                    self.position_history = self.position_history[-20:]
        
        super().save(*args, **kwargs)
    
    def get_rank_emoji(self):
        """Эмодзи для ранга"""
        if self.position == 1:
            return "👑"
        elif self.position <= 3:
            return "🏆"
        elif self.position <= 5:
            return "⭐"
        elif self.position <= 10:
            return "💫"
        else:
            return "⚔️"

    @classmethod
    def update_all_positions(cls):
        """Обновляет позиции всех игроков на основе среднего урона"""
        players = cls.objects.filter(is_active=True).order_by('-average_damage')
        for index, player in enumerate(players, start=1):
            if player.position != index:
                player.position = index
                cls.objects.filter(pk=player.pk).update(position=index)


class DuelSession(models.Model):
    """Модель дуэльной сессии"""
    player1 = models.ForeignKey(
        Player,
        on_delete=models.CASCADE,
        related_name='sessions_as_player1'
    )
    player2 = models.ForeignKey(
        Player,
        on_delete=models.CASCADE,
        related_name='sessions_as_player2'
    )

    # Танки
    tank1 = models.CharField('Танк игрока 1', max_length=100, default='Не указан')
    tank2 = models.CharField('Танк игрока 2', max_length=100, default='Не указан')

    # Урон в этом бою
    player1_battle_damage = models.IntegerField('Урон игрока 1', default=0)
    player2_battle_damage = models.IntegerField('Урон игрока 2', default=0)

    # Изменение среднего урона
    player1_damage_change = models.IntegerField('Изменение урона P1', default=0)
    player2_damage_change = models.IntegerField('Изменение урона P2', default=0)

    # Победитель
    winner = models.ForeignKey(
        Player,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='won_sessions'
    )

    # Позиции ДО
    old_position_player1 = models.IntegerField('Позиция P1 до', default=0)
    old_position_player2 = models.IntegerField('Позиция P2 до', default=0)

    # Позиции ПОСЛЕ
    new_position_player1 = models.IntegerField('Позиция P1 после', default=0)
    new_position_player2 = models.IntegerField('Позиция P2 после', default=0)

    position_changed = models.BooleanField('Позиции изменились', default=False)

    session_date = models.DateTimeField('Дата сессии', auto_now_add=True)
    notes = models.TextField('Заметки', blank=True)

    class Meta:
        verbose_name = 'Дуэльная сессия'
        verbose_name_plural = 'Дуэльные сессии'
        ordering = ['-session_date']

    def __str__(self):
        return f"{self.player1.nickname} vs {self.player2.nickname}"

    def apply_damage_updates(self):
        """Применить изменения после сессии"""
        # Обновляем средний урон
        if self.player1_damage_change != 0:
            self.player1.average_damage += self.player1_damage_change
        
        if self.player2_damage_change != 0:
            self.player2.average_damage += self.player2_damage_change
        
        # Обновляем победы/поражения
        if self.winner:
            if self.winner == self.player1:
                self.player1.wins += 1
                self.player2.losses += 1
            else:
                self.player2.wins += 1
                self.player1.losses += 1
        
        # Увеличиваем счетчик битв
        self.player1.total_battles += 1
        self.player2.total_battles += 1
        
        # Сохраняем игроков
        self.player1.save()
        self.player2.save()
        
        # Пересчитываем позиции
        Player.update_all_positions()
        
        # Обновляем объекты в памяти
        self.player1.refresh_from_db()
        self.player2.refresh_from_db()
        
        # Сохраняем новые позиции
        self.new_position_player1 = self.player1.position
        self.new_position_player2 = self.player2.position
        
        if (self.old_position_player1 != self.new_position_player1 or 
            self.old_position_player2 != self.new_position_player2):
            self.position_changed = True