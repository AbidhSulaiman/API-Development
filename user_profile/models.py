from django.db import models


class CustomUser(models.Model):
    """
    CustomUser model represents a user in the application.
    
    Fields:
    - name: Full name of the user.
    - email: Email address of the user, which must be unique.
    - age: Age of the user. Must be between 0 and 120.
    """
    name = models.CharField(max_length=255)
    email = models.EmailField(unique=True)
    age = models.PositiveIntegerField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

