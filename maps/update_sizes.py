# update_sizes.py
import os
import sys
import django
from PIL import Image

# Настройка Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from maps.models import GameMap

def update_all_sizes():
    maps = GameMap.objects.all()
    updated = 0
    
    print(f"📊 Найдено карт: {maps.count()}")
    print("=" * 50)
    
    for game_map in maps:
        try:
            if game_map.image and os.path.exists(game_map.image.path):
                with Image.open(game_map.image.path) as img:
                    width, height = img.size
                    
                    if game_map.width != width or game_map.height != height:
                        print(f"🔄 Обновляю '{game_map.name}': {game_map.width}x{game_map.height} -> {width}x{height}")
                        game_map.width = width
                        game_map.height = height
                        game_map.save()
                        updated += 1
                    else:
                        print(f"✅ '{game_map.name}': {width}x{height} (уже правильно)")
            else:
                print(f"⚠️ '{game_map.name}': нет изображения или файл не найден")
                
        except Exception as e:
            print(f"❌ Ошибка в '{game_map.name}': {e}")
    
    print("=" * 50)
    print(f"🎯 Обновлено: {updated} из {maps.count()} карт")
    print("💾 Для применения изменений перезапусти сервер")

if __name__ == '__main__':
    update_all_sizes()