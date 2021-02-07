from dal import autocomplete
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404
from django.utils.decorators import method_decorator
from todo.models import Hazard
from todo.utils import user_can_read_hazard


class TaskAutocomplete(autocomplete.Select2QuerySetView):
    @method_decorator(login_required)
    def dispatch(self, request, hazard_id, *args, **kwargs):
        self.hazard = get_object_or_404(Hazard, pk=hazard_id)
        if not user_can_read_hazard(self.hazard, request.user):
            raise PermissionDenied

        return super().dispatch(request, hazard_id, *args, **kwargs)

    def get_queryset(self):
        # Don't forget to filter out results depending on the visitor !
        if not self.request.user.is_authenticated:
            return Hazard.objects.none()

        qs = Hazard.objects.filter(project=self.hazard.project).exclude(pk=self.hazard.pk)

        if self.q:
            qs = qs.filter(title__istartswith=self.q)

        return qs
