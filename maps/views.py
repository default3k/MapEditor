from django.shortcuts import render, get_object_or_404
from .models import GameMap

def map_list(request):
    maps = GameMap.objects.all()
    
    search_query = request.GET.get('search', '')
    mode_filter = request.GET.get('mode', '')
    sort_by = request.GET.get('sort', 'name')
    
    if search_query:
        maps = maps.filter(name__icontains=search_query)
    
    if mode_filter:
        maps = maps.filter(mode=mode_filter)
    
    if sort_by == 'name':
        maps = maps.order_by('name')
    elif sort_by == 'newest':
        maps = maps.order_by('-created_at')
    elif sort_by == 'oldest':
        maps = maps.order_by('created_at')
    
    mode_choices = GameMap.MODE_CHOICES
    
    context = {
        'maps': maps,
        'search_query': search_query,
        'mode_filter': mode_filter,
        'sort_by': sort_by,
        'mode_choices': mode_choices,
        'total_maps': maps.count(),
    }
    
    return render(request, 'maps/map_list.html', context)

def map_detail(request, map_id):
    game_map = get_object_or_404(GameMap, id=map_id)
    return render(request, 'maps/map_detail.html', {'map': game_map})

def test_view(request, map_id):
    game_map = get_object_or_404(GameMap, id=map_id)
    return render(request, 'maps/test.html', {'map': game_map})

def test_image(request, map_id):
    game_map = get_object_or_404(GameMap, id=map_id)
    return render(request, 'maps/test_image.html', {'map': game_map})