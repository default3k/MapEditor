from django.urls import path
from . import views

app_name = 'clan'

urlpatterns = [
    path('', views.player_list, name='player_list'),
    path('players/', views.player_list, name='player_list'),
    path('players/add/', views.player_add, name='player_add'),
    path('players/<int:player_id>/', views.player_detail, name='player_detail'),
    path('players/<int:player_id>/edit/', views.player_edit, name='player_edit'),
    path('players/<int:player_id>/delete/', views.player_delete, name='player_delete'),
    
    path('sessions/', views.session_list, name='session_list'),
    path('sessions/add/', views.session_add, name='session_add'),
    path('sessions/<int:session_id>/edit/', views.session_edit, name='session_edit'),
    path('sessions/<int:session_id>/delete/', views.session_delete, name='session_delete'),
    
    path('rankings/', views.rankings, name='rankings'),
]