"""Tests for reporting app."""

import pytest
from django.contrib.auth.models import User
from reporting.models import Report


@pytest.mark.django_db
class TestReportModel:
    def test_create_report(self):
        report = Report.objects.create(
            title="Monthly Report",
            report_type="PATIENT",
            data="some data",
        )
        assert report.pk is not None
        assert report.created_at is not None

    def test_str_representation(self):
        report = Report.objects.create(
            title="Test Report",
            report_type="BILLING",
            data="billing data",
        )
        assert "Test Report" in str(report)
        assert "BILLING" in str(report)

    def test_multiple_reports(self):
        Report.objects.create(title="R1", report_type="LAB", data="d1")
        Report.objects.create(title="R2", report_type="SURGERY", data="d2")
        assert Report.objects.count() == 2

    def test_ordering_by_created_at(self):
        r1 = Report.objects.create(title="First", report_type="A", data="x")
        r2 = Report.objects.create(title="Second", report_type="B", data="y")
        reports = list(Report.objects.order_by("created_at"))
        assert reports[0].pk == r1.pk
        assert reports[1].pk == r2.pk


@pytest.mark.django_db
class TestReportViews:
    def _admin_client(self, client):
        user = User.objects.create_superuser(
            username="admin_report", password="pass", email="a@a.com"
        )
        client.force_login(user)
        return client

    def test_report_list_requires_login(self, client):
        response = client.get("/reports/")
        # raise_exception=True on the view means unauthenticated → 403
        assert response.status_code in (302, 403)

    def test_download_report(self, client):
        self._admin_client(client)
        report = Report.objects.create(
            title="Download Report", report_type="INVENTORY", data="inventory data"
        )
        response = client.get(f"/reports/{report.pk}/download/")
        assert response.status_code == 200
        assert b"inventory data" in response.content
        assert response["Content-Disposition"].startswith("attachment")

    def test_download_report_requires_login(self, client):
        report = Report.objects.create(
            title="Secure Report", report_type="BILLING", data="secret"
        )
        response = client.get(f"/reports/{report.pk}/download/")
        assert response.status_code == 302
