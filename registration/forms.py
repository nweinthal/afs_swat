from django import forms
from django.core import validators
from django.contrib.auth.models import User
from registration.models import UserProfile
from registration.models import AffinityGroup
from registration.models import EcoProfile
from django.forms.extras.widgets import SelectDateWidget
import datetime
import re
from django.forms.widgets import Widget, Select
from django.utils.dates import MONTHS
from django.utils.safestring import mark_safe
from django.core import exceptions

__all__ = ('MonthYearWidget',)

RE_DATE = re.compile(r'(\d{4})-(\d\d?)-(\d\d?)$')

class MonthYearWidget(Widget):
    """
    A Widget that splits date input into two <select> boxes for month and year,
    with 'day' defaulting to the first of the month.
    
    Based on SelectDateWidget, in 
    
    django/trunk/django/forms/extras/widgets.py
    
    CREDIT: User greg from Django Snippets
    
    """
    none_value = (0, '---')
    month_field = '%s_month'
    year_field = '%s_year'

    def __init__(self, attrs=None, years=None, required=True):
        # years is an optional list/tuple of years to use in the "year" select box.
        self.attrs = attrs or {}
        self.required = required
        if years:
            self.years = years
        else:
            this_year = datetime.date.today().year
            self.years = range(this_year, this_year+10)

    def render(self, name, value, attrs=None):
        try:
            year_val, month_val = value.year, value.month
        except AttributeError:
            year_val = month_val = None
            if isinstance(value, basestring):
                match = RE_DATE.match(value)
                if match:
                    year_val, month_val, day_val = [int(v) for v in match.groups()]

        output = []

        if 'id' in self.attrs:
            id_ = self.attrs['id']
        else:
            id_ = 'id_%s' % name

        month_choices = MONTHS.items()
        if not (self.required and value):
            if not (self.required and month_val):
                month_choices.append(self.none_value)
        month_choices.sort()
        local_attrs = self.build_attrs(id=self.month_field % id_)
        s = Select(choices=month_choices)
        select_html = s.render(self.month_field % name, month_val, local_attrs)
        output.append(select_html)

        year_choices = [(i, i) for i in self.years]
        if not (self.required and value):
                if not (self.required and year_val):
                    year_choices.insert(0, self.none_value)
        local_attrs['id'] = self.year_field % id_
        s = Select(choices=year_choices)
        select_html = s.render(self.year_field % name, year_val, local_attrs)
        output.append(select_html)

        return mark_safe(u'\n'.join(output))

    def id_for_label(self, id_):
        return '%s_month' % id_
    id_for_label = classmethod(id_for_label)

    def value_from_datadict(self, data, files, name):
        y = data.get(self.year_field % name)
        m = data.get(self.month_field % name)
        if y == m == "0":
            return None
        if y and m:
            return '%s-%s-%s' % (y, m, 1)
        return data.get(name, None)



    
class UserUpdateForm(forms.Form):
    current_year = datetime.datetime.now().year
    year_choices = range(current_year-12, current_year+1)
    
    # Updated Monthly
    date_on_bills   = forms.DateField()
    water_bill      = forms.FloatField(required=False, initial = 0)   # Gallons
    electric_bill   = forms.FloatField(required=False, initial = 0)   # KWh
    trash_weight    = forms.FloatField(required=False, initial = 0)   # Gallons
    gas             = forms.FloatField(required=False, initial = 0) # Gallons
    natural_gas     = forms.FloatField(required=False, initial = 0) # CCF
    heating_oil     = forms.FloatField(required=False, initial = 0)    # Gallons
    
    # Updated Ocassionally    
    house_sq        = forms.IntegerField()
    occupants       = forms.IntegerField()
    
    def make_defaults(self, usr):
        defaults = UserProfile.objects.get(user = usr)
        self.house_sq = forms.IntegerField(widget=forms.TextInput, initial = defaults.house_square_footage)
        self.occupants = forms.IntegerField(widget=forms.TextInput, initial = defaults.number_of_people)

    def save(self, usr):
        data = self.cleaned_data
        ecp = EcoProfile()
        ecp.user = usr
        ecp.water_this_month = data['water_bill']
        ecp.gas_this_month = int(data['gas'])
        ecp.heating_oil = data['heating_oil']
        ecp.natural_gas = int(data['natural_gas'])
        ecp.pounds_of_trash = data['trash_weight']
        ecp.current_month = data['date_on_bills']
        ecp.electricity_this_month = data['electric_bill']
        ecp.save()
        
        profile = UserProfile.objects.get(user = usr)
        profile.house_square_footage = data['house_sq']
        profile.number_of_people = data['occupants']
        profile.save()
        return ecp
    
class RecordRetrieveForm(forms.Form):
    month_date      = forms.DateField(widget = MonthYearWidget(years = UserUpdateForm.year_choices))
'''
CLASS   RegistrationForm
DESC    Defines the user registration form on the sign up page
'''
class RegistrationForm(forms.Form):
    first_name = forms.CharField()
    last_name = forms.CharField()
    username = forms.CharField(max_length = 50)
    email = forms.EmailField()
    password = forms.CharField(widget=forms.PasswordInput)
    password_v = forms.CharField(widget=forms.PasswordInput, label="Confirm Password")
    try:
        affinity_group = forms.ModelChoiceField(queryset=AffinityGroup.objects.all(), initial = AffinityGroup.objects.get(ident='No'))
    except exceptions.ObjectDoesNotExist:
        nogroup = AffinityGroup(ident='No', name='None')
        nogroup.save()
        affinity_group = forms.ModelChoiceField(queryset=AffinityGroup.objects.all(), initial = AffinityGroup.objects.get(ident='No'))
    address = forms.CharField()
    zip_code = forms.IntegerField()
    heating_fuel = forms.MultipleChoiceField(widget=forms.CheckboxSelectMultiple, choices=(('oil','Fuel Oil'), ('gas', 'Natural gas'),))    
    number_of_residents = forms.IntegerField()
    house_square_feet = forms.IntegerField()
    
    def checkUsername(self, wanted):
        try:
            User.objects.get(username = wanted)
        except:
            return
        raise validators.ValidationError('Username is already taken') #% wanted

    def save(self):
        data = self.cleaned_data
        self.checkUsername(data['username'])
        if data['password'] == data['password_v']:
            user = User.objects.create_user(data['username'], data['email'], data['password'])
        else:
            raise validators.ValidationError('Passwords do not match')
        user.first_name = data['first_name']
        user.last_name = data['last_name']
        user.save()
        
        profile = user.get_profile()
        profile.address = data['address']
        profile.zip_code = data['zip_code']
        profile.house_square_footage = data['house_square_feet']
        profile.number_of_people = data['number_of_residents']
        profile.heating_fuel_type = data['heating_fuel']
        profile.save()
        data['affinity_group'].members.add(user)

        
        eco_profile = EcoProfile(user=user)
        eco_profile.save()
        
    
        
        
    
