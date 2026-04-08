from os import environ

SESSION_CONFIGS = [
    dict(
        name='xi_identification',
        display_name='X/I Identification',
        app_sequence=['grid_experiment'],
        num_demo_participants=1,
        test_mode=False,
    ),
    dict(
        name='xi_identification_test',
        display_name='X/I Identification — TEST (2 main rounds)',
        app_sequence=['grid_experiment'],
        num_demo_participants=1,
        test_mode=True,
    ),
]

# dict(
 #       name='grid_experiment',
  #      display_name='Altruism Grid Experiment',
  #      app_sequence=['grid_experiment'],
   #     num_demo_participants=1,
   #     view_again_cost=0,
    #),

# if you set a property in SESSION_CONFIG_DEFAULTS, it will be inherited by all configs
# in SESSION_CONFIGS, except those that explicitly override it.
# the session config can be accessed from methods in your apps as self.session.config,
# e.g. self.session.config['participation_fee']

SESSION_CONFIG_DEFAULTS = dict(
    real_world_currency_per_point=1.00, participation_fee=5.00, doc=""
)

ROOMS = [
    dict(
        name='VCEEroom',
        display_name='VCEE Room',
    ),
]

PARTICIPANT_FIELDS = []
SESSION_FIELDS = []

# ISO-639 code
# for example: de, fr, ja, ko, zh-hans
LANGUAGE_CODE = 'en'

# e.g. EUR, GBP, CNY, JPY
REAL_WORLD_CURRENCY_CODE = 'EUR'
USE_POINTS = False

ADMIN_USERNAME = 'admin'
# for security, best to set admin password in an environment variable
ADMIN_PASSWORD = environ.get('OTREE_ADMIN_PASSWORD')

DEMO_PAGE_INTRO_HTML = """ """

SECRET_KEY = '4100987363977'
