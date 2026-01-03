from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.models import User
from .models import FriendRequest, Friendship, Message
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Q

def home(request):
    return render(request, 'start_messiging/home.html')

def view_login(request):
    if request.method == "POST":
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            login(request, user)
            messages.success(request, 'Login successful!')
            return redirect('home')
        else:
            messages.error(request, 'Invalid Username or Password')
            return redirect('view_login')
    
    return render(request, 'start_messiging/login.html')

def view_logout(request):
    logout(request)
    messages.success(request, 'You have been logged out successfully!')
    return redirect('home')

def signup(request):
    if request.method == "POST":
        username = request.POST.get('username')
        name = request.POST.get('name')
        email = request.POST.get('email')
        password = request.POST.get('password1')
        confirm_password = request.POST.get('password2')
        
        if password == confirm_password:
            try:
                if User.objects.filter(username=username).exists():
                    messages.error(request, 'Username already exists')
                    return redirect('signup')
                
                if User.objects.filter(email=email).exists():
                    messages.error(request, 'Email already exists')
                    return redirect('signup')
                
                user = User.objects.create_user(
                    username=username, 
                    email=email,
                    password=password,
                    first_name=name
                )
                user.save()
                
                messages.success(request, 'Account created successfully!')
                return redirect('view_login')
            
            except Exception as e:
                messages.error(request, f'Error creating account: {str(e)}')
                return redirect('signup')
        else:
            messages.error(request, 'Passwords do not match')
            return redirect('signup')
    
    return render(request, 'start_messiging/signup.html')


@login_required(login_url='view_login')
def view_connect(request):
    # Get all users except current user
    all_users = User.objects.exclude(id=request.user.id)
    
    # Get current user's friends
    friendships = Friendship.objects.filter(
        Q(user1=request.user) | Q(user2=request.user)
    )
    friend_ids = []
    for friendship in friendships:
        if friendship.user1 == request.user:
            friend_ids.append(friendship.user2.id)
        else:
            friend_ids.append(friendship.user1.id)
    
    # Get sent requests
    sent_requests = FriendRequest.objects.filter(from_user=request.user)
    sent_request_ids = [req.to_user.id for req in sent_requests]
    
    # Get received requests
    received_requests = FriendRequest.objects.filter(to_user=request.user)
    received_request_ids = [req.from_user.id for req in received_requests]
    
    # Available users (not friends, no pending requests)
    available_users = all_users.exclude(
        id__in=friend_ids + sent_request_ids + received_request_ids
    )
    
    context = {
        'available_users': available_users,
        'sent_requests': sent_requests,
        'received_requests': received_requests,
        'friends': User.objects.filter(id__in=friend_ids)
    }
    
    return render(request, 'start_messiging/connect.html', context)


@login_required(login_url='view_login')
def send_request(request, user_id):
    to_user = get_object_or_404(User, id=user_id)
    
    if to_user != request.user:
        FriendRequest.objects.get_or_create(
            from_user=request.user,
            to_user=to_user
        )
        messages.success(request, f'Friend request sent to {to_user.username}')
    
    return redirect('view_connect')


@login_required(login_url='view_login')
def accept_request(request, request_id):
    friend_request = get_object_or_404(FriendRequest, id=request_id, to_user=request.user)
    
    # Create friendship
    Friendship.objects.create(
        user1=friend_request.from_user,
        user2=request.user
    )
    
    # Delete the request
    friend_request.delete()
    
    messages.success(request, f'You are now friends with {friend_request.from_user.username}')
    return redirect('view_connect')


@login_required(login_url='view_login')
def reject_request(request, request_id):
    friend_request = get_object_or_404(FriendRequest, id=request_id, to_user=request.user)
    from_user = friend_request.from_user
    friend_request.delete()
    
    messages.info(request, f'Request from {from_user.username} rejected')
    return redirect('view_connect')


@login_required(login_url='view_login')
def chat_view(request, friend_id):
    friend = get_object_or_404(User, id=friend_id)
    
    # Check if they are friends
    is_friend = Friendship.objects.filter(
        Q(user1=request.user, user2=friend) | Q(user1=friend, user2=request.user)
    ).exists()
    
    if not is_friend:
        messages.error(request, 'You can only chat with friends')
        return redirect('view_connect')
    
    # Get all messages between these two users
    messages_list = Message.objects.filter(
        Q(sender=request.user, receiver=friend) | Q(sender=friend, receiver=request.user)
    ).order_by('timestamp')
    
    # Mark messages as read
    Message.objects.filter(sender=friend, receiver=request.user, is_read=False).update(is_read=True)
    
    # Send message
    if request.method == 'POST':
        content = request.POST.get('message')
        if content:
            Message.objects.create(
                sender=request.user,
                receiver=friend,
                content=content
            )
            return redirect('chat_view', friend_id=friend_id)
    
    context = {
        'friend': friend,
        'messages': messages_list
    }
    
    return render(request, 'start_messiging/chat.html', context)


@login_required(login_url='view_login')
def get_messages(request, friend_id):
    """API endpoint to get messages via AJAX"""
    from django.http import JsonResponse
    
    friend = get_object_or_404(User, id=friend_id)
    
    # Check if they are friends
    is_friend = Friendship.objects.filter(
        Q(user1=request.user, user2=friend) | Q(user1=friend, user2=request.user)
    ).exists()
    
    if not is_friend:
        return JsonResponse({'error': 'Not friends'}, status=403)
    
    # Get messages
    messages_list = Message.objects.filter(
        Q(sender=request.user, receiver=friend) | Q(sender=friend, receiver=request.user)
    ).order_by('timestamp')
    
    # Mark as read
    Message.objects.filter(sender=friend, receiver=request.user, is_read=False).update(is_read=True)
    
    # Convert to JSON
    messages_data = []
    for msg in messages_list:
        messages_data.append({
            'id': msg.id,
            'content': msg.content,
            'sender_id': msg.sender.id,
            'timestamp': msg.timestamp.strftime('%I:%M %p')
        })
    
    return JsonResponse({
        'messages': messages_data,
        'current_user_id': request.user.id
    })