from django.contrib import admin

# Register your models here.
from .models import User, Friends,ChallengeQueue, FriendlyChQueue, RunningChallenge

admin.site.register(User)
admin.site.register(Friends)
admin.site.register(ChallengeQueue)
admin.site.register(FriendlyChQueue)
admin.site.register(RunningChallenge)
