'''
ECOLOGICAL IMPACT TRACKER - USER REGISTRATION MODELS
By Noah Weinthal '15 - Swarthmore College
Released as free and open source software under the terms of the GPL
'''
from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.core import validators

'''
CLASS    AffinityGroup
DESC     A simple grouping of individual users used to aggregate impact data.
'''
class AffinityGroup(models.Model): # TODO - Rename as Green Group
    ident = models.CharField(max_length=10)
    name = models.CharField(max_length=50)
    members = models.ManyToManyField(User, null=True)

    '''
    FUNC        unicode
    PARAMS      None
    DESC        returns unicode description of model, in this case, group name
    '''
    def __unicode__(self):
        return self.name
    
    '''
    FUNC    getUsers
    PARAMS  None
    DESC    returns iterable object list of all users in a group
    '''
    def getUsers(self):
        return self.members.all()
    
    '''
    FUNC    getMonthlyData
    PARAMS  datetime 'start_date', datetime 'end_date'
    DESC    returns summed aggreage data for each eco profile matching dates
            for each user in group.  TODO - optimize to less than O(n^2)
    '''
    def getMonthlyData(start_date, end_date, self):
        data = {'gr_water': 0,
                'gr_gas': 0,
                'gr_electric': 0,
                'gr_trash': 0,
                'gr_natgas': 0,
                'gr_oil': 0
                }
        users_in_group = getUsers(self)
        for this_user in users_in_group:
            user_profiles = EcoProfile.objects.filter(user=this_user)
            for user_profile in user_profiles:
                if (user_profile.current_month <= end_date and 
                    user_profile.current_month >= start_date):
                    try:
                        data['gr_water'] += user_profile.water_this_month
                        data['gr_gas'] += user_profile.gas_this_month
                        data['gr_electric'] += user_profile.electricity_this_month
                        data['gr_trash'] += user_profile.pounds_of_trash
                        data['gr_natgas'] += user_profile.natural_gas
                        data['gr_oil'] += user_profile.heating_oil
                        
                    except KeyError as val:
                        log('KeyError for user: ' + str(user_profile.user)
                              + ' in  getMonthlyData while '
                              + 'looking up value ' + str(val), True
                            )
                        continue
        return data
                                
        
'''
CLASS     EcoProfile
DESC      A month-specific profile or 'snapshot' of usage data for each user.
          Stores environmental data for given month and saves it to the server.
'''   
class EcoProfile(models.Model):
    #Worked with a Sustainability Coach - Boolean
    user = models.ForeignKey(User)
    current_month = models.DateField(null=True)
    water_this_month = models.IntegerField(null=True)
    gas_this_month = models.IntegerField(null=True)
    electricity_this_month = models.IntegerField(null=True)
    pounds_of_trash = models.IntegerField(null=True)
    natural_gas = models.IntegerField(null=True)
    heating_oil = models.IntegerField(null=True)
    
    def __unicode__(self):
        un = self.user.username
        date = self.current_month
        datestring = str(date)
        return un + ' ' + datestring
    
    def getImpactScore(self):
        try:
            score = int((self.electricity_this_month/10+2*self.gas_this_month+self.water_this_month/60+self.pounds_of_trash/5+self.heating_oil/5+self.natural_gas/5))
        except:
            raise validators.ValidationError('Empty Impact Score')
        return score
        
'''
CLASS    UserProfile
DESC     Defines user-specific that isn't often changed.  House SQft and number
         of occupants may be changed with the user update form to account for 
         changes in residential situations.  Other changes currently require
         admin attention
'''
class UserProfile(models.Model):
    user                    =  models.OneToOneField(User)
    address                 = models.CharField(max_length=35, default="Ex: 500 College Ave, Swarthmore PA")
    zip_code                = models.IntegerField(max_length=5, default="19081")
    number_of_people        = models.IntegerField(null=True) 
    house_square_footage    = models.IntegerField(null=True)
    heating_fuel_type       = models.CharField(max_length=15)
    is_leader               = models.BooleanField(default=False)
    # Add multi-fields of interest
    
    def __unicode__(self):
        return self.user.username

    
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.create(user=instance)
post_save.connect(create_user_profile, sender=User)
 

    
def log(message, warn = False):
    try:
        logfile = open("/var/www/media/django_log", "a")
        try:
            if not warn:
                logfile.write(str(datetime.datetime.now()) + ' in registration/models.py: ' + message + '\n')
            else:
                logfile.write(str(datetime.datetime.now()) + ' in registration/models.py: WARNING: ' + message + '\n')
        finally:
            logfile.close()
    except IOError, err:
        raise IOError(str(err))