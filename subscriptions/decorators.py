from functools import wraps
from django.shortcuts import redirect

PLAN_APPS = {
    "monthly": ["menu", "inventory", "reports"],
    "yearly": ["menu", "inventory", "reports", "reservation.core"],
    "three_years": ["menu", "inventory", "reports", "reservation.core", "accounts", "orders", "payments", "organizations"]
}

def subscription_required(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        sub = getattr(request.user, "usersubscription", None)
        if not sub or not sub.is_valid():
            return redirect("/subscriptions/choose/")
        return view_func(request, *args, **kwargs)
    return wrapper

def plan_required_for_app(app_name):
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            sub = getattr(request.user, "usersubscription", None)
            if not sub or not sub.is_valid():
                return redirect("/subscriptions/choose/")
            allowed_apps = PLAN_APPS.get(sub.plan.key, [])
            if app_name not in allowed_apps:
                return redirect("/subscriptions/choose/")
            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator
