from otree.api import *
import datetime, time, math, csv

from mechanisms.income_distributions import IncomeDistributions
from mechanisms.mechanism import calculate_cost, calculate_utility

doc = """
Your app description
"""


class C(BaseConstants):
    NAME_IN_URL = 'main'
    PLAYERS_PER_GROUP = 4
    NUM_ROUNDS = 25

    # mechanism parameters ================================================

    dt_range = 10
    dt_payment_max = 10
    big_n = 4

    # ========================================

    # treatment = "OGL"
    # N = 4
    # n = 4

    treatment = "MGL"
    N = 4
    n = 2

    # treatment = "MPT"
    # N = 4
    # n = 2

    # =========================================

    q = 400
    omega = 15 # max tokens
    gamma = 15
    r = 0

    low_incomes = [1600, 2000, 2000, 2400]
    high_incomes = [3200, 4000, 4000, 4800]

    # participants that are selected to participate in each round
    sampling_matrix = [
        [1,2,3,4], # tutorial
        [1,2], # 2
        [1,2], # 3
        [1,3],
        [1,3],
        [3,4],
        [3,4], # 7
        [1,4], # 8
        [1,4], # 9
        [3,4],
        [3,4],
        [2,4],
        [2,4], # 13
        [1,2], # 14
        [1,2], 
        [1,3],
        [1,3],
        [3,4], # 18
        [3,4], # 19
        [1,4], # 20
        [1,4], 
        [3,4],
        [3,4],
        [2,4],
        [2,4],

    ]


class Subsession(BaseSubsession):
    pass


class Group(BaseGroup):
    # ==========mechanism============
    mechanism_start = models.FloatField(blank=True)
    # ===============================

    # ===========mechanism functions================

    def total_quantity(self):
        return sum(p.quantity for p in self.get_players())

    # ==============================================



class Player(BasePlayer):
    # ==========mechanism fields==================
    starting_points = models.IntegerField(initial=0)
    quantity = models.IntegerField(initial=0)
    your_cost = models.FloatField(initial=0)
    mechanism_participant = models.BooleanField(initial=False)
    nonparticipant_tax = models.FloatField(initial=0)
    your_individual_quantity = models.FloatField(initial=0)
    utility = models.FloatField(initial=0)
    participant_rebate = models.IntegerField(initial=0)
    # ============================================
    balance = models.FloatField(initial=0)


class MechanismInput(ExtraModel):
    player = models.Link(Player)
    id_in_group = models.IntegerField()
    group = models.Link(Group)
    quantity = models.IntegerField(initial=0)
    created = models.FloatField()
    round_number = models.IntegerField()

    @classmethod
    def record(cls, quantity, player_id, id_in_group, group_id, round_number):
        # update this os it is more accurate and gives player and participant information
        MechanismInput.create(player_id=player_id, id_in_group=id_in_group, group_id=group_id, round_number=round_number, quantity=quantity, created=time.time())

    @classmethod
    def csvHeader(cls):
        return [
                    "group_id", 
                    "participants",
                    "player_id", 
                    "round_number", 
                    "quantity",
                    "group_commodities", 
                    "starting_points",
                    "costs", 
                    "utilities", 
                    "individual_commodities", 
                    # "participant_rebates", 
                    "nonparticipant_taxes", 
                    "created", 
                    "treatment",
                    "gamma",
                    "price",
                    "created_withinround"
                ]

    def row(self, uo, mechanism_start, g_id):
        """g_id is the group id per group in session and always starts at 1. It is not a unique db key"""
        return [
            g_id,
            list(uo['n_id']),
            self.id_in_group,
            self.round_number - 1, # subtract 1 because of tutorial
            self.quantity, 
            uo['group_quantities'],
            uo['starting_points'],
            list(uo['participant_costs']), 
            list(uo['utility']), 
            list(uo['quantity_ind_commodity']), 
            # list(uo['participant_rebate']), 
            list(uo['nonparticipant_tax']), 
            datetime.datetime.fromtimestamp(self.created).strftime('%d/%m/%Y %H:%M:%S'), 
            C.treatment,
            uo['gamma'],
            uo['price'],
            self.created - mechanism_start if mechanism_start else self.created,
        ]

    def header(self):
        return 


# FUNCTIONS
def get_round_incomes(round_number):
    if round_number == 1:
        return C.low_incomes

    return C.high_incomes if round_number % 2 == 1 else C.low_incomes

def creating_session(subsession: Subsession):

    subsession.session.vars['session_start'] = time.time()
    subsession.session.vars['session_date'] = datetime.datetime.today().strftime('%Y%m%d')

    if subsession.round_number == 1:
        index = 1
        for group in subsession.get_groups():
            for player in group.get_players():
                player.participant.vars['group_id'] = index
            index += 1

    for g in subsession.get_groups():
        for player in g.get_players():

            # initialize balances
            player.participant.vars['balances'] = []

            income_index = player.id_in_group - 1

            incomes = get_round_incomes(g.round_number)
            
            player.starting_points = player.balance = incomes[income_index]

# PAGES
class SurveyInitWait(WaitPage):
    @staticmethod
    def after_all_players_arrive(group: Group):
        """select players that will participate in the mechanism."""

        # policing = self.session.config['include_policing']
        # if policing:
        #     selected_players = Player.objects.filter(group_id=self.group.pk).exclude(id_in_group=1)
        # else:
        selected_players = group.get_players()

        if C.treatment == "OGL":
            selected_ids = [1,2,3,4]
        else:
            selected_ids = C.sampling_matrix[group.round_number - 1]

        for p in selected_players:
            # SurveyResponse.objects.create(group=self.group, player=p, response=dict(), participant=True)
            if p.id_in_group in selected_ids:
                p.mechanism_participant=True

                # add rebate for mgl participants
                if p.mechanism_participant and C.treatment == 'MGL':
                    p.starting_points += 0
                    p.balance += 0
                

class StartModal(Page):
    timeout_seconds = 5

    @staticmethod
    def vars_for_template(player: Player):
        return dict(
            selected=player.mechanism_participant,
            your_cost=player.your_cost,
            hide_selected_text=C.N == C.n,
        )
    

class DefendTokenSurvey(Page):

    @staticmethod
    def live_method(player: Player, data):

        if data.get('quantity'):
            quantity = int(data['quantity']['quantity'])
            player.quantity = quantity

            if player.round_number == 1 and C.treatment != 'OGL':
                # in nonOGL tutorial players are split into two groups

                data = {
                        'type': 'quantity_update',
                        'player_update': {player.id: quantity},
                    }

                if player.id_in_group in [1,2]:

                    return {1: data, 2: data}

                elif player.id_in_group in [3,4]:
                    
                    return {3: data, 4: data}
            
            else:

                # TODO: exclude id 1 when policing is included
                # TODO; this needs to map to specific players when only some players are selected for mechanism
                # quantities = Player.objects.filter(group_id=group_id).order_by('id_in_group').values_list('quantity', flat=True)
                # costs = calculate_costs(Constants.N, Constants.gamma, quantities, Constants.q, mechanism="OGL")
                
                # res = {i+1: costs[i] for i in range(len(costs))}

                MechanismInput.record(quantity, player.id, player.id_in_group, player.group_id, player.round_number)

                n_id = [p.id_in_group for p in player.group.get_players() if p.mechanism_participant]

                data = {
                        'type': 'quantity_update',
                        'player_update': {player.id: quantity},
                    }
                
                quantity_data = {}
                for id in n_id:
                    quantity_data[id] = data

                return quantity_data

                # return {
                #     0: {
                #         'type': 'quantity_update',
                #         'player_update': {player.id: quantity},
                #     }
                # }
    
        elif data.get('cost'):

            if player.round_number == 1:
                # tutorial code
                players = player.group.get_players() # this is ordered by id_in_group
                quantities = [p.quantity for p in players]

                quantity = player.quantity
                # player_index = quantities.index(quantity) # i think this is breaking in the tutorial round

                if C.treatment != "OGL":
                    if player.id_in_group < 3:
                        n_id = [1,2]
                    else:
                        n_id = [3,4]
                else:
                    n_id = [1,2,3,4]

                plus = None
                minus = None
                
                if quantity < C.omega:
                    plus_quantity = quantity + 1
                    plus_quantities = quantities.copy()
                    plus_quantities[player.id_in_group-1] = plus_quantity
                    plus = calculate_cost(
                            C.N, 
                            C.gamma, 
                            plus_quantities, 
                            plus_quantity, 
                            C.q, 
                            n_id,
                            mechanism=C.treatment,
                        )
                
                if quantity > 0:
                    minus_quantity = quantity - 1
                    minus_quantities = quantities.copy()
                    minus_quantities[player.id_in_group-1] = minus_quantity
                    minus = calculate_cost(
                            C.N, 
                            C.gamma, 
                            minus_quantities, 
                            minus_quantity, 
                            C.q, 
                            n_id,
                            mechanism=C.treatment,
                        )

                cost = calculate_cost(C.N, C.gamma, quantities, quantity, C.q, n_id, mechanism=C.treatment)

                #=====================================

                balances = [p.balance for p in players]

                utilities = calculate_utility(
                        C.N,
                        C.q,
                        C.gamma,
                        list(quantities), 
                        r=C.r,
                        betai = list(balances),
                        n_id = n_id,
                        mechanism = C.treatment
                        )
                
                utility = utilities['utility'][player.id_in_group-1]

                cost2 = utilities['participant_costs'][player.id_in_group-1]

                #=====================================

                return { player.id_in_group: {
                        'type': 'cost_update',
                        'cost': cost,
                        'plus': plus,
                        'minus': minus,
                        'utility': utility,
                        'cost2': cost2,
                    }}
            
            else:
                # non tutorial code
                players = player.group.get_players() # this is ordered by id_in_group
                quantities = [p.quantity for p in players]

                # participants = Player.filter(group=player.group, mechanism_participant=True)
                participants = [p for p in player.group.get_players() if p.mechanism_participant]
                n_id = [p.id_in_group for p in participants]

                quantity = player.quantity

                plus = None
                minus = None

                if quantity < C.omega:
                    plus_quantity = quantity + 1
                    plus_quantities = quantities.copy()
                    plus_quantities[player.id_in_group-1] = plus_quantity
                    # print(f"PLUS ID{player.id_in_group}, {plus_quantities}, {plus_quantity}, {n_id}")
                    plus = calculate_cost(
                            C.N, 
                            C.gamma, 
                            plus_quantities, 
                            plus_quantity, 
                            C.q, 
                            n_id,
                            mechanism=C.treatment
                        )
                    
                    # print(f"PLUS {plus}")
                
                if quantity > 0:
                    minus_quantity = quantity - 1
                    minus_quantities = quantities.copy()
                    minus_quantities[player.id_in_group-1] = minus_quantity
                    # print(f"MINUS ID{player.id_in_group}, {plus_quantities}, {minus_quantity}, {n_id}")
                    minus = calculate_cost(
                            C.N, 
                            C.gamma, 
                            minus_quantities, 
                            minus_quantity, 
                            C.q, 
                            n_id,
                            mechanism=C.treatment
                        )
                    
                    # print(f"MINUS {minus}")

                # print(f"COST ID{player.id_in_group}, {plus_quantities}, {quantity}, {n_id}")
                cost = calculate_cost(C.N, C.gamma, quantities, quantity, C.q, n_id, mechanism=C.treatment)

                # print(f"====================GID: {group_id}")

                balances = [p.balance for p in players]

                # print(f"BALANCES {balances}")

                # print(balances)
                utilities = calculate_utility(
                        C.N,
                        C.q,
                        C.gamma,
                        list(quantities), 
                        r=C.r,
                        betai = list(balances),
                        n_id = n_id,
                        mechanism = C.treatment
                        )

                # print(f"UTILITIES {utilities}")
                
                utility = utilities['utility'][player.id_in_group-1]

                cost2 = utilities['participant_costs'][player.id_in_group-1]

                data = {'type': 'cost_update',
                        'cost': cost,
                        'plus': plus,
                        'minus': minus,
                        'utility': utility,
                        'cost2': cost2,}

                return { player.id_in_group: {
                        'type': 'cost_update',
                        'cost': cost,
                        'plus': plus,
                        'minus': minus,
                        'utility': utility,
                        'cost2': cost2,
                    }}

    @staticmethod
    def get_timeout_seconds(player: Player):
        if player.round_number == 1:
            return None
        else:
            return 45

    @staticmethod
    def vars_for_template(player: Player):

        if player.id_in_group == 1 and not player.group.field_maybe_none('mechanism_start'):
            player.group.mechanism_start = time.time()

        constants = dict(
            N=C.N,
            n=C.n,
            q=C.q,
            gamma=C.gamma,
            r=C.r,
        )

        template_vars = dict(
            selected=player.mechanism_participant,
            dt_range=C.dt_range,
            dt_payment_max=C.dt_payment_max,
            big_n=C.PLAYERS_PER_GROUP-1,
            gamma=C.gamma,
            omega=C.omega,
            constants=constants,
        )

        return template_vars


class DefendTokenWaitPage(WaitPage):
    timeout_seconds = 80 
    timer_text = 'Please wait for round to start'

    @staticmethod
    def after_all_players_arrive(group: Group):
        """calculate how many defend tokens are going to be used, costs and tax.
        Individual survey tax is saved to survey objects here, but not applied
        until after round, when tax is recalculated to include costs accrued during round"""

        # calculate fields for all players
        quantities = [p.quantity for p in group.get_players()]
        balances = [p.balance for p in group.get_players()]

        participants = [p for p in group.get_players() if p.mechanism_participant]
        nonparticipants = [p for p in group.get_players() if not p.mechanism_participant]

        g_id = participants[0].participant.vars['group_id']

        if group.round_number == 1 and C.treatment != 'OGL':

            utilities = calculate_utility(
                C.N,
                C.q,
                C.gamma,
                list(quantities), 
                r=C.r,
                betai = list(balances),
                n_id = [1,2],
                mechanism = C.treatment
                )

            for player in participants:
                if player.id_in_group in [1,2]:
                    player.your_cost = utilities['participant_costs'][player.id_in_group-1]
                    player.your_individual_quantity = utilities['quantity_ind_commodity'][player.id_in_group-1]
                    player.utility = utilities['utility'][player.id_in_group-1]
                    player.participant_rebate = C.r
            
            utilities = calculate_utility(
                C.N,
                C.q,
                C.gamma,
                list(quantities), 
                r=C.r,
                betai = list(balances),
                n_id = [3,4],
                mechanism = C.treatment
                )
            
            for player in participants:
                if player.id_in_group in [3,4]:
                    player.your_cost = utilities['participant_costs'][player.id_in_group-1]
                    player.your_individual_quantity = utilities['quantity_ind_commodity'][player.id_in_group-1]
                    player.utility = utilities['utility'][player.id_in_group-1]
                    player.participant_rebate = C.r
        else:
            utilities = calculate_utility(
                C.N,
                C.q,
                C.gamma,
                list(quantities), 
                r=C.r,
                betai = list(balances),
                n_id = [p.id_in_group for p in group.get_players() if p.mechanism_participant],
                mechanism = C.treatment
                )

            # note this code does not work if there is an officer!

            for player in participants:
                player.your_cost = utilities['participant_costs'][player.id_in_group-1]
                player.your_individual_quantity = utilities['quantity_ind_commodity'][player.id_in_group-1]
                player.utility = utilities['utility'][player.id_in_group-1]

            for player in nonparticipants:
                player.nonparticipant_tax = utilities['nonparticipant_tax'][player.id_in_group-1]
                player.utility = utilities['utility'][player.id_in_group-1]
                player.your_cost = utilities['participant_costs'][player.id_in_group-1]
                player.your_individual_quantity = utilities['quantity_ind_commodity'][player.id_in_group-1]

        # write csv code for the round

        session_start=group.session.vars['session_start']
        session_date=group.session.vars['session_date']

        if 'session_identifier' in group.session.config:
            from mechanisms.helpers import write_session_dir, TimeFormatter
            file_path = write_session_dir(group.session.config['session_identifier'])
        else:
            file_path = 'data/'

        mechanism_inputs = MechanismInput.filter(group=group)
        mechanism_inputs = sorted(mechanism_inputs, key=lambda x: x.created)

        # n_id = list(participants.values_list('id_in_group', flat=True))
        n_id = [p.id_in_group for p in group.get_players() if p.mechanism_participant]
        # balances = get_round_incomes(self.round_number)

        start = math.floor(session_start)
        file_name = "{}Session_{}_Group_{}_{}_{}.csv".format(file_path, group.session.id, player.participant.vars['group_id'], session_date, start)

        f = open(file_name, 'a', newline='')
        
        with f:
            writer = csv.writer(f)

            # write header
            if group.round_number == 1: #todo: adjust this to exclude practice rounds
                writer.writerow(MechanismInput.csvHeader())

            group_quantities = [0,0,0,0]
            for mi in mechanism_inputs:

                # update group quantities
                group_quantities[mi.id_in_group-1] = mi.quantity

                utility_obj = calculate_utility(
                    C.N,
                    C.q,
                    C.gamma,
                    group_quantities, 
                    r=C.r,
                    betai = list(balances),
                    n_id = n_id,
                    mechanism = C.treatment
                )

                if group.round_number != 1:
                    writer.writerow(mi.row(utility_obj, group.mechanism_start, g_id))

        # update player balance to their calculated utility
        for player in group.get_players():
            player.balance = player.utility
            
            # players cannot earn a utility less than 0
            player.balance = 0 if player.balance < 0 else player.balance


class EndModal(Page):
    @staticmethod
    def get_timeout_seconds(player: Player):
        if player.round_number == 1:
            return None
        else:
            return 10

    @staticmethod
    def vars_for_template(player: Player):

        # tutorial everyone is a participant so totals are taken from subgroups
        if player.round_number == 1 and C.treatment != 'OGL':
            if player.id_in_group in [1,2]:
                total_quantity = player.group.get_player_by_id(1).quantity + player.group.get_player_by_id(2).quantity
            else:
                total_quantity = player.group.get_player_by_id(3).quantity + player.group.get_player_by_id(4).quantity
        else:
            total_quantity = player.group.total_quantity()

        
        return dict(
            mechanism_object=dict(
                your_quantity=player.quantity, 
                your_cost=player.your_cost,
                total_quantity=total_quantity,
                nonparticipant_tax=player.nonparticipant_tax,
                individual_quantity=player.your_individual_quantity,
                utility=player.utility,
                participant_rebate=player.participant_rebate,
                treatment=C.treatment,
                balance=player.balance,
                participant=player.mechanism_participant
            )
        )
    

class Wait(WaitPage):
    pass


class ResultsWaitPage(WaitPage):
    def after_all_players_arrive(self):
        # # recalculate taxes and update player balances

        if self.round_number != 1:
            for player in self.group.get_players():
                player.participant.vars['balances'].append(math.floor(player.balance))

#=========================================End mechanism pages=====================================================



page_sequence = [
        SurveyInitWait,
        Wait,
        StartModal,
        Wait,
        DefendTokenSurvey,
        DefendTokenWaitPage,
        Wait,
        EndModal,
        ResultsWaitPage,
]
