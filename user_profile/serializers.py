from rest_framework import serializers
from .models import CustomUser

class CustomUserSerializer(serializers.ModelSerializer):
    """
    Serializer for the CustomUser model.
    
    Fields: 'id','name', 'email', 'age'
    """
    class Meta:
        model = CustomUser
        fields = ['id','name', 'email', 'age']
        

    def validate_name(self, value):
        """
        Validates that the name should be a non-empty string
        """
        if len(value) == 0:
            raise serializers.ValidationError("Name cannot be empty.")
        return value
    
    
    def validate_age(self, value):
        """
        Validates that the age is between 0 and 120.
        """
        if not (0 < value <= 120):
            raise serializers.ValidationError("Age must be between 0 and 120.")
        return value
        