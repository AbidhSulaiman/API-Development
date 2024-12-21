import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient
from io import StringIO
from .models import CustomUser



def generate_csv(data: str, filename="users.csv"):
    """
    Utility function to generate CSV files
    """
    
    file = StringIO(data)
    file.name = filename
    return file


@pytest.fixture
def api_client():
    """
    Provides an instance of the Django APIClient for testing.
    """
    return APIClient()


@pytest.fixture
def add_user_url():
    """
    Returns: URL for the 'add_user' API endpoint
    """
    return reverse('add_user')


@pytest.fixture
def valid_csv_file():
    """
    Returns: A valid CSV file for testing.
    """
    csv_data = "name,email,age\nJohn Doe,john@example.com,30\nJane Mane,jane@example.com,25\n"
    return generate_csv(csv_data)


@pytest.fixture
def invalid_csv_file():
    """
    Returns: An invalid CSV file for testing with missing name, invalide email and invalid date.
    """
    csv_data = (
        "name,email,age\n"
        ",john@example.com,30\n"
        "Jane Mane,janeexample.com,25\n"
        "Jan Mane,jane@example.com,125\n"
    )
    return generate_csv(csv_data)


@pytest.mark.django_db
def test_upload_empty_file(api_client, add_user_url):
    """
    Test uploading an empty file. Should return 400 with error message.
    """
    response = api_client.post(add_user_url, {'file': ''}, format='multipart')
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.data['error'] == 'No file uploaded.'


@pytest.mark.django_db
def test_upload_wrong_file_format(api_client, add_user_url):
    """
    Test uploading a file with the wrong format (e.g., TSV instead of CSV).
    Should return 400 with an error message.
    """
    data = "name\temail\tage\nJohn Doe\tjohn@example.com\t30\n"
    file = generate_csv(data, filename="input.tsv")
    response = api_client.post(add_user_url, {'file': file}, format='multipart')

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.data['error'] == 'File must have a .csv extension.'


@pytest.mark.django_db
def test_upload_valid_csv(api_client, valid_csv_file, add_user_url):
    """
    Test uploading a valid CSV file. Should successfully save records.
    """
    response = api_client.post(add_user_url, {'file': valid_csv_file}, format='multipart')

    assert response.status_code == status.HTTP_200_OK
    assert response.data['saved_records'] == 2
    assert response.data['rejected_records'] == 0
    assert response.data['errors'] == []
    assert CustomUser.objects.count() == 2


@pytest.mark.django_db
def test_upload_invalid_csv(api_client, invalid_csv_file, add_user_url):
    """
    Test uploading an invalid CSV file. Should reject all records and return errors.
    """
    response = api_client.post(add_user_url, {'file': invalid_csv_file}, format='multipart')

    assert response.status_code == status.HTTP_200_OK
    assert response.data['saved_records'] == 0
    assert response.data['rejected_records'] == 3
    assert len(response.data['errors']) == 3
    assert response.data['errors'][0]['error']['name'][0] == "This field may not be blank."
    assert response.data['errors'][1]['error']['email'][0] == "Enter a valid email address."
    assert response.data['errors'][2]['error']['age'][0] == "Age must be between 0 and 120."


@pytest.mark.django_db
def test_upload_duplicate_mail_id(api_client, add_user_url):
    """
    Test uploading a CSV file with duplicate email addresses. Should save one record and reject the duplicate.
    """
    csv_data = "name,email,age\nJohn Doe,john@example.com,30\nJane Mane,john@example.com,25\n"
    file = generate_csv(csv_data)

    response = api_client.post(add_user_url, {'file': file}, format='multipart')

    assert response.status_code == status.HTTP_200_OK
    assert response.data['saved_records'] == 1
    assert response.data['rejected_records'] == 1
    assert len(response.data['errors']) == 1
    assert "Duplicate email in file" in response.data['errors'][0]['error']
    assert CustomUser.objects.filter(email='john@example.com').count() == 1
