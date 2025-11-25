import os
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from django.template.loader import render_to_string
from .models import Notification, ProjectUpdate

# Colors for user avatars
USER_COLORS = ['#0d6efd', '#6f42c1', '#d63384', '#fd7e14', '#198754', '#20c997', '#dc3545']

@receiver(post_save, sender=Notification)
def notification_created(sender, instance, created, **kwargs):
    if created:
        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(
            f"user_{instance.user.id}_notifications",
            {
                "type": "send_notification",
                "message": instance.message,
                "link": instance.link,
            }
        )

@receiver(post_save, sender=ProjectUpdate)
def project_update_created(sender, instance, created, **kwargs):
    if created:
        channel_layer = get_channel_layer()
        project = instance.project
        
        # File URLs
        image_url = instance.image.url if instance.image else None
        file_url = instance.file.url if instance.file else None
        file_name = os.path.basename(instance.file.name) if instance.file else None
        
        # --- NEW: Get Profile Photo URL ---
        sender_profile_photo = None
        if instance.user and instance.user.profile_photo:
            sender_profile_photo = instance.user.profile_photo.url
        # ----------------------------------

        # Decide layout
        if instance.title:
            html = render_to_string('pms/partials/timeline_item.html', {'update': instance})
        else: 
            html = render_to_string('pms/partials/chat_bubble.html', {'update': instance})
        
        async_to_sync(channel_layer.group_send)(
            f"project_{project.id}_updates",
            {
                "type": "send_project_update",
                "html": html,
                "sender_id": instance.user.id,
                "title": instance.title,
                "message": instance.remarks,
                "sender_username": instance.user.username,
                "sender_profile_photo": sender_profile_photo, # <-- SEND THIS
                "timestamp": instance.created_at.strftime("%I:%M %p"),
                "image_url": image_url,
                "file_url": file_url,
                "file_name": file_name,
            }
        )