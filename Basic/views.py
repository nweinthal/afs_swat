from django.template import Context
from django.contrib.auth import logout
from django.template.loader import *
from django.http import HttpResponse
from django.shortcuts import render_to_response
from django.shortcuts import render
from django.http import HttpResponseRedirect
from django.contrib.auth.decorators import login_required
from registration.forms import RegistrationForm
from registration.forms import UserUpdateForm
from registration.forms import RecordRetrieveForm
from django.core.validators import ValidationError
from django.db.models import Sum
from registration.models import EcoProfile
from registration.models import UserProfile
from registration.models import AffinityGroup
from django.contrib.auth.models import User
from django.http import HttpRequest
from django.core import exceptions
import calendar
import datetime

def hello(request):
    return HttpResponse("Server Test Page: Test Succesful")

def now(request):
    html = "<html><body>It is now %s. </body></html>" % datetime.datetime.now()
    return HttpResponse(html)

def createUser(request):
    if request.method == 'POST': # If the form has been submitted...
        form = RegistrationForm(request.POST) # A form bound to the POST data
        if form.is_valid(): # All validation rules pass
            try:
                form.save()
            except ValidationError, err:
                error = unicode(err)
                return render(request, 'createuser.html', {'form': form, 'error': error})
            return HttpResponseRedirect('/thanks/') # Redirect after POST
    else:
        form = RegistrationForm() # An unbound form

    return render(request, 'createuser.html', {
        'form': form,
    })
    
@login_required
def groupPage(request):
    profile = UserProfile.objects.get(user = request.user)
    
    
@login_required
def profile(request):
    name = request.user.first_name
    epq = EcoProfile.objects.filter(user=request.user) #EcoProfile queryset for user
    gas = epq.aggregate(Sum('gas_this_month')).values()[0]
    water = epq.aggregate(Sum('water_this_month')).values()[0]
    kwh = epq.aggregate(Sum('electricity_this_month')).values()[0]
    trash = epq.aggregate(Sum('pounds_of_trash')).values()[0]
    heatoil = epq.aggregate(Sum('heating_oil')).values()[0] #TODO Get Units For This!
    natgas = epq.aggregate(Sum('natural_gas')).values()[0]
    try:
        greenscore =  int((kwh/10+2*gas+water/60+trash/5+natgas)/(5*len(epq)))
    except:
        greenscore = 'Enter Data to get Score'
    heights, scores, months = graphHeights(request.user)
    spacer_heights = list()
    for height in heights:
        spacer_heights.append(100 - height)
    
    all_heights = list()
    for i in range(0,len(heights)):
        all_heights.append((heights[i], spacer_heights[i], int(scores[i]), months[i]))
        
    render_dict = {'green_score': greenscore,
                   'water_gal': water,
                   'gas_gal': gas,
                   'kwh': kwh,
                   'trash': trash,
                   'natgas': natgas,
                   'username': name,
                   'title': ' - My Profile',
                   'logged_in':True,
                   'graph_stat': 'verify',
                   'heights': all_heights,
                   'scores' : scores,
                   }
    return render_to_response('registration/profile.html', render_dict)#'registration/profile.html', render_dict)

def logout_view(request):
    if not request.user.is_authenticated():
        return createUser(request)
    else:
        logout(request)
        return render_to_response('registration/logout.html', {})

def thanks(request):
    return render_to_response('thanks.html', {})


@login_required
def update(request):
    flag = 'month_date_month' in request.GET and 'month_date_year' in request.GET
    if request.method == 'GET' and flag:
        month_date_month = int(request.GET['month_date_month'])
        month_date_year = int(request.GET['month_date_year'])
        if month_date_month and month_date_year:
            record_date = datetime.date(month_date_year, month_date_month, 1) #(YYYY, MM, DD)
            eco_profiles_for_user = EcoProfile.objects.filter(user = request.user)
            try:
                eco_profile = eco_profiles_for_user.get(current_month = record_date)
                form = UserUpdateForm(initial = getInitialDataFor(eco_profile, request.user))
                message = "Step 2: Update your record from " + str(month_date_month) + "/" + str(month_date_year)
                return render(request, 'registration/update.html', {'message': message, 
                                                                    'form': form,
                                                                    'form_method': 'POST',
                                                                    },)
            except exceptions.ObjectDoesNotExist:
                eco_profile = EcoProfile()
                eco_profile.current_month = record_date
                form = UserUpdateForm(initial = getInitialDataFor(eco_profile, request.user))
                message = "Step 2: Create a record for " + str(month_date_month) + "/" + str(month_date_year)
                return render(request, 'registration/update.html', {'message': message, 
                                                                    'form': form,
                                                                    'form_method': 'POST',
                                                                    },)
    elif request.method == 'POST':
        sub_form = UserUpdateForm(request.POST)
        if sub_form.is_valid():
            data = sub_form.cleaned_data
            if recordExistsFor(request.user, sub_form.cleaned_data):
                updateData(request.user, sub_form.cleaned_data, 'update')
            else:
                updateData(request.user, sub_form.cleaned_data, 'new')
            return render(request, 'registration/update.html', {'form': RecordRetrieveForm(),
                                                       'message': 'Submission Recorded Successfully! \
                                                       Choose another month or visit your profile to view more info',
                                                       'form_method': 'GET',
                                                       })
        else:
            return render(request, 'registration/update.html', {'form': RecordRetrieveForm(),
                                                       'message': 'There was an error processing your form.  Please try again',
                                                       'form_method': 'GET',
                                                       })
    return render(request, 'registration/update.html', {'form': RecordRetrieveForm(), 
                                                            'message': "Step 1: Select a month/year combination",
                                                            'form_method': 'GET',
                                                            })
    

def recordExistsFor(usr, data):    
    record_date = data['date_on_bills']
    recs_for_user = EcoProfile.objects.filter(user = usr)
    try:
        recs_for_user.get(current_month = record_date)
    except:
        return False
    return True

def updateData(usr, data, method):
    record_date = data['date_on_bills']
    usp = UserProfile.objects.get(user=usr)
    if method == 'update':
        assert(recordExistsFor(usr, data))
        record = EcoProfile.objects.filter(user = usr).get(current_month = record_date)
    elif method == 'new':
        record = EcoProfile(user = usr)
    record.current_month = record_date
    record.water_this_month = data['water_bill']
    record.gas_this_month = data['gas']
    record.electricity_this_month = data['electric_bill']
    record.pounds_of_trash = data['trash_weight']
    record.natural_gas = data['natural_gas']
    record.heating_oil = data['heating_oil']
    usp.house_square_footage = data['house_sq']
    usp.number_of_people = data['occupants']
    usp.save()
    record.save()
    
def getInitialDataFor(ecp, usr):
    usp = UserProfile.objects.get(user = usr)
    initial = {'date_on_bills': str(ecp.current_month),
        'water_bill':       str(ecp.water_this_month or 0),      
        'electric_bill':    str(ecp.electricity_this_month or 0),  
        'trash_weight':     str(ecp.pounds_of_trash or 0),
        'gas':              str(ecp.gas_this_month or 0), 
        'natural_gas':      str(ecp.natural_gas or 0),     
        'heating_oi':       str(ecp.heating_oil or 0),
        'house_sq':         str(usp.house_square_footage),
        'occupants':        str(usp.number_of_people)
    }
    return initial
    

def graphHeights(usr):
    ecps = EcoProfile.objects.filter(user = usr).order_by('current_month')
    entries = len(ecps)
    try:
        last_6 = ecps[entries-6:entries]
    except:
        last_6 = ecps
    impact_scores = list()
    months = list()
    for record in last_6:
        try:
            impact_scores.append(float(record.getImpactScore()))
            months.append(calendar.month_abbr[record.current_month.month] + ' \'' + str(record.current_month.year)[2:4])
        except:
            impact_scores.append(0)
            months.append('')
    heights = list()
    for score in impact_scores:
        try:
            heights.append(5+score/max(impact_scores)*85)
        except:
            heights.append(0)
    return heights, impact_scores, months

def createGroupGraphs(usr):
    return



def log(message, warn = False):
    try:
        logfile = open("/var/www/media/django_log", "a")
        try:
            if not warn:
                logfile.write(str(datetime.datetime.now()) + ' in views.py: ' + message + '\n')
            else:
                logfile.write(str(datetime.datetime.now()) + ' in views.py: WARNING: ' + message + '\n')
        finally:
            logfile.close()
    except IOError, err:
        raise IOError(str(err))
    
