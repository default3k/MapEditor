from django import forms
from .models import GameMap
from PIL import Image

class GameMapAdminForm(forms.ModelForm):
    class Meta:
        model = GameMap
        fields = ['name', 'image', 'mode', 'created_by']
    
    def save(self, commit=True):
        instance = super().save(commit=False)
        
        # Определяем размеры изображения
        if self.cleaned_data.get('image'):
            try:
                # Открываем изображение из памяти
                image_file = self.cleaned_data['image']
                
                # Перематываем файл в начало
                image_file.seek(0)
                
                # Открываем с помощью Pillow
                img = Image.open(image_file)
                instance.width, instance.height = img.size
                
                # Возвращаем указатель файла в начало
                image_file.seek(0)
                img.close()
                
            except Exception as e:
                print(f"Ошибка при определении размеров: {e}")
                instance.width = 1000
                instance.height = 1000
        
        if commit:
            instance.save()
        
        return instance