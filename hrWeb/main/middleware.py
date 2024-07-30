# main/middlewares.py
from django.shortcuts import redirect
from django.urls import reverse
from .models import Compte

class AuthenticationMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        print("AuthenticationMiddleware exécuté")
        user_id = request.session.get('user_id')
        print(user_id)
        if user_id:
            try:
                request.user = Compte.objects.get(id=user_id)
            except Compte.DoesNotExist:
                request.user = None
        else:
            request.user = None

        response = self.get_response(request)
        return response

class ProtectUrlsMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        protected_urls = {
            reverse('home_admin'): ['AD'],
            reverse('home_salarie'): ['SA'],
            reverse('home_entreprise'): ['EN'],
            reverse('home_client'): ['CL'],
            reverse('liste_salarie'): ['AD'],
        }

        user_id = request.session.get('user_id')
        if user_id:
            try:
                request.user = Compte.objects.get(id=user_id)
                user_role = request.user.role.acce_page if request.user.role else None
            except Compte.DoesNotExist:
                request.user = None
                user_role = None
        else:
            request.user = None
            user_role = None

        for url, roles in protected_urls.items():
            if request.path == url and user_role not in roles:
                return redirect('connexion')  # Nom de votre URL de connexion

        response = self.get_response(request)
        return response