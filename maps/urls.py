from django.urls import path
from . import views

urlpatterns = [
    path('', views.map_list, name='map_list'),
    path('<int:map_id>/', views.map_detail, name='map_detail'),
    path('<int:map_id>/test/', views.test_view, name='test_map'),
    path('<int:map_id>/test-image/', views.test_image, name='test_image'),
]