from django.db import models

pos_dict = {}

def get_position(session_id):
    if session_id in pos_dict:
        return pos_dict[session_id]
    else:
        return [[0]*6 for i in range(9)]

def set_position(session_id, position_array):
    pos_dict[session_id] = position_array


###############################      User Model      ###############################

from django.db import models
from django.contrib.auth.models import AbstractUser, Group, Permission

class User(AbstractUser):
    games_played = models.IntegerField(default=0)
    games_won = models.IntegerField(default=0)
    groups = models.ManyToManyField(Group, blank=True, related_name='custom_user_set')
    user_permissions = models.ManyToManyField(Permission, blank=True, related_name='custom_user_set')

class Friends(models.Model):
    user1 = models.ForeignKey(User, on_delete=models.CASCADE, related_name='friends_as_user1')
    user2 = models.ForeignKey(User, on_delete=models.CASCADE, related_name='friends_as_user2')
    games_played_between = models.IntegerField(default=0)
    games_won_by_user1 = models.IntegerField(default=0)
    games_won_by_user2 = models.IntegerField(default=0)
    
    class Meta:
        unique_together = ['user1', 'user2']  # Ensure uniqueness of friendships


###############################      Multiplayer_Global      ###############################
chat_diary = {}
def set_chat(id,cht):
    chat_diary[id] = cht


class ChallengeQueue(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.user.username

class FriendlyChQueue(models.Model):
    p1 = models.ForeignKey(User, related_name='p1', on_delete=models.CASCADE)
    p2 = models.ForeignKey(User, related_name='p2', on_delete=models.CASCADE)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['p1', 'p2']
    

class RunningChallenge(models.Model):
    player1 = models.ForeignKey(User, related_name='player1', on_delete=models.CASCADE)
    player2 = models.ForeignKey(User, related_name='player2', on_delete=models.CASCADE)
    room_name = models.CharField(max_length=8)

    class Meta:
        unique_together = ['player1', 'player2']

