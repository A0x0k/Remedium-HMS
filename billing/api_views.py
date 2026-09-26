from rest_framework import viewsets, filters, status
from rest_framework.decorators import action
from rest_framework.response import Response
from drf_spectacular.utils import extend_schema, extend_schema_view
from django.core.exceptions import ValidationError as DjangoValidationError
from django.utils import timezone
from django_filters.rest_framework import DjangoFilterBackend
from .models import Invoice, Payment
from .serializers import InvoiceSerializer
from core.permissions import IsBillingStaff
from core.serializers import StandardErrorSerializer


@extend_schema_view(
    list=extend_schema(
        summary="List all invoices",
        description="Retrieve a paginated list of all invoices in the system.",
    ),
    retrieve=extend_schema(
        summary="Get invoice details",
        description="Retrieve detailed information about a specific invoice by ID.",
    ),
    create=extend_schema(
        summary="Create invoice", description="Generate a new invoice record."
    ),
    update=extend_schema(
        summary="Update invoice",
        description="Update all fields of an existing invoice.",
    ),
    partial_update=extend_schema(
        summary="Partial update invoice",
        description="Update specific fields of an existing invoice.",
    ),
    destroy=extend_schema(
        summary="Delete invoice",
        description="Remove an invoice record from the system.",
    ),
)
class InvoiceViewSet(viewsets.ModelViewSet):
    queryset = Invoice.objects.all()
    serializer_class = InvoiceSerializer
    permission_classes = [IsBillingStaff]
    filter_backends = [
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    ]
    filterset_fields = ["patient", "paid", "insurance_claimed"]
    search_fields = [
        "patient__unique_id",
        "patient__first_name",
        "patient__last_name",
        "invoice_number",
    ]
    ordering_fields = ["issue_date", "due_date", "total_amount"]
    ordering = ["-issue_date"]

    @extend_schema(
        summary="List unpaid invoices",
        description="Retrieve all invoices that have not yet been marked as fully paid.",
        responses={200: InvoiceSerializer(many=True)},
    )
    @action(detail=False, methods=["get"])
    def unpaid(self, request):
        """Get all unpaid invoices."""
        unpaid = self.queryset.filter(paid=False)
        serializer = self.get_serializer(unpaid, many=True)
        return Response(serializer.data)

    @extend_schema(
        summary="List overdue invoices",
        description="Retrieve all unpaid invoices where the due date has already passed.",
        responses={200: InvoiceSerializer(many=True)},
    )
    @action(detail=False, methods=["get"])
    def overdue(self, request):
        """Get overdue invoices."""
        overdue = self.queryset.filter(due_date__lt=timezone.now().date(), paid=False)
        serializer = self.get_serializer(overdue, many=True)
        return Response(serializer.data)

    @extend_schema(
        summary="Mark invoice as paid",
        description="Create a payment record to mark an invoice as paid. Defaults to full payment if amount is not specified.",
        request=None,
        responses={200: InvoiceSerializer, 400: StandardErrorSerializer},
    )
    @action(detail=True, methods=["post"])
    def mark_paid(self, request, pk=None):
        """Mark an invoice as paid by creating a payment record."""
        invoice = self.get_object()
        if invoice.paid:
            return Response(
                {"detail": "Invoice is already marked as paid."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        # Create a payment record for audit trail
        amount = request.data.get("amount", invoice.total_amount)
        payment_method = request.data.get("payment_method", "CASH")
        transaction_id = request.data.get("transaction_id", "")

        try:
            Payment.objects.create(
                invoice=invoice,
                amount=amount,
                payment_method=payment_method,
                transaction_id=transaction_id,
            )
        except DjangoValidationError as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)

        invoice.refresh_from_db()
        serializer = self.get_serializer(invoice)
        return Response(serializer.data)
