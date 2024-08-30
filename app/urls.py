from django.urls import path, include
from . import views

urlpatterns = [
    path("profile/", views.Profile, name = "Profile"),
    path("addFriend/<str:name>/", views.addFriend, name = "addFriend"),
    path("game_state/", views.GameState, name= "GameState"),
    path("update_position/<int:row>/<int:col>/", views.update_position, name="update_position"),
    path("sign_up/", views.signup, name= "signup"),
    path("login/", views.login, name= "login"),
    path("csrf_token/", views.get_csrf_token, name= "csrftoken"),
    path("clearTrace/", views.clear_trace, name = "clearTrace"),
    # path('Game/<str:room_code>/', views.Game, name='Game'),
    path('Challenge/',views.Challenge, name='Challenge'),
    path('acceptChallenge/<str:name>/', views.acceptChallenge, name='acceptChallenge'),
    path('createChallenge/<str:name>/', views.createChallenge, name='createChallenge'),
    path('cancelChallenge/<str:name>/', views.cancelChallenge, name='createChallenge'),
    path('randomChallenge/', views.randomChallenge, name='randomChallenge'),
    path('endWait/', views.endWait, name='endWait'),
    path("game_state_GP/", views.GameState_GP, name= "GameState"),
    path("update_position_GP/<str:room_code>/<int:row>/<int:col>/", views.update_position_GP, name="update_position"),
    path('clearGame/<int:win>/<int:p>/', views.clearGame, name='clearGame'),
    path('sendMessage/<int:p>/<str:message>/', views.send_Message, name='send_Message'),
    path('ai_agent_move/', views.update_from_AI, name='update_from_ai'),
]
