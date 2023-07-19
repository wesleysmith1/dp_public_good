from otree.api import *


doc = """
Your app description
"""


class C(BaseConstants):
    NAME_IN_URL = 'wtp_survey'
    PLAYERS_PER_GROUP = None
    NUM_ROUNDS = 1


class Subsession(BaseSubsession):
    pass


class Group(BaseGroup):
    pass


class Player(BasePlayer):
    wtp5 = models.IntegerField(label="5")
    wtp10 = models.IntegerField(label="10")
    wtp15 = models.IntegerField(label="15")
    wtp20 = models.IntegerField(label="20")
    wtp25 = models.IntegerField(label="25")


# PAGES
class Introduction(Page):
    timeout_seconds = 20
    timer_text = 'Please wait to begin survey'


class WTPSurvey(Page):
    form_model = 'player'
    form_fields = ['wtp5', 'wtp10', 'wtp15', 'wtp20', 'wtp25']


class ResultsWaitPage(WaitPage):
    pass


class Results(Page):
    pass


page_sequence = [Introduction, WTPSurvey]
