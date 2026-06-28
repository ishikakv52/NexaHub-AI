from django.apps import AppConfig

class CoachConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'coach'
    verbose_name = 'AI English Coach'

    def ready(self):
        from django.db.models.signals import post_save
        from django.contrib.auth.models import User

        def create_profile(sender, instance, created, **kwargs):
            if created:
                from coach.models import UserProfile
                UserProfile.objects.get_or_create(user=instance)

        post_save.connect(create_profile, sender=User)
