from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.db.models import Q, Avg
from django.db import transaction
from .models import Player, DuelSession
from .forms import PlayerForm, DuelSessionForm

def player_list(request):
    """Список всех игроков клана"""
    Player.update_all_positions()
    players = Player.objects.filter(is_active=True).order_by('position')
    search_query = request.GET.get('search', '')
    
    if search_query:
        players = players.filter(
            Q(nickname__icontains=search_query) |
            Q(discord_nick__icontains=search_query)
        )
    
    total_players = players.count()
    total_battles = DuelSession.objects.count()
    avg_clan_damage = players.aggregate(avg=Avg('average_damage'))['avg'] or 0
    
    context = {
        'players': players,
        'search_query': search_query,
        'total_players': total_players,
        'total_battles': total_battles,
        'avg_clan_damage': round(avg_clan_damage),
        'clan_name': '2KLOX',
    }
    return render(request, 'clan/player_list.html', context)

def player_detail(request, player_id):
    """Детальная страница игрока"""
    player = get_object_or_404(Player, id=player_id)
    sessions = DuelSession.objects.filter(
        Q(player1=player) | Q(player2=player)
    ).select_related('player1', 'player2', 'winner').order_by('-session_date')
    
    # Статистика изменений урона
    damage_changes = []
    for session in sessions:
        if session.player1 == player and session.player1_damage_change != 0:
            damage_changes.append({
                'date': session.session_date,
                'change': session.player1_damage_change,
                'opponent': session.player2.nickname
            })
        elif session.player2 == player and session.player2_damage_change != 0:
            damage_changes.append({
                'date': session.session_date,
                'change': session.player2_damage_change,
                'opponent': session.player1.nickname
            })
    
    context = {
        'player': player,
        'sessions': sessions,
        'damage_changes': damage_changes,
    }
    return render(request, 'clan/player_detail.html', context)

def player_add(request):
    """Добавление нового игрока"""
    if request.method == 'POST':
        form = PlayerForm(request.POST)
        if form.is_valid():
            player = form.save(commit=False)
            player.position = 0
            player.save()
            Player.update_all_positions()
            messages.success(request, f'Игрок {player.nickname} успешно добавлен!')
            return redirect('clan:player_list')
    else:
        form = PlayerForm()
    
    return render(request, 'clan/player_form.html', {
        'form': form,
        'title': 'Добавить игрока'
    })

def player_edit(request, player_id):
    """Редактирование игрока"""
    player = get_object_or_404(Player, id=player_id)
    
    if request.method == 'POST':
        form = PlayerForm(request.POST, instance=player)
        if form.is_valid():
            form.save()
            Player.update_all_positions()
            messages.success(request, f'Данные игрока {player.nickname} обновлены!')
            return redirect('clan:player_detail', player_id=player.id)
    else:
        form = PlayerForm(instance=player)
    
    return render(request, 'clan/player_form.html', {
        'form': form,
        'title': f'Редактировать {player.nickname}',
        'player': player
    })

def session_list(request):
    """Список всех дуэльных сессий"""
    sessions = DuelSession.objects.all().select_related(
        'player1', 'player2', 'winner'
    ).order_by('-session_date')
    
    # Поиск по игроку
    player_filter = request.GET.get('player', '')
    if player_filter:
        sessions = sessions.filter(
            Q(player1__nickname__icontains=player_filter) |
            Q(player2__nickname__icontains=player_filter)
        )
    
    # Статистика
    total_sessions = sessions.count()
    total_changed = sessions.filter(position_changed=True).count()
    
    context = {
        'sessions': sessions,
        'player_filter': player_filter,
        'total_sessions': total_sessions,
        'total_changed': total_changed,
    }
    return render(request, 'clan/session_list.html', context)

def session_edit(request, session_id):
    """Редактирование сессии"""
    session = get_object_or_404(DuelSession, id=session_id)
    
    if request.method == 'POST':
        form = DuelSessionForm(request.POST, instance=session)
        if form.is_valid():
            with transaction.atomic():
                edited_session = form.save(commit=False)
                
                # Откатываем старые изменения
                old_player1 = Player.objects.get(id=session.player1.id)
                old_player2 = Player.objects.get(id=session.player2.id)
                
                # Откатываем старую статистику
                if session.winner:
                    if session.winner == session.player1:
                        old_player1.wins -= 1
                        old_player2.losses -= 1
                    else:
                        old_player2.wins -= 1
                        old_player1.losses -= 1
                
                old_player1.total_battles -= 1
                old_player2.total_battles -= 1
                
                if session.player1_damage_change != 0:
                    old_player1.average_damage -= session.player1_damage_change
                
                if session.player2_damage_change != 0:
                    old_player2.average_damage -= session.player2_damage_change
                
                old_player1.save()
                old_player2.save()
                
                # Применяем новые изменения
                player1 = edited_session.player1
                player2 = edited_session.player2
                
                edited_session.old_position_player1 = player1.position
                edited_session.old_position_player2 = player2.position
                
                if edited_session.player1_damage_change != 0:
                    player1.average_damage += edited_session.player1_damage_change
                
                if edited_session.player2_damage_change != 0:
                    player2.average_damage += edited_session.player2_damage_change
                
                if edited_session.winner:
                    if edited_session.winner == player1:
                        player1.wins += 1
                        player2.losses += 1
                    else:
                        player2.wins += 1
                        player1.losses += 1
                
                player1.total_battles += 1
                player2.total_battles += 1
                
                player1.save()
                player2.save()
                
                Player.update_all_positions()
                
                player1.refresh_from_db()
                player2.refresh_from_db()
                
                edited_session.new_position_player1 = player1.position
                edited_session.new_position_player2 = player2.position
                edited_session.position_changed = (
                    edited_session.old_position_player1 != edited_session.new_position_player1 or
                    edited_session.old_position_player2 != edited_session.new_position_player2
                )
                
                edited_session.save()
                
                messages.success(request, "Сессия обновлена")
                return redirect('clan:session_list')
    else:
        form = DuelSessionForm(instance=session)
    
    return render(request, 'clan/session_edit.html', {
        'form': form,
        'session': session
    })

def session_delete(request, session_id):
    """Удаление сессии"""
    session = get_object_or_404(DuelSession, id=session_id)
    
    if request.method == 'POST':
        with transaction.atomic():
            # Откатываем статистику
            player1 = session.player1
            player2 = session.player2
            
            if session.winner:
                if session.winner == player1:
                    player1.wins -= 1
                    player2.losses -= 1
                else:
                    player2.wins -= 1
                    player1.losses -= 1
            
            player1.total_battles -= 1
            player2.total_battles -= 1
            
            
            player1.save()
            player2.save()
            
            Player.update_all_positions()
            
            session.delete()
            messages.success(request, 'Сессия удалена')
        return redirect('clan:session_list')
    
    return render(request, 'clan/session_confirm_delete.html', {'session': session})

def session_add(request):
    """Добавление новой дуэльной сессии"""
    if request.method == 'POST':
        form = DuelSessionForm(request.POST)
        if form.is_valid():
            with transaction.atomic():
                session = form.save(commit=False)
                
                # Получаем игроков
                player1 = session.player1
                player2 = session.player2
                
                # Сохраняем старые позиции
                session.old_position_player1 = player1.position
                session.old_position_player2 = player2.position
                
                # Обновляем средний урон
                if session.player1_damage_change != 0:
                    player1.average_damage = session.player1_damage_change
                
                if session.player2_damage_change != 0:
                    player2.average_damage = session.player2_damage_change
                
                # Обновляем победы/поражения
                if session.winner:
                    if session.winner == player1:
                        player1.wins += 1
                        player2.losses += 1
                    else:
                        player2.wins += 1
                        player1.losses += 1
                
                # Увеличиваем счетчик битв
                player1.total_battles += 1
                player2.total_battles += 1
                
                # Сохраняем игроков
                player1.save()
                player2.save()
                
                # Пересчитываем позиции
                Player.update_all_positions()
                
                # Обновляем объекты в памяти
                player1.refresh_from_db()
                player2.refresh_from_db()
                
                # Сохраняем новые позиции
                session.new_position_player1 = player1.position
                session.new_position_player2 = player2.position
                
                # Проверяем, изменились ли позиции
                if (session.old_position_player1 != session.new_position_player1 or 
                    session.old_position_player2 != session.new_position_player2):
                    session.position_changed = True
                
                # СОХРАНЯЕМ СЕССИЮ (вместо session_edit)
                session.save()
                
                messages.success(request, "Сессия успешно записана")
                return redirect('clan:session_list')
    else:
        form = DuelSessionForm()
    
    return render(request, 'clan/session_form.html', {
        'form': form,
        'title': 'Записать дуэль'
    })

def rankings(request):
    """Рейтинговая таблица"""
    Player.update_all_positions()
    players = Player.objects.filter(is_active=True).order_by('position')
    top3 = players[:3]
    
    context = {
        'players': players,
        'top3': top3,
        'total_players': players.count(),
    }
    return render(request, 'clan/rankings.html', context)

def player_delete(request, player_id):  # Должен быть player_id, не pk
    """Удаление игрока"""
    player = get_object_or_404(Player, id=player_id)
    
    if request.method == 'POST':
        player.delete()
        messages.success(request, f'Игрок {player.nickname} удалён')
        return redirect('clan:player_list')
    
    return render(request, 'clan/player_confirm_delete.html', {'player': player})