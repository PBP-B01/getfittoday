from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth.models import User

class StyledUserCreationForm(UserCreationForm):
    class Meta:
        model = User
        fields = ("username", "password1", "password2")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        base = "w-full px-4 py-3 rounded-lg bg-white text-blue-900 outline-none ring-2 ring-transparent focus:ring-yellow-400/80 transition placeholder:text-blue-900/50"
        self.fields["username"].widget.attrs.update({
            "class": base,
            "placeholder": "Username",
            "autocomplete": "username",
        })
        self.fields["password1"].widget.attrs.update({
            "class": base,
            "placeholder": "Password",
            "autocomplete": "new-password",
        })
        self.fields["password2"].widget.attrs.update({
            "class": base,
            "placeholder": "Ulangi password",
            "autocomplete": "new-password",
        })


class StyledAuthenticationForm(AuthenticationForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        base = "w-full px-4 py-3 rounded-lg bg-white text-blue-900 outline-none ring-2 ring-transparent focus:ring-yellow-400/80 transition placeholder:text-blue-900/50"
        self.fields["username"].widget.attrs.update({
            "class": base,
            "placeholder": "Username",
            "autocomplete": "username",
        })
        self.fields["password"].widget.attrs.update({
            "class": base,
            "placeholder": "Password",
            "autocomplete": "current-password",
        })