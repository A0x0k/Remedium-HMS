from django.shortcuts import get_object_or_404
from django.views import generic
from .models import Invoice, Payment
from .forms import InvoiceForm, InvoiceItemFormSet
from django.urls import reverse_lazy, reverse
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.contrib.messages.views import SuccessMessageMixin
from core.views import DeleteSuccessMixin, SuccessQueryParamMixin
from django.db import transaction


class InvoiceListView(LoginRequiredMixin, PermissionRequiredMixin, generic.ListView):
    model = Invoice
    template_name = "billing/invoice_list.html"
    context_object_name = "invoices"
    paginate_by = 10
    permission_required = "billing.billing_view_invoice"
    raise_exception = True

    ALLOWED_ORDER_BY = [
        "issue_date",
        "due_date",
        "total_amount",
        "-issue_date",
        "-due_date",
        "-total_amount",
    ]

    def get_queryset(self):
        queryset = super().get_queryset().select_related("patient")
        order_by = self.request.GET.get("order_by", "issue_date")
        if order_by not in self.ALLOWED_ORDER_BY:
            order_by = "issue_date"
        return queryset.order_by(order_by)


class InvoiceCreateView(
    LoginRequiredMixin, PermissionRequiredMixin,
    SuccessQueryParamMixin, SuccessMessageMixin,
    generic.CreateView
):
    model = Invoice
    form_class = InvoiceForm
    template_name = "billing/invoice_form.html"
    success_url = reverse_lazy("invoice_list")
    permission_required = "billing.billing_add_invoice"
    raise_exception = True
    success_message = "Invoice created successfully."

    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)
        if self.request.POST:
            data["items"] = InvoiceItemFormSet(self.request.POST)
        else:
            data["items"] = InvoiceItemFormSet()
        return data

    def form_valid(self, form):
        context = self.get_context_data()
        items = context["items"]
        with transaction.atomic():
            self.object = form.save()
            if items.is_valid():
                items.instance = self.object
                items.save()
            else:
                return self.form_invalid(form)
        return super().form_valid(form)


class InvoiceUpdateView(
    LoginRequiredMixin, PermissionRequiredMixin,
    SuccessQueryParamMixin, SuccessMessageMixin,
    generic.UpdateView
):
    model = Invoice
    form_class = InvoiceForm
    template_name = "billing/invoice_form.html"
    success_url = reverse_lazy("invoice_list")
    permission_required = "billing.billing_change_invoice"
    raise_exception = True
    success_query_param = "updated"
    success_message = "Invoice updated successfully."

    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)
        if self.request.POST:
            data["items"] = InvoiceItemFormSet(self.request.POST, instance=self.object)
        else:
            data["items"] = InvoiceItemFormSet(instance=self.object)
        return data

    def form_valid(self, form):
        context = self.get_context_data()
        items = context["items"]
        with transaction.atomic():
            self.object = form.save()
            if items.is_valid():
                items.instance = self.object
                items.save()
            else:
                return self.form_invalid(form)
        return super().form_valid(form)


class InvoiceDeleteView(
    DeleteSuccessMixin, LoginRequiredMixin, PermissionRequiredMixin,
    SuccessMessageMixin, generic.DeleteView
):
    model = Invoice
    template_name = "billing/invoice_confirm_delete.html"
    success_url = reverse_lazy("invoice_list")
    permission_required = "billing.billing_delete_invoice"
    raise_exception = True
    success_message = "Invoice deleted successfully."


class InvoiceDetailView(
    LoginRequiredMixin, PermissionRequiredMixin, generic.DetailView
):
    model = Invoice
    template_name = "billing/invoice_detail.html"
    context_object_name = "invoice"
    permission_required = "billing.billing_view_invoice"
    raise_exception = True

    def get_queryset(self):
        return (
            Invoice.objects.select_related("patient")
            .prefetch_related("payments", "items__service")
            .all()
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["payments"] = self.object.payments.all()
        context["items"] = self.object.items.all()
        return context


class InvoicePrintView(LoginRequiredMixin, PermissionRequiredMixin, generic.DetailView):
    model = Invoice
    template_name = "billing/invoice_print.html"
    context_object_name = "invoice"
    permission_required = "billing.billing_view_invoice"
    raise_exception = True

    def get_queryset(self):
        return (
            Invoice.objects.select_related("patient")
            .prefetch_related("payments", "items__service")
            .all()
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["payments"] = self.object.payments.all()
        context["items"] = self.object.items.all()
        return context


class PaymentCreateView(
    LoginRequiredMixin, PermissionRequiredMixin,
    SuccessMessageMixin, generic.CreateView
):
    model = Payment
    fields = ["amount", "payment_method", "transaction_id"]
    template_name = "billing/payment_form.html"
    permission_required = "billing.billing_change_invoice"
    raise_exception = True
    success_message = "Payment recorded successfully."

    def form_valid(self, form):
        form.instance.invoice = get_object_or_404(Invoice, pk=self.kwargs["invoice_pk"])
        return super().form_valid(form)

    def get_success_url(self):
        url = reverse("invoice_detail", kwargs={"pk": self.kwargs["invoice_pk"]})
        return f"{url}?created=1"
