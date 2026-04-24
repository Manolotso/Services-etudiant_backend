from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    username_field = "email"

    def validate(self, attrs):
        data = super().validate(attrs)

        data["must_change_password"] = self.user.must_change_password
        data["has_username"] = bool(self.user.custom_username)
        data["role"] = self.user.role

        return data
    
#################################################################

# schedule/serializers.py
from rest_framework import serializers
from .models import Schedule

class ScheduleSerializer(serializers.ModelSerializer):
    course_name = serializers.CharField(source='course.name', read_only=True)
    teacher_name = serializers.CharField(source='course.teacher', read_only=True)
    room_name = serializers.CharField(source='room.name', read_only=True)

    class Meta:
        model = Schedule
        fields = '__all__'


#######################################################################

# jobs/serializers.py
from rest_framework import serializers
from .models import Job

class JobSerializer(serializers.ModelSerializer):
    class Meta:
        model = Job
        fields = '__all__'

    

#############################################################################


from rest_framework import serializers
from .models import HelpRequest, HelpResponse

class HelpResponseSerializer(serializers.ModelSerializer):
    user_name = serializers.SerializerMethodField()
    user_id = serializers.ReadOnlyField(source='user.id')

    class Meta:
        model = HelpResponse
        fields = ['id', 'user_name', 'user_id', 'content', 'is_accepted', 'created_at']

    def get_user_name(self, obj):
        return obj.user.custom_username or obj.user.email


class HelpRequestSerializer(serializers.ModelSerializer):
    user_name = serializers.SerializerMethodField()
    user_id = serializers.ReadOnlyField(source='user.id')
    responses = HelpResponseSerializer(many=True, read_only=True)

    class Meta:
        model = HelpRequest
        fields = [
            'id', 'user_name', 'user_id', 'title', 'description',
            'category', 'status', 'created_at', 'responses'
        ]

    def get_user_name(self, obj):
        return obj.user.custom_username or obj.user.email