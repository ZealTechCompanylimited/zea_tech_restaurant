from django.shortcuts import redirect
from django.urls import resolve
from .decorators import PLAN_APPS

class SubscriptionMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Staff & superuser bypass
        if request.user.is_authenticated and (request.user.is_staff or request.user.is_superuser):
            return self.get_response(request)

        # Exempt paths
        exempt_paths = [
            '/admin/', '/subscriptions/choose/', '/subscriptions/checkout/', '/payments/', '/static/', '/login/', '/logout/'
        ]
        path = request.path
        if any(path.startswith(p) for p in exempt_paths):
            return self.get_response(request)

        if request.user.is_authenticated:
            sub = getattr(request.user, "usersubscription", None)
            if not sub or not sub.is_valid():
                return redirect("/subscriptions/choose/")

            # current_app may be None
            try:
                current_app = resolve(path).app_name
            except Exception:
                current_app = None

            allowed_apps = PLAN_APPS.get(sub.plan.key, [])
            if current_app and current_app not in allowed_apps:
                return redirect("/subscriptions/choose/")

        return self.get_response(request)
