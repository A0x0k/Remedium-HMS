from django.views import generic
from .models import Ward, Room, HospitalService
from .forms import WardForm, RoomForm
from django.urls import reverse_lazy
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.contrib.messages.views import SuccessMessageMixin
from core.views import DeleteSuccessMixin, SuccessQueryParamMixin


class HospitalServiceListView(
    LoginRequiredMixin, PermissionRequiredMixin, generic.ListView
):
    model = HospitalService
    template_name = "hospital/service_list.html"
    context_object_name = "services"
    paginate_by = 15
    permission_required = "hospital.view_hospitalservice"
    raise_exception = True

    def get_queryset(self):
        queryset = super().get_queryset()
        category = self.request.GET.get("category")
        if category:
            queryset = queryset.filter(category=category)
        return queryset


class OccupancyMapView(
    LoginRequiredMixin, PermissionRequiredMixin, generic.TemplateView
):
    template_name = "hospital/occupancy_map.html"
    permission_required = "hospital.view_ward"
    raise_exception = True

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Prefetch wards with rooms, and rooms with patients.
        # Room.ward declares no related_name, so the reverse accessor is
        # "room_set"; prefetching "rooms" raises AttributeError and 500s the
        # page for every user.
        context["wards"] = Ward.objects.prefetch_related(
            "room_set", "room_set__patient_set"
        ).all()
        return context


class WardListView(LoginRequiredMixin, PermissionRequiredMixin, generic.ListView):
    model = Ward
    template_name = "hospital/ward_list.html"
    context_object_name = "wards"
    paginate_by = 10
    permission_required = "hospital.view_ward"
    raise_exception = True

    def get_queryset(self):
        queryset = super().get_queryset()
        order_by = self.request.GET.get("order_by", "name")
        return queryset.order_by(order_by)


class WardDetailView(LoginRequiredMixin, PermissionRequiredMixin, generic.DetailView):
    model = Ward
    template_name = "hospital/ward_detail.html"
    context_object_name = "ward"
    permission_required = "hospital.view_ward"
    raise_exception = True


class WardCreateView(
    LoginRequiredMixin, PermissionRequiredMixin,
    SuccessQueryParamMixin, SuccessMessageMixin,
    generic.CreateView
):
    model = Ward
    form_class = WardForm
    template_name = "hospital/ward_form.html"
    success_url = reverse_lazy("ward_list")
    permission_required = "hospital.add_ward"
    raise_exception = True
    success_message = "Ward created successfully."


class WardUpdateView(
    LoginRequiredMixin, PermissionRequiredMixin,
    SuccessQueryParamMixin, SuccessMessageMixin,
    generic.UpdateView
):
    model = Ward
    form_class = WardForm
    template_name = "hospital/ward_form.html"
    success_url = reverse_lazy("ward_list")
    permission_required = "hospital.change_ward"
    raise_exception = True
    success_query_param = "updated"
    success_message = "Ward updated successfully."


class WardDeleteView(
    DeleteSuccessMixin, LoginRequiredMixin, PermissionRequiredMixin,
    SuccessMessageMixin, generic.DeleteView
):
    model = Ward
    template_name = "hospital/ward_confirm_delete.html"
    success_url = reverse_lazy("ward_list")
    permission_required = "hospital.delete_ward"
    raise_exception = True
    success_message = "Ward deleted successfully."


class RoomListView(LoginRequiredMixin, PermissionRequiredMixin, generic.ListView):
    model = Room
    template_name = "hospital/room_list.html"
    context_object_name = "rooms"
    paginate_by = 10
    permission_required = "hospital.view_room"
    raise_exception = True

    def get_queryset(self):
        queryset = super().get_queryset()
        order_by = self.request.GET.get("order_by", "room_number")
        return queryset.order_by(order_by)


class RoomDetailView(LoginRequiredMixin, PermissionRequiredMixin, generic.DetailView):
    model = Room
    template_name = "hospital/room_detail.html"
    context_object_name = "room"
    permission_required = "hospital.view_room"
    raise_exception = True


class RoomCreateView(
    LoginRequiredMixin, PermissionRequiredMixin,
    SuccessQueryParamMixin, SuccessMessageMixin,
    generic.CreateView
):
    model = Room
    form_class = RoomForm
    template_name = "hospital/room_form.html"
    success_url = reverse_lazy("room_list")
    permission_required = "hospital.add_room"
    raise_exception = True
    success_message = "Room created successfully."


class RoomUpdateView(
    LoginRequiredMixin, PermissionRequiredMixin,
    SuccessQueryParamMixin, SuccessMessageMixin,
    generic.UpdateView
):
    model = Room
    form_class = RoomForm
    template_name = "hospital/room_form.html"
    success_url = reverse_lazy("room_list")
    permission_required = "hospital.change_room"
    raise_exception = True
    success_query_param = "updated"
    success_message = "Room updated successfully."


class RoomDeleteView(
    DeleteSuccessMixin, LoginRequiredMixin, PermissionRequiredMixin,
    SuccessMessageMixin, generic.DeleteView
):
    model = Room
    template_name = "hospital/room_confirm_delete.html"
    success_url = reverse_lazy("room_list")
    permission_required = "hospital.delete_room"
    raise_exception = True
    success_message = "Room deleted successfully."
