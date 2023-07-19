from otree.api import *


doc = """
Your app description
"""


class C(BaseConstants):
    NAME_IN_URL = 'payment'
    PLAYERS_PER_GROUP = None
    NUM_ROUNDS = 1


class Subsession(BaseSubsession):
    pass


class Group(BaseGroup):
    pass


class Player(BasePlayer):
    first_name = models.StringField()
    last_name = models.StringField()

    # strategy = models.StringField(label="How did you make your decisions during the experiment?")
    # feedback = models.StringField(label="Is there anything else you would like to tell the experimenters about this experiment?")
    feedback = models.StringField(label="Is there anything you would like to tell the experimenters about this experiment?", blank=True)

    participant_code = models.StringField()
    id_in_session = models.IntegerField()


# PAGES
class SurveyWaitPage(WaitPage):
    @staticmethod
    def after_all_players_arrive(group: Group):
        # generate results here
        from payment.helpers import generate_payouts
        generate_payouts(group)


class MainSurvey(Page):
    form_model = 'player'
    form_fields = ['first_name', 'last_name', 'feedback']


class FinalWaitPage(WaitPage):
    pass


class FinalPage(Page):
    pass


page_sequence = [SurveyWaitPage, MainSurvey, FinalWaitPage, FinalPage]
