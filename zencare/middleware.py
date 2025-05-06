from django.middleware.csrf import CsrfViewMiddleware

class DisableCSRFMiddleware(CsrfViewMiddleware):
    def process_view(self, request, callback, callback_args, callback_kwargs):
        return None 