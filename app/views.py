from django.shortcuts import render
from django.http import HttpResponse, JsonResponse
from .models import *
from django.views.decorators.csrf import ensure_csrf_cookie
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth import login as auth_login

from rest_framework.response import Response
from rest_framework.authtoken.models import Token
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth import authenticate
from django.contrib.auth import login as auth_login
from .forms import CustomUserCreationForm
from django.views.decorators.csrf import csrf_exempt
from django.middleware.csrf import get_token
import json

from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse, JsonResponse
from django.template import loader
from .models import User, Friends
from .models import ChallengeQueue, FriendlyChQueue, RunningChallenge
from .models import get_position, set_position, pos_dict, set_chat, chat_diary
import time, random, string
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
import json
from django.db.models import Q
from django.contrib.auth.decorators import login_required


###############################      ProfilePage      ###############################

# Create your views here.
# @login_required(login_url='login')
from rest_framework.decorators import authentication_classes, permission_classes
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework.authtoken.models import Token

def find_User(req):
    authorization_header = req.headers.get("Authorization")
    _, token = authorization_header.split()
    authentication = TokenAuthentication()
    user, _ = authentication.authenticate_credentials(token)

    return user

@authentication_classes([])
@permission_classes([IsAuthenticated])
def Profile(request):
    
    authorization_header = request.headers.get("Authorization")
    _, token = authorization_header.split()
    authentication = TokenAuthentication()
    user, _ = authentication.authenticate_credentials(token)
    print(user)
    
    friends_as_user1 = Friends.objects.filter(user1=user)
    friends_as_user2 = Friends.objects.filter(user2=user)

    friends = []
    for friend in friends_as_user1:
        name = friend.user2.username
        games_won = friend.games_won_by_user1
        games_won_by_friend = friend.games_won_by_user2
        games_played = friend.games_played_between

        friends.append({
            'name': name,
            'games_won': games_won,
            'games_won_by_friend': games_won_by_friend,
            'games_played': games_played
        })
    
    for friend in friends_as_user2:
        name = friend.user1.username
        games_won = friend.games_won_by_user2
        games_won_by_friend = friend.games_won_by_user1
        games_played = friend.games_played_between

        friends.append({
            'name': name,
            'games_won': games_won,
            'games_won_by_friend': games_won_by_friend,
            'games_played': games_played
        })

    data = {
        'user': {
            'username': user.username,
            'games_won': user.games_won,
            'games_played': user.games_played,
            'wp': '%.2f' % (user.games_won * 100 / user.games_played),
        },
        'friend_list': friends,
    }

    print(data)
    return JsonResponse(data)

def addFriend(request, name):
    user = find_User(request)
    print(name)

    if(name == user.username):
        return JsonResponse({"success": 1, "message": "Hey! You are already your own friend."})

    try:
        friend = User.objects.get(username = name)
        print(friend)
    except:
        friend = []

    if(friend):
        pair = Friends.objects.filter((Q(user1 = user) & Q(user2 = friend)) | (Q(user1 = friend) & Q(user2 = user))).first()
        if(pair):
            return JsonResponse({"success": 1, "message": "Already in Friend List."})
        else:
            Friends.objects.create(user1= user, user2 = friend)
            return JsonResponse({"success": 1, "message": "Added to Friend List."})
    else:
        return JsonResponse({"success": 0, "message": "User does not exist."})

###############################      GamePage(single player)      ###############################

# @ensure_csrf_cookie
def GameState(request):
    
    session_id = request.session.session_key
    print(request)
    print(request.session)
    print(request.session.session_key)
    print(session_id)

    if(session_id in pos_dict.keys()):
        position_array = get_position(session_id)
    else:
        request.session.save()
        session_id = request.session.session_key
        print(session_id)
        position_array = [[0]*6 for i in range(9)]
        set_position(session_id, position_array)

    data = {'session_id':session_id,
            'Position': position_array, 
            'move': num_move(session_id),
            'win': win(session_id)}

    return JsonResponse(data)


# @ensure_csrf_cookie
def update_position(request, row, col):

    print("hii")
    # session_id = request.session.session_key
    session_id = request.headers['Content-Type']
    print(session_id, row, col)

    position = pos_dict[session_id]
    move_num = num_move(session_id)

    if(move_num%2 == 0):
        if(position[row][col]<0):
            pass
        add(row, col, 1, session_id)
    else:
        if(position[row][col]>0):
            pass
        add(row, col, -1, session_id)


    position_array = get_position(session_id)

    data = {'Position': position_array, 
            'move': num_move(session_id),
            'win': win(session_id)}
    
    return JsonResponse(data)

columns = 6
rows = 9

def num_move(request):
    session_id = request
    position = pos_dict[session_id]
    sum=0
    for i in range(rows):
        for j in range(columns):
            sum+= abs(position[i][j])
    
    return sum


def mx(row,col):
    if((row==0 or row==rows-1) and (col==0 or col==columns-1)):
        return 1
    elif((row==0 or row==rows-1) or (col==0 or col==columns-1)):
        return 2
    else:
        return 3

def reaction(row,col,player, id):
    session_id = id
    position = pos_dict[session_id]
    # position = Position
    position[row][col] = 0
    add(row-1,col,player,id)
    add(row+1,col,player,id)
    add(row,col-1,player,id)
    add(row,col+1,player,id)


def add(row,col,player,id):
    session_id = id
    position = pos_dict[session_id]
    # position = Position

    if(row<0 or row>=rows or col<0 or col>=columns):
        return None
    if(position[row][col] == 0):
        position[row][col] = player
    elif(abs(position[row][col]) < mx(row,col)):
        position[row][col] = (abs(position[row][col])+1)*player
    else:
        reaction(row,col,player,id)


def win(request):
    session_id = request
    position = pos_dict[session_id]
    # position = Position

    if num_move(request)<=2:
        return False

    p1=0
    p2=0
    for i in range(rows):
        for j in range(columns):
            if (position[i][j] > 0):
                p1+=1
            elif(position[i][j] < 0):
                p2+=1
    
    if(p1==0):
        # print("Player 2 has won!!")
        return 2
    elif(p2==0):
        # print("Player 1 has won!!")
        return 1
    
    return False


###############################      signup/login      ###############################


def get_csrf_token(request):
    csrf_token = get_token(request)
    print(csrf_token)
    return JsonResponse({'csrfToken': csrf_token})

@csrf_exempt
def signup(request):
    
    if request.method == 'POST':
        data = json.loads(request.body.decode('utf-8'))
        print(request.body)
        print(data)
        form = CustomUserCreationForm(data)
        print(request.POST)
        

        if form.is_valid():
            user = form.save()
            token, created = Token.objects.get_or_create(user=user)
            auth_login(request, user)
            return JsonResponse({'success': True, 'message': 'Signup successful!', 'token': token.key})
        else:
            return JsonResponse({'success': False, 'errors': form.errors}, status=200)
    else:
        form = CustomUserCreationForm()

    return render(request, 'signup.html', {'form': form})


@csrf_exempt
def login(request):

    if request.method == 'POST':
        data = json.loads(request.body.decode('utf-8'))
        print(data)
        username = data['username']
        password = data['password']

        user = authenticate(request, username=username, password=password)
        
        if(user):
            auth_login(request, user)
            token, _ = Token.objects.get_or_create(user=user)
            return JsonResponse({'success': True, 'message': 'Login successful', 'token': token.key}, status=200)
        else:
            return JsonResponse({'success': False, 'errors': 'Invalid credentials'}, status=200)

    else:
        form = AuthenticationForm()
    return render(request, 'login.html', {'form': form})


###############################      Multiplayer_Global      ###############################
###############################      Challange Page      ###############################

# @login_required(login_url='login')
def Challenge(request):
    current_user = find_User(request)

    print(current_user.username)
    friends_as_user1 = Friends.objects.filter(user1=current_user)
    friends_as_user2 = Friends.objects.filter(user2=current_user)

    friends = []
    for friend in friends_as_user1:
        friend_name = friend.user2.username
        games_won = friend.games_won_by_user1
        games_lost = friend.games_won_by_user2
        games_played = friend.games_played_between

        friends.append({
            'name': friend_name,
            'won': games_won,
            'lost': games_lost,
            'games': games_played
        })

    for friend in friends_as_user2:
        friend_name = friend.user1.username
        games_won = friend.games_won_by_user2
        games_lost = friend.games_won_by_user1
        games_played = friend.games_played_between

        friends.append({
            'name': friend_name,
            'won': games_won,
            'lost': games_lost,
            'games': games_played
        })
    
    friendly_challenge_queue = []
    fr_ch_Q = FriendlyChQueue.objects.filter(p2 = current_user).order_by('timestamp')
    
    for friend in fr_ch_Q:
        friend_name = friend.p1.username
        friendly_challenge_queue.append({
            'name': friend_name,
        })

    context = {
        'username': current_user.username,
        'friends': friends,
        'received_challenges': friendly_challenge_queue,
    }

    print(context)
    return JsonResponse(context)


def createChallenge(request, name):
    current_user = find_User(request)
    opponent = User.objects.get(username = name)
    
    FriendlyChQueue.objects.create(p1=current_user, p2 = opponent)
    # response_data = {'pairing_z': True}
    # print(response_data)
    # print("Challenge created for", current_user, name)
    # return HttpResponse(json.dumps(response_data), content_type = 'application/json')
    return JsonResponse({'success': 1})

def cancelChallenge(request, name):
    current_user = find_User(request)
    opponent = User.objects.get(username = name)
    user_queue = FriendlyChQueue.objects.filter(Q(p1 = current_user) | Q(p2 = current_user)).order_by('timestamp')
    user_queue.delete()
    
    return JsonResponse({'success': 1})

def acceptChallenge(request, name):
    opponent = User.objects.get(username = name)
    current_user = find_User(request)
    
    opponent_queue = FriendlyChQueue.objects.filter(p1 = opponent).order_by('timestamp')
    opponent_queue.delete()
    user_queue = FriendlyChQueue.objects.filter(Q(p1 = current_user) | Q(p2 = current_user)).order_by('timestamp')
    user_queue.delete()
    room_code = ''.join(random.choice(string.ascii_letters) for _ in range(8))
    RunningChallenge.objects.create(player1=opponent, player2=current_user, room_name=room_code)

    if current_user in pos_dict.keys():
        position_array = get_position(current_user)
    else:
        position_array = [[0] * 6 for _ in range(9)]
        set_position(current_user, position_array)
        set_position(opponent, position_array)
        cht = []                ##
        set_chat(current_user, cht)         ##
        set_chat(opponent, cht)             ##
    
    channel_layer = get_channel_layer()
    async_to_sync(channel_layer.group_send)(
        'random_challenge',
        {
            'type': 'game_state_update',
            'message': 'You have been paired with another player.',
            'player1_name': opponent.username,
            'player2_name': current_user.username,
            'room_code' : room_code
        }
    )

    print("redirecting Player 2")
    return redirect('/Game/' + room_code + '/')


def randomChallenge(request):
    current_user = find_User(request)
    challenge_queue = ChallengeQueue.objects.all().order_by('timestamp')

    if challenge_queue.exists():
        opponent = challenge_queue.first().user
        challenge_queue.first().delete()
        room_code = ''.join(random.choice(string.ascii_letters) for _ in range(8))
        RunningChallenge.objects.create(player1=opponent, player2=current_user, room_name=room_code)

        if current_user in pos_dict.keys():
            position_array = get_position(current_user)
        else:
            position_array = [[0] * 6 for _ in range(9)]
            set_position(current_user, position_array)
            set_position(opponent, position_array)
            cht = []                ##
            set_chat(current_user, cht)         ##
            set_chat(opponent, cht)             ##

        # Send message to the other player's WebSocket
        print(opponent.username, room_code)
        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(
            'random_challenge',
            {
                'type': 'game_state_update',
                'message': 'You have been paired with another player.',
                'player1_name': opponent.username,
                'player2_name': current_user.username,
                'room_code' : room_code
            }
        )

        print("redirecting Player 2")
        return redirect('/Game/' + room_code + '/')
    else:
        ChallengeQueue.objects.create(user=current_user)
        # Update the HTML template to display the endWait button instead of randomChallenge button
        # context = {
        #     'pairing': pairing
        # }
        response_data = {'pairing': True}
        print(response_data)
        print("response to player1")
        return HttpResponse(json.dumps(response_data), content_type = 'application/json')


def endWait(request):
    current_user = find_User(request)
    
    challenge_queue = ChallengeQueue.objects.filter(user=current_user)
    if challenge_queue.exists():
        challenge_queue.delete()

    return JsonResponse({'success': 1})

def createMatch(request):
    if session_id in pos_dict.keys():
        position_array = get_position(session_id)
    else:
        request.session.save()
        session_id = request.session.session_key
        position_array = [[0]*6 for i in range (9)]
        set_position(session_id, position_array)


###############################      GamePage(Global Game)      ###############################
def GameState_GP(request):
    id = find_User(request)

    q = RunningChallenge.objects.filter(Q(player1 = id) | Q(player2 = id))

    if(id == q.first().player1):
        player = 0
        oppnt = q.first().player2
    else:
        player = 1
        oppnt = q.first().player1

    position_array = pos_dict[id]

    room_code = q.first().room_name
    data = {
        'room_code': room_code,
        'p' : player,
        'user_data' : [id.username, id.games_won, id.games_played],
        'opp_data' : [oppnt.username, oppnt.games_won, oppnt.games_played],
        'position': position_array,
        'move': num_move(id),
        'win': win(id),
        'conv': chat_diary[id],
    }

    print(data)
    return JsonResponse(data)


def update_position_GP(request, room_code, row, col):

    id = find_User(request)

    position = pos_dict[id]
    move_num = num_move(id)

    if(move_num%2 == 0):
        if(position[row][col]<0):
            pass
        add(row, col, 1, id)
    else:
        if(position[row][col]>0):
            pass
        add(row, col, -1, id)

    position_array = pos_dict[id]       # get_position(id)


    channel_layer = get_channel_layer()
    async_to_sync(channel_layer.group_send)(
        'game_' + room_code,
        {
            'type': 'position_update',
            'message': 'update',
            'lastmove': [row, col],
            'position': position_array,
            'move': num_move(id),
            'win': win(id),
            'conv': chat_diary[id],
        }
    )

    data = {'Position': position_array, 
            'move': num_move(id),
            'win': win(id)}
    
    print(data)
    return JsonResponse(data)


def clearGame(request,win,p):
    print(win, p)
    id = find_User(request)
    # id = request.user
    player = id.username
    print("erased", win, p)

    position = pos_dict[id]
    for i in range(rows):
        for j in range(columns):
            position[i][j] = 0
    
    print(1)
    # del chat_diary[id]
    # print("2")
    user = get_object_or_404(User, username=player)

    user.games_played += 1

    if(p + 1 == win):
        user.games_won += 1

    user.save()

    if(p==0):
        gm = RunningChallenge.objects.filter(player1 = id)
        opnt = gm.first().player2
        gm.delete()
        # gm.save(gm)

        pair = Friends.objects.filter((Q(user1 = id) & Q(user2 = opnt)) | (Q(user1 = opnt) & Q(user2 = id))).first()
        if(pair is not None):
            pair.games_played_between += 1
            if(win == 1):
                if(pair.user1 == id):
                    pair.games_won_by_user1 +=1
                else:
                    pair.games_won_by_user2 +=1
            elif(win==2):
                if(pair.user1 == id):
                    pair.games_won_by_user2 +=1
                else:
                    pair.games_won_by_user1 +=1

            pair.save()

    data = {"message": "success"}
    return JsonResponse(data)

def send_Message(request, p, message):
    user = find_User(request)
    player = user

    chat_diary[player].append([p, str(player.username)[0], message])

    room_code = RunningChallenge.objects.filter(Q(player1=player) | Q(player2=player)).first().room_name
    position_array = pos_dict[user]

    channel_layer = get_channel_layer()
    async_to_sync(channel_layer.group_send)(
        'game_' + room_code,
        {
            'type': 'position_update',
            'message': 'conv_update',
            'lastmove': [0, 0],
            'position': position_array,
            'move': num_move(user),
            'win': win(user),
            'conv': chat_diary[player],
        }
    )

    data = {
            'message': 'conv_update',
            'conv': chat_diary[player],
        }
    return JsonResponse(data)