from rest_framework import serializers
from .models import CustomUser

class UserSerializer(serializers.ModelSerializer):
    
    class Meta:
        model = CustomUser
        fields = ['id','name', 'email', 'age']

    def validate_name(self, value):
        if len(value) == 0:
            raise serializers.ValidationError("Name cannot be empty.")
        return value
    
    def validate_age(self, value):
        if not (0 < value <= 120):
            raise serializers.ValidationError("Age must be between 0 and 120.")
        return value
        