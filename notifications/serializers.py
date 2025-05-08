from rest_framework import serializers
from .models import Notification

class NotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = ['id', 'notification_type', 'title', 'message', 'is_read', 'created_at', 'related_object_id', 'related_object_type']
        read_only_fields = ['notification_type', 'title', 'message', 'created_at', 'related_object_id', 'related_object_type'] 