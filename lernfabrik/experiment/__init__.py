import json
import time

import requests
from frisbee.otree_extension import server_ws, thingspeak
from otree.api import *

doc = """
Experiment in der Lernfabrik.
"""


# Configuration of the ThingSpeak Channels that will be created during the experiment
channel_config = thingspeak.ChannelConfig(api_key='KWOJ1KJ7XY5HU60C',
                                          description='Productivity',
                                          fieldX={'field1': 'Amount of produced parts',
                                                  'field2': 'Timestamps'},
                                          metadata=json.dumps({'Experimenter': 'Max Mustermann'}),
                                          name='Productivity in a Field-in-the-Lab Experiment',
                                          public_flag=False,
                                          tags=['Productivity', 'Field-in-the-Lab', 'Sensor'],
                                          url='www.otree-frisbee.com',
                                          use_participant_specific_preface=True)

# Configuration of the Frisbee
frisbee_server = server_ws.FrisbeeCom(host='127.0.0.1',
                                      port=8001,
                                      participant_label_file='_rooms/econ101.txt',
                                      channel_config=channel_config)

# Start Frisbee Server
frisbee_server.start_server()


class C(BaseConstants):
    NAME_IN_URL = 'experiment'
    PLAYERS_PER_GROUP = None
    NUM_ROUNDS = 1
    # INSTRUCTIONS_TEMPLATE = 'experiment/Assembly.html'


class Subsession(BaseSubsession):
    pass


class Group(BaseGroup):
    pass


class Player(BasePlayer):
    produced_parts = models.FloatField(initial=0)


class Productivity(ExtraModel):
    player = models.Link(Player)
    produced_parts = models.FloatField()
    timestamp = models.LongStringField()


# FUNCTIONS
def match_maker(group: Group):
    number_of_players = len(group.get_players())
    print(f'Number of Players: {number_of_players}')

    connected_clients_info = frisbee_server.get_connected_clients_info()
    print(f'Connected Clients Info: {connected_clients_info}')

    number_of_connected_participants = len(connected_clients_info)
    print(f'Number of connected participants: {number_of_connected_participants}')

    # Get All Clients
    while number_of_connected_participants != number_of_players:
        connected_clients_info = frisbee_server.get_connected_clients_info()
        number_of_connected_participants = len(connected_clients_info)

    print('Match finished')

    for player in group.get_players():
        for client in connected_clients_info:
            if client is not None and player.participant.label == client['participant_label']:
                player.participant.ch_settings = client['thingspeak_ch_settings']
                client = None  # "Delete"
                break


# PAGES
class Welcome(Page):
    pass


class Assembly(Page):
    pass


class Test(Page):
    pass


class Special(Page):

    @staticmethod
    def is_displayed(player):
        return player.id_in_group == 1


class WaitPageSensors(WaitPage):
    title_text = 'Die Hauptrunde beginnt in Kürze.'
    body_text = 'Halten Sie sich bereit.'

    @staticmethod
    def after_all_players_arrive(group: Group):
        match_maker(group)

    @staticmethod
    def before_next_page(player: Player, timeout_happened):
        frisbee_server.start_recording(player.participant.label)


class MainRound(Page):
    timeout_seconds = 15

    @staticmethod
    def is_displayed(player):
        return player.id_in_group == 2

    @staticmethod
    def before_next_page(player: Player, timeout_happened):
        frisbee_server.stop_recording(player.participant.label)


class MainRoundSpecial(Page):
    timeout_seconds = 15

    @staticmethod
    def is_displayed(player):
        return player.id_in_group == 1

    @staticmethod
    def live_method(player: Player, data):
        # other player
        other = (player.get_others_in_group())[0]
        # channel id of thingspeak channel of other player
        channel_id = other.participant.ch_settings['id']
        # read api key for reading the data from the channel
        read_api_key = other.participant.ch_settings['api_keys'][1]['api_key']
        # field where amount of produced parts is stored
        field = '1'
        # read data
        url_request = f'https://api.thingspeak.com/channels/{channel_id}/fields/{field}.json'
        data = {'api_key': read_api_key,
                'sum': '60'}
        response = requests.get(url_request, data=data)
        tmp = response.json()
        print(tmp)

        produced_parts = tmp['feeds'][0]['field1']
        print(produced_parts)


        # produced_parts = thingspeak.read_data(read_api_key=read_api_key, channel_id=channel_id, field=)

        if produced_parts != -1:
            produced_parts = float(produced_parts)
            otreetime = time.asctime()
            Productivity.create(player=other, produced_parts=produced_parts, timestamp=otreetime)
            player.produced_parts = produced_parts
            result = {
                'produced_parts': produced_parts,
            }
            return {0: result}
        else:
            return 0

    @staticmethod
    def before_next_page(player: Player, timeout_happened):
        frisbee_server.stop_recording(player.participant.label)


class End(Page):
    pass


page_sequence = [Welcome, Assembly, Test, Special, WaitPageSensors, MainRound, MainRoundSpecial, End]
