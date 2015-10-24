from django import forms
from django.conf import settings
from django.contrib.auth.models import Group
from django.utils.translation import ugettext_lazy as _
from .models import User
from phoenix.animals.models import Breeder


class SignUpForm(forms.Form):
    farm = forms.CharField(label='Farm Name', widget=forms.TextInput(attrs={'placeholder': _('Farm name')}))

    def clean_farm(self):
        farm = self.cleaned_data.get('farm')
        farms = User.objects.filter(farm__iexact=farm)
        if farms:
            raise forms.ValidationError('Farm with that name already exists.')
        return farm

    def signup(self, request, user):
        farm = request.POST.get('farm')
        # create user
        user = User.objects.create(farm=farm)
        # create this farm as breeder
        Breeder.objects.create(name=farm, created_by=user, modified_by=user)

        # add user to all groups
        for group in settings.GROUP_PERMISSIONS.keys():
            user.groups.add(Group.objects.get(name=group))
