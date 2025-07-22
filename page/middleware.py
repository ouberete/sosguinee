import threading

_thread_local = threading.local()

class CurrentUserMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        _thread_local.user = request.user  # Enregistre l'utilisateur actuel dans un contexte local
        response = self.get_response(request)
        return response

def get_current_user():
    return getattr(_thread_local, 'user', None)
