from unittest import mock

# Mock google.cloud.secretmanager before app.crud is imported
with mock.patch(
    "google.cloud.secretmanager.SecretManagerServiceClient"
) as MockSecretManagerServiceClient:
    (
        MockSecretManagerServiceClient.return_value.access_secret_version.return_value.payload.data.decode.return_value
    ) = "dummy_secret_key"
    from app.crud import is_password_strong_enough


def test_password_strong_enough() -> None:
    """Tests the is_password_strong_enough function."""
    assert is_password_strong_enough("StrongP@ss1")
    assert not is_password_strong_enough("weak")  # Too short
    assert not is_password_strong_enough("NO_LOWERCASE1")
    assert not is_password_strong_enough("no_uppercase1")
    assert not is_password_strong_enough("NoNumbers")
    # This should pass based on current regex
    assert is_password_strong_enough("NoSpecialChar1")
    assert is_password_strong_enough("AnotherStrongP@ss2")
