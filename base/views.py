from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.contrib.auth import authenticate, login, logout

from django.core.files import File
from django.core.files.temp import NamedTemporaryFile

from .models import Room, Topic, Message, User, SteamRecent
from .forms import RoomForm, UserForm, MyUserCreationForm
from django.conf import settings
import requests
from PIL import Image
from io import BytesIO
import urllib

# Create your views here.

# rooms = [
#     {'id':1, 'name':'Lets learn python!'},
#     {'id':2, 'name':'Design with me'},
#     {'id':3, 'name':'Frontend developers'},
#     ]


def loginPage(request):
    page = 'login'
    if request.user.is_authenticated:
        return redirect('home')

    if request.method == 'POST':
        email = request.POST.get('email').lower()
        password = request.POST.get('password')

        try:
            user = User.objects.get(email=email)
            
        except:
            messages.error(request, 'Email does not exist')
        
        user = authenticate(request, email=email, password=password)
        
        if user is not None:
            login(request, user)
            return redirect('home')
        else:
            messages.error(request, 'Password was incorrect...')

    
    context = {'page': page}
    return render(request, 'base/login_register.html', context)


def logoutUser(request):
    logout(request)
    return redirect('home')


def registerPage(request):
    
    form = MyUserCreationForm()
    context = {'form': form}

    if request.method == 'POST':
        form = MyUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.username = user.username.lower()
            user.save()
            login(request, user)
            return redirect('home')
        else:
            messages.error(request, 'An error occurred during registration')

    return render(request, 'base/login_register.html', context)

def home(request):

    q = request.GET.get('q') if request.GET.get('q') != None else ''

    rooms = Room.objects.filter(
        Q(topic__name__icontains=q) |
        Q(name__icontains=q) |
        Q(description__icontains=q)
        ) 


    # figure out how to filter topics by most popular first!!!
    topics = Topic.objects.all()[0:5]
    room_count = rooms.count()

    #can change in future  to modify so that it only shows people you follow
    room_messages = Message.objects.filter(Q(room__topic__name__icontains=q))
    
    context = {'rooms':rooms, 'topics': topics, 'room_count': room_count, 'room_messages':room_messages}
    return render(request, 'base/home.html', context)

def room(request, pk):
    room = Room.objects.get(id=pk)
    room_messages = room.message_set.all().order_by('-created')
    participants = room.participants.all()
    if request.method == 'POST':
        message = Message.objects.create(
            user = request.user,
            room = room,
            body = request.POST.get('body')
        )
        room.participants.add(request.user)
        return redirect('room', pk=room.id)

    context = {'room': room, 'room_messages': room_messages, 'participants': participants}
    return render(request, 'base/room.html', context)


def userProfile(request, pk):
    user = User.objects.get(id=pk)
    # can get all of the children of an object for ex: room_set
    steam_games = user.steamrecent_set.all()
    steam_count = user.steamrecent_set.count()
    
    rooms = user.room_set.all()
    room_messages = user.message_set.all()
    topics = Topic.objects.all()
    context = {'user': user, 'rooms': rooms , 'topics': topics, 'room_messages': room_messages, 'steam_games': steam_games, 'steam_count': steam_count}
    return render(request, 'base/profile.html', context)


@login_required(login_url='login')
def createRoom(request):
    form = RoomForm()
    topics = Topic.objects.all()

    if request.method == 'POST':
        topic_name = request.POST.get('topic')
        topic, created = Topic.objects.get_or_create(name=topic_name)
        # Saves the form value in manually since a new topic can be added
        Room.objects.create(
            host=request.user,
            topic=topic,
            name=request.POST.get('name'),
            description = request.POST.get('description'),
        )


        # Alternative method of saving from without adding new topics
        # form = RoomForm(request.POST)
        # if form.is_valid():
        #     # copmmit = False saves an instance of the form allowing someone to edit the value inside
        #     room = form.save(commit = False)
        #     room.host = request.user
        #     room.save()
        return redirect('home')

    context= {'form': form, 'topics': topics}
    return render(request, 'base/room_form.html', context)


@login_required(login_url='login')
def updateRoom(request, pk):
    room = Room.objects.get(id=pk)

    form = RoomForm(instance=room)
    

    topics = Topic.objects.all()

    if request.user != room.host:
        return HttpResponse('You are not allowed here!!')

    if request.method == 'POST':
        topic_name = request.POST.get('topic')
        topic, created = Topic.objects.get_or_create(name=topic_name)
        room.name = request.POST.get('name')
        room.topic = topic
        room.description = request.POST.get('description')
        room.save()
        return redirect('home')

    context = {'form': form, 'topics': topics, 'room':room}
    return render(request, 'base/room_form.html', context)


@login_required(login_url='login')
def deleteRoom(request, pk):
    room = Room.objects.get(id=pk)

    if request.user != room.host:
        return HttpResponse('You are not allowed here!!')


    if request.method == 'POST':
        room.delete()
        return redirect('home')
    
    return render(request, 'base/delete.html', {'obj': room})

@login_required(login_url='login')
def deleteMessage(request, pk):
    message = Message.objects.get(id=pk)

    if request.user != message.user:
        return HttpResponse('You are not allowed here!!')


    if request.method == 'POST':
        message.delete()
        return redirect('home')
    return render(request, 'base/delete.html', {'obj': message})


@login_required(login_url='login')
def updateUser(request):
    user = request.user
    form = UserForm(instance=user)

    if request.method == 'POST':
        # request files also sends the files submitted through the form
        form = UserForm(request.POST, request.FILES, instance=user)
        if form.is_valid():
            form.save()
            return redirect('user-profile', pk=user.id)

    return render(request, 'base/update-user.html', {'form': form})



def topicsPage(request):
    q = request.GET.get('q') if request.GET.get('q') != None else ''

    topics = Topic.objects.filter(name__icontains=q)
    return render(request, 'base/topics.html', {'topics': topics})


def activityPage(request):
    room_messages = Message.objects.all()
    return render(request, 'base/activity.html', {'room_messages': room_messages})

def steamPage(request, pk):
    user = User.objects.get(id=pk)
    
    api_key = settings.API_KEY
    print(settings.API_KEY)
    count = 3
    steam_id = 0
    stats = None
    profile_valid = None

    if request.method == 'POST':

        print(request.POST.get('steamid'))
                
        steam_id = request.POST.get('steamid')
        url = f"http://api.steampowered.com/IPlayerService/GetRecentlyPlayedGames/v0001/?key={api_key}&count={count}&steamid={steam_id}&format=json"
        profileurl = f"http://api.steampowered.com/ISteamUser/GetPlayerSummaries/v0002/?key={api_key}&steamids={steam_id}&format=json"
        responseapi = requests.get(url)
        profile = requests.get(profileurl)

        
        try:
            stats = responseapi.json()
            profile_valid = profile.json()
            print(stats)
        except:
            print("hi")
            messages.error(request, 'steam id was invalid or profile is private')
        
        
        
        if stats != None and stats.get('response').get('total_count') > 0 and profile_valid != None:

            user.steamadd = True
            user.steamname = profile_valid.get('response').get('players')[0].get('personaname')
            user.save()
        
            for game in stats.get('response').get('games'):

                total_played = round(game.get('playtime_forever') / 60, 1)
                appId = game.get('appid')
                imgId = game.get('img_icon_url')
                get_img = f"http://media.steampowered.com/steamcommunity/public/images/apps/{appId}/{imgId}.jpg"

                form = SteamRecent()

                
                form.user = request.user
                form.name = game.get('name')
                form.stat = f"Total time played: {total_played} hrs"
                form.gameImgURL = get_img
                
                form.cache()
                form.save()

        elif stats != None and stats.get('response').get('total_count') == 0 and profile_valid != None:

            user.steamadd = True
            user.steamname = profile_valid.get('response').get('players')[0].get('personaname')
            user.save()
                
        else:
            stats = None
            return redirect('steam', pk)
        return redirect('user-profile', pk)

    
    context = {}

    return render(request, 'base/steam_page.html', context)




def updateSteam(request, pk):

    user = User.objects.get(id=pk)
    
    
    
    api_key = settings.API_KEY
    print(settings.API_KEY)
    count = 3
    steam_id = 0
    stats = None
    profile_valid = None

    if request.method == 'POST':

        if user.steamrecent_set.count > 0:

            steam_games = user.steamrecent_set.all().delete()

        print(request.POST.get('steamid'))
                
        steam_id = request.POST.get('steamid')
        url = f"http://api.steampowered.com/IPlayerService/GetRecentlyPlayedGames/v0001/?key={api_key}&count={count}&steamid={steam_id}&format=json"
        profileurl = f"http://api.steampowered.com/ISteamUser/GetPlayerSummaries/v0002/?key={api_key}&steamids={steam_id}&format=json"
        responseapi = requests.get(url)
        profile = requests.get(profileurl)

        
        try:
            stats = responseapi.json()
            profile_valid = profile.json()
            print(stats)
        except:
            print("hi")
            messages.error(request, 'steam id was invalid or profile is private')
        
        
        
        if stats != None and stats.get('response').get('total_count') > 0 and profile_valid != None:

            user.steamadd = True
            user.steamname = profile_valid.get('response').get('players')[0].get('personaname')
            user.save()
        
            for game in stats.get('response').get('games'):

                total_played = round(game.get('playtime_forever') / 60, 1)
                appId = game.get('appid')
                imgId = game.get('img_icon_url')
                get_img = f"http://media.steampowered.com/steamcommunity/public/images/apps/{appId}/{imgId}.jpg"

                form = SteamRecent()

                
                form.user = request.user
                form.name = game.get('name')
                form.stat = f"Total time played: {total_played} hrs"
                form.gameImgURL = get_img
                
                form.cache()
                form.save()

        
                
        else:
            stats = None
            return redirect('update-steam', pk)
        return redirect('user-profile', pk)

    
    context = {}

    return render(request, 'base/steam_page.html', context)


def deleteSteam(request, pk):

    user = User.objects.get(id=pk)
    
    

    if request.method == 'POST':

        steam_games = user.steamrecent_set.all().delete()

                
        user.steamname = ""
        user.steamadd = False
        user.save()
        return redirect('user-profile', pk)

    
    context = {'pk': pk}

    return render(request, 'base/delete_steam.html', context)
