from django.shortcuts import redirect
from .decorators import PLAN_APPS  # Make sure PLAN_APPS is in decorators.py

class PlanRequiredMixin:
    """
    Use this mixin in class-based views to restrict access based on user's subscription plan.
    Set `app_name` in your CBV to the app this view belongs to.
    """
    app_name = None

    def dispatch(self, request, *args, **kwargs):
        sub = getattr(request.user, "usersubscription", None)

        # Redirect if user has no subscription or subscription expired
        if not sub or not sub.is_valid():
            return redirect("/subscriptions/choose/")

        # Check if the app is allowed for the user's plan
        allowed_apps = PLAN_APPS.get(sub.plan.key, [])
        if self.app_name not in allowed_apps:
            return redirect("/subscriptions/choose/")

        # Continue with normal dispatch
        return super().dispatch(request, *args, **kwargs)
