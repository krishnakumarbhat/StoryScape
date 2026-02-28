from django.shortcuts import render


BASE_CONTEXT = {
    'name': 'StoryScape API',
    'status': 'ok',
    'endpoints': {
        'admin': '/admin/',
        'auth': '/api/auth/',
        'stories': '/api/stories/',
    },
}


def home_view(request):
    return render(request, 'home.html', BASE_CONTEXT)


def login_view(request):
    return render(request, 'login.html', BASE_CONTEXT)


def register_view(request):
    return render(request, 'register.html', BASE_CONTEXT)


def app_view(request):
    return render(request, 'app.html', BASE_CONTEXT)
