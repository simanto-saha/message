from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('login/', views.view_login, name='view_login'),
    path('signup/', views.signup, name='signup'),
    path('logout/', views.view_logout, name='view_logout'),
    path('connect/', views.view_connect, name='view_connect'),
    path('send-request/<int:user_id>/', views.send_request, name='send_request'),
    path('accept-request/<int:request_id>/', views.accept_request, name='accept_request'),
    path('reject-request/<int:request_id>/', views.reject_request, name='reject_request'),
    path('chat/<int:friend_id>/', views.chat_view, name='chat_view'),
    path('api/messages/<int:friend_id>/', views.get_messages, name='get_messages'),
]