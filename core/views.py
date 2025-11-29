from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import JsonResponse
from django.views import View
from django.views.generic import CreateView
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.db import transaction
import json

from .forms import RegisterForm

class RegisterView(CreateView):
    form_class = RegisterForm

    @method_decorator(csrf_exempt)
    def post(self, request):
        data = json.loads(request.body)
        form = self.form_class(data)
        if form.is_valid():
            user = form.save()
            return JsonResponse({
                'success': True,
                'message': 'User registered',
                'role': user.groups.first().name if user.groups.exists() else 'Agent'
            })
        return JsonResponse({'error': form.errors}, status=400)

class LoginView(View):
    @method_decorator(csrf_exempt)
    def post(self, request):
        data = json.loads(request.body)
        username = data.get('username')
        password = data.get('password')
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            role = user.groups.first().name if user.groups.exists() else 'None'
            return JsonResponse({
                'success': True,
                'role': role,
                'user_id': user.id
            })
        return JsonResponse({'error': 'Invalid credentials'}, status=400)

class LogoutView(View):
    @method_decorator(csrf_exempt)
    @method_decorator(login_required)
    def post(self, request):
        logout(request)
        return JsonResponse({'success': True, 'message': 'Logged out'})

# Example protected view (role check decorator)
from functools import wraps

def manager_required(view_func):
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated or not request.user.groups.filter(name='Manager').exists():
            return JsonResponse({'error': 'Manager access required'}, status=403)
        return view_func(request, *args, **kwargs)
    return _wrapped_view

# Test protected view (e.g., for dashboard)
class TestProtectedView(LoginRequiredMixin, View):
    @method_decorator(csrf_exempt)
    def get(self, request):
        return JsonResponse({'message': f'Hello {request.user.username}, role: {request.user.groups.first().name if request.user.groups.exists() else "None"}'})