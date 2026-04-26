import pytest
from django.conf import settings
from django.contrib.auth import get_user_model
from django.test import Client


def test_django_daisy_installed_before_admin():
    apps = settings.INSTALLED_APPS
    assert "django_daisy" in apps
    assert apps.index("django_daisy") < apps.index("django.contrib.admin")


@pytest.mark.django_db
def test_admin_login_page_renders():
    client = Client()
    response = client.get("/admin/login/")
    assert response.status_code == 200
    content = response.content
    assert b'name="username"' in content
    assert b'name="password"' in content
    assert b"csrfmiddlewaretoken" in content


@pytest.mark.django_db
def test_change_form_shows_ecosystem_summary():
    User = get_user_model()
    User.objects.create_user(
        username="staffadmin",
        password="test-pass-123",
        is_staff=True,
        is_superuser=True,
    )
    client = Client()
    assert client.login(username="staffadmin", password="test-pass-123")
    response = client.get("/admin/customers/customer/add/")
    assert response.status_code == 200
    assert b"How this fits in the platform" in response.content
    assert b"Canonical hotspot subscriber identity" in response.content


@pytest.mark.django_db
def test_staff_can_access_admin_index_and_auth_group_changelist():
    User = get_user_model()
    User.objects.create_user(
        username="staffadmin",
        password="test-pass-123",
        is_staff=True,
        is_superuser=True,
    )
    client = Client()
    assert client.login(username="staffadmin", password="test-pass-123")
    index = client.get("/admin/")
    assert index.status_code == 200
    changelist = client.get("/admin/auth/group/")
    assert changelist.status_code == 200
