from allauth.socialaccount.adapter import DefaultSocialAccountAdapter


class CustomSocialAccountAdapter(DefaultSocialAccountAdapter):
    def populate_user(self, request, sociallogin, data):
        user = super().populate_user(request, sociallogin, data)

        # tenta pegar email do provider / extra_data
        email = (
            data.get("email")
            or sociallogin.account.extra_data.get("email")
            or ""
        ).strip()

        if email:
            user.email = email
            if not user.username:
                user.username = email

        return user

    def save_user(self, request, sociallogin, form=None):
        user = super().save_user(request, sociallogin, form)

        email = (
            sociallogin.account.extra_data.get("email")
            or user.email
            or ""
        ).strip()

        if email and user.email != email:
            user.email = email

        if email and not user.username:
            user.username = email

        user.save(update_fields=["email", "username"])
        return user