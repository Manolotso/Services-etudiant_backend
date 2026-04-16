from django.contrib import admin
from django.core.mail import send_mail
from django.conf import settings
from .models import RegistrationRequest, User, Course, Room, Schedule, Job
from .utils import generate_password


def approve_requests(modeladmin, request, queryset):
    print("🔥 ACTION CALLED")

    for req in queryset:
        print("➡ processing:", req.email, req.status)

        if req.status != "pending":
            continue

        password = generate_password()

        user = User.objects.create_user(
            email=req.email,
            password=password,
            role="student",
            must_change_password=True
        )

        print("📧 sending email to:", req.email)

        send_mail(
            'Votre mot de passe',
            f'Votre mot de passe est : {password}',
            settings.EMAIL_HOST_USER,
            [req.email],
            fail_silently=False,
        )

        req.status = "approved"
        req.save()


approve_requests.short_description = "Approuver les demandes"


@admin.register(RegistrationRequest)
class RegistrationRequestAdmin(admin.ModelAdmin):
    list_display = ("email", "status", "created_at")
    actions = [approve_requests]


admin.site.register(Course)
admin.site.register(Room)
admin.site.register(Schedule)
admin.site.register(Job)