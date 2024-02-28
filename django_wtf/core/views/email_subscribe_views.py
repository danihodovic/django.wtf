from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.mail import EmailMessage
from django.urls import reverse_lazy
from django.views.generic import TemplateView
from django.views.generic.base import RedirectView

from django_wtf.core.models import EmailSubscriber


class EmailSubscriberLandingView(TemplateView):
    template_name = "core/email_subscriber_landing.html"


email_subscriber_landing_view = EmailSubscriberLandingView.as_view()


class CreateEmailSubscriberView(LoginRequiredMixin, RedirectView):
    permanent = False
    url = reverse_lazy("core:index")
    query_string = True

    def get_redirect_url(self, *args, **kwargs):
        user = self.request.user
        _, _ = EmailSubscriber.objects.get_or_create(user=self.request.user)
        emailaddress = user.emailaddress_set.get(primary=True)  # type: ignore
        email = EmailMessage(
            subject="Subscription confirmed to Django.WTF",
            body="""Woohoo!

I'll update you with trending projects and news from the Django world every two weeks.

Thanks,
The people behind Django.WTF
""",
            from_email="noreply@django.wtf",
            to=[emailaddress.email],
            reply_to=["noreply@django.wtf"],
        )
        email.send()
        messages.success(
            self.request,
            "We will send you email updates every other week on trending repositories.",
        )

        return super().get_redirect_url(*args, **kwargs)


create_email_subscriber_view = CreateEmailSubscriberView.as_view()
