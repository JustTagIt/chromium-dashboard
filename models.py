import datetime
import time

from google.appengine.api import memcache
from google.appengine.ext import db
#from google.appengine.ext.db import djangoforms

#from django.forms import ModelForm
from django import forms


SIMPLE_TYPES = (int, long, float, bool, dict, basestring, list)


class DictModel(db.Model):
  # def to_dict(self):
  #   return dict([(p, unicode(getattr(self, p))) for p in self.properties()])

  def to_dict(self):
    output = {}

    for key, prop in self.properties().iteritems():
      value = getattr(self, key)

      if value is None or isinstance(value, SIMPLE_TYPES):
        output[key] = value
      elif isinstance(value, datetime.date):
        # Convert date/datetime to ms-since-epoch ("new Date()").
        #ms = time.mktime(value.utctimetuple())
        #ms += getattr(value, 'microseconds', 0) / 1000
        #output[key] = int(ms)
        output[key] = unicode(value)
      elif isinstance(value, db.GeoPt):
        output[key] = {'lat': value.lat, 'lon': value.lon}
      elif isinstance(value, db.Model):
        output[key] = to_dict(value)
      else:
        raise ValueError('cannot encode ' + repr(prop))

    return output


# UMA metrics.
class StableInstance(DictModel):
  created = db.DateTimeProperty(auto_now_add=True)
  updated = db.DateTimeProperty(auto_now=True)

  property_name = db.StringProperty(required=True)
  bucket_id = db.IntegerProperty(required=True)
  date = db.DateProperty(verbose_name='When the data was fetched',
                             required=True)
  hits = db.IntegerProperty(required=True)
  total_pages = db.IntegerProperty()
  day_percentage = db.FloatProperty()
  rolling_percentage = db.FloatProperty()


# Feature dashboard.
class Feature(DictModel):
  """Container for a feature."""

  @staticmethod
  def format_for_template(self):
    d = self.to_dict()
    d['id'] = self.key().id()
    d['category'] = FEATURE_CATEGORIES[self.category]
    d['visibility'] = VISIBILITY_CHOICES[self.visibility]
    d['impl_status_chrome'] = IMPLEMENATION_STATUS[self.impl_status_chrome]
    d['ff_views'] = {'value': self.ff_views,
                     'text': VENDOR_VIEWS[self.ff_views]}
    d['ie_views'] = {'value': self.ie_views,
                     'text': VENDOR_VIEWS[self.ie_views]}
    d['safari_views'] = {'value': self.safari_views,
                         'text': VENDOR_VIEWS[self.safari_views]}
    d['standardization'] = {'value': self.standardization,
                            'text': STANDARDIZATION[self.standardization]}
    d['web_dev_views'] = {'value': self.web_dev_views,
                          'text': WEB_DEV_VIEWS[self.web_dev_views]}
    #d['owner'] = ', '.join(self.owner)
    return d

  def format_for_edit(self):
    d = self.to_dict()
    d['id'] = self.key().id
    d['owner'] = ', '.join(self.owner)
    return d

  # Metadata.
  created = db.DateTimeProperty(auto_now_add=True)
  updated = db.DateTimeProperty(auto_now=True)

  # General info.
  category = db.IntegerProperty(required=True)
  name = db.StringProperty(required=True)
  summary = db.StringProperty(required=True)

  # Chromium details.
  bug_url = db.LinkProperty()
  impl_status_chrome = db.IntegerProperty(required=True)
  shipped_milestone = db.StringProperty(required=True)

  owner = db.ListProperty(db.Email, required=True)
  footprint = db.IntegerProperty()
  visibility = db.IntegerProperty(required=True)

  #webbiness = db.IntegerProperty() # TODO: figure out what this is

  # Standards details.
  standardization = db.IntegerProperty(required=True)
  spec_link = db.LinkProperty()
  prefixed = db.BooleanProperty()

  safari_views = db.IntegerProperty(required=True)
  ie_views = db.IntegerProperty(required=True)
  ff_views = db.IntegerProperty(required=True)

  safari_views_link = db.LinkProperty()
  ff_views_link = db.LinkProperty()
  ie_views_link = db.LinkProperty()

  # Web dev details.
  web_dev_views = db.IntegerProperty()
  #doc_links = db.StringProperty()
  #tests = db.StringProperty()

  comments = db.StringProperty()


class PlaceholderCharField(forms.CharField):

  def __init__(self, *args, **kwargs):
    #super(forms.CharField, self).__init__(*args, **kwargs)

    attrs = {}
    if kwargs.get('placeholder'):
      attrs['placeholder'] = kwargs.get('placeholder')
      del kwargs['placeholder']

    label = kwargs.get('label') or ''
    if label:
      del kwargs['label']

    self.max_length = kwargs.get('max_length') or None

    super(forms.CharField, self).__init__(label=label,
        widget=forms.TextInput(attrs=attrs), *args, **kwargs)


# class PlaceholderForm(forms.Form):
#   def __init__(self, *args, **kwargs):
#     super(PlaceholderForm, self).__init__(*args, **kwargs)
     
#     for field_name in self.fields:
#      field = self.fields.get(field_name)  
#      if field:
#        if type(field.widget) in (forms.TextInput, forms.DateInput):
#          field.widget = forms.TextInput(attrs={'placeholder': field.label})


WEBCOMPONENTS = 1
MISC = 2
SECURITY = 3
MULTIMEDIA = 4
DOM = 5
FILE = 6
OFFLINE = 7
DEVICE = 8
COMMUNICATION = 9
JAVASCRIPT = 10
NETWORKING = 11
INPUT = 12
PERFORMANCE = 13
GRAPHICS = 14
CSS = 15

FEATURE_CATEGORIES = {
  CSS: 'CSS',
  WEBCOMPONENTS: 'Web Components',
  MISC: 'Misc',
  SECURITY: 'Security',
  MULTIMEDIA: 'Multimedia',
  DOM: 'DOM',
  FILE: 'File APIs',
  OFFLINE: 'Offline / Storage',
  DEVICE: 'Device',
  COMMUNICATION: 'Realtime / Communication',
  JAVASCRIPT: 'JavaScript',
  NETWORKING: 'Network / Connectivity',
  INPUT: 'User input',
  PERFORMANCE: 'Performance',
  GRAPHICS: 'Graphics',
  }

NOT_ACTIVE = 1
PROPOSED = 2
STARTED = 3
EXPERIMENTAL = 4
CANARY_DEV = 5
BETA = 6
STABLE = 7
DEPRECATED = 8

IMPLEMENATION_STATUS = {
  NOT_ACTIVE: 'No active development',
  PROPOSED: 'Proposed',
  STARTED: 'Started',
  EXPERIMENTAL: 'Experimental',
  CANARY_DEV: 'Canary / Dev channel',
  BETA: 'Beta channel',
  STABLE: 'Stable channel',
  DEPRECATED: 'Deprecated',
  }

MAJOR_NEW_API = 1
MAJOR_MINOR_NEW_API = 2
SUBSTANTIVE_CHANGES = 3
MINOR_EXISTING_CHANGES = 4
EXTREMELY_SMALL_CHANGE = 5

FOOTPRINT_CHOICES = {
  MAJOR_NEW_API: ('A major new independent API (e.g. adding a large # '
                  'independent concepts with many methods/properties/objects)'),
  MAJOR_MINOR_NEW_API: ('Major changes to an existing API OR a minor new '
                        'independent API (e.g. adding a large # of new '
                        'methods/properties or introducing new concepts to '
                        'augment an existing API)'),
  SUBSTANTIVE_CHANGES: ('Substantive changes to an existing API (e.g. small '
                        'number of new methods/properties)'),
  MINOR_EXISTING_CHANGES: (
      'Minor changes to an existing API (e.g. adding a new keyword/allowed '
      'argument to a property/method)'),
  EXTREMELY_SMALL_CHANGE: ('Extremely small tweaks to an existing API (e.g. '
                           'how existing keywords/arguments are interpreted)'),
  }

MAINSTREAM_NEWS = 1
WARRANTS_ARTICLE = 2 
IN_LARGER_ARTICLE = 3
SMALL_NUM_DEVS = 4
SUPER_SMALL = 5

VISIBILITY_CHOICES = {
  MAINSTREAM_NEWS: 'Likely in mainstream tech news',
  WARRANTS_ARTICLE: 'Warrants its own article on a site like html5rocks.com',
  IN_LARGER_ARTICLE: 'Covered as part of a larger article but not on its own',
  SMALL_NUM_DEVS: 'Only a very small number of web developers will care about',
  SUPER_SMALL: "So small it doesn't need to be covered in this dashboard.",
  }

SHIPPED = 1
IN_DEV = 2
PUBLIC_SUPPORT = 3
MIXED_SIGNALS = 4
NO_PUBLIC_SIGNALS = 5
PUBLIC_SKEPTICISM = 6
OPPOSED = 7

VENDOR_VIEWS = {
  SHIPPED: 'Shipped',
  IN_DEV: 'In development',
  PUBLIC_SUPPORT: 'Documented public support',
  MIXED_SIGNALS: 'Mixed public signals',
  NO_PUBLIC_SIGNALS: 'No public signals',
  PUBLIC_SKEPTICISM: 'Public skepticism',
  OPPOSED: 'Opposed',
  }

DEFACTO_STD = 1
ESTABLISHED_STD = 2
WORKING_DRAFT = 3
EDITORS_DRAFT = 4
PUBLIC_DISCUSSION = 5
NO_STD_OR_DISCUSSION = 6

STANDARDIZATION = {
  DEFACTO_STD: 'De-facto standard',
  ESTABLISHED_STD: 'Established standard',
  WORKING_DRAFT: 'Working draft or equivalent',
  EDITORS_DRAFT: "Editor's draft specification",
  PUBLIC_DISCUSSION: 'Public discussion',
  NO_STD_OR_DISCUSSION: 'No public discussion / Not standards track',
  }

DEV_STRONG_POSTIVE = 1
DEV_POSTIVE = 2
DEV_MIXED_SIGNALS = 3
DEV_NO_SIGNALS = 4
DEV_NEGATIVE = 5
DEV_STRONG_NEGATIVE = 6

WEB_DEV_VIEWS = {
  DEV_STRONG_POSTIVE: 'Strongly positive',
  DEV_POSTIVE: 'Positive',
  DEV_MIXED_SIGNALS: 'Mixed signals',
  DEV_NO_SIGNALS: 'No signals',
  DEV_NEGATIVE: 'Negative',
  DEV_STRONG_NEGATIVE: 'Strongly negative',
  }


class FeatureForm(forms.Form):
  
  category = forms.ChoiceField(required=True, choices=FEATURE_CATEGORIES.items())

  name = PlaceholderCharField(required=True, placeholder='Feature name')
  #feature_name = forms.CharField(required=True, label='Feature name')
  
  summary = forms.CharField(label='', required=True,
      widget=forms.Textarea(attrs={'cols': 50, 'placeholder': 'Summary'}))

  owner = PlaceholderCharField(
      required=True, placeholder='Owner(s) email',
      help_text='Owner (@chromium.org username or a full email).')
  
  bug_url = forms.URLField(label='Bug URL',
                           help_text='OWP Launch Tracking or crbug.')

  impl_status_chrome = forms.ChoiceField(required=True,
                                         label='Status in Chromium',
                                         choices=IMPLEMENATION_STATUS.items())

  shipped_milestone = forms.CharField(
      label='Earliest version full feature shipped to desktop',
      help_text='(X = not shipped yet, ? = unknown)')

  prefixed = forms.BooleanField(required=False, initial=True, label='Prefixed?')

  standardization = forms.ChoiceField(
      label='Standardization', choices=STANDARDIZATION.items(),
      initial=EDITORS_DRAFT,
      help_text=("The standardization status of the API. In bodies that don't "
                 "use this nomenclature, use the closest equivalent."))

  spec_link = forms.URLField(label='Spec link',
                             help_text="Prefer an editor's draft.")

  footprint  = forms.ChoiceField(label='Technical footprint',
                                 choices=FOOTPRINT_CHOICES.items(),
                                 initial=MAJOR_MINOR_NEW_API)

  visibility  = forms.ChoiceField(
      label='Developer visibility',
      choices=VISIBILITY_CHOICES.items(),
      initial=WARRANTS_ARTICLE,
      help_text=('How much press / media / web developer buzz will this '
                 'feature generate?'))

  web_dev_views = forms.ChoiceField(
      label='Web developer views',
      choices=WEB_DEV_VIEWS.items(),
      initial=DEV_NO_SIGNALS,
      help_text=('How positive has the reaction from developers been? If '
                 'unsure, default to "No signals".'))

  safari_views = forms.ChoiceField(label='Documented Safari views',
                                   choices=VENDOR_VIEWS.items(),
                                   initial=NO_PUBLIC_SIGNALS)
  safari_views_link = forms.URLField(label='Link')

  ff_views = forms.ChoiceField(label='Documented Firefox views',
                               choices=VENDOR_VIEWS.items(),
                               initial=NO_PUBLIC_SIGNALS)
  ff_views_link = forms.URLField(label='Link')


  ie_views = forms.ChoiceField(label='Documented IE views',
                               choices=VENDOR_VIEWS.items(),
                               initial=NO_PUBLIC_SIGNALS)
  ie_views_link = forms.URLField(label='Link')

  comments = forms.CharField(label='', required=False, widget=forms.Textarea(
      attrs={'cols': 50, 'placeholder': 'Additional Comments'}))

  class Meta:
    model = Feature
    exclude = ('safari_views_link', 'ff_views_link', 'ie_views_link',)

  def __init__(self, *args, **keyargs):
    super(FeatureForm, self).__init__(*args, **keyargs)

    meta = getattr(self, 'Meta', None)
    exclude = getattr(meta, 'exclude', [])

    for field_name in exclude:
     if field_name in self.fields:
       del self.fields[field_name]

    for field, val in self.fields.iteritems():
      if val.required:
       self.fields[field].widget.attrs['required'] = 'required'