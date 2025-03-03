from otree.api import *
from pymongo import MongoClient
import time
import pandas as pd
from vonage import Auth, Vonage
from vonage_video.models import VideoSession
from vonage_video.models import SessionOptions
from vonage_video.models import TokenOptions


author = 'Timo Promann'


app_id = "dfab0d19-xxxx-4088-xxxx-6d1df008cbc9"
private_key_path = 'C:/Users/.../VideoChatFolder/private.key'
vonage_client = Vonage(Auth(application_id=app_id, private_key=private_key_path))
client_mongo = MongoClient("mongodb+srv://username:password@cluster0.xxxxx.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0")
db_mongo = client_mongo.otreedb

doc = """
Video Chat
"""


class C(BaseConstants):
    NAME_IN_URL = 'VideoChat'
    PLAYERS_PER_GROUP = 4
    NUM_ROUNDS = 1
    pass


class Subsession(BaseSubsession):
    pass


class Group(BaseGroup):
    pass


class Player(BasePlayer):
    pass


# PAGES

class VideoChat(Page):

    @staticmethod
    def live_method(player, data):
        print('audio data testing:', data)

        d_type = data['type']
        if d_type == "noise_level":
            db_mongo.otreedb_users.insert_one(data)
        elif d_type == "start_stop_talking":
            db_mongo.otreedb_users.insert_one(data)

    def vars_for_template(player) -> dict:
        print("gruppennummer ", player.group.id_in_subsession)
        print("label ", player.participant.session.code)
        print("user session code: ", player.participant.code)
        if db_mongo.otreedb.count_documents(
                {"group": player.group.id_in_subsession,
                 "otree_session_id": player.participant.session.code,
                 "current_app": player.participant._current_app_name}) > 0:
            vonage_infos = db_mongo.otreedb.find_one(
                {"group": player.group.id_in_subsession,
                 "otree_session_id": player.participant.session.code,
                 "current_app": player.participant._current_app_name})
            print(vonage_infos['vonage_session_id'])
            vonage_token = vonage_client.video.generate_client_token(TokenOptions(session_id=vonage_infos['vonage_session_id'])).decode("utf-8")
        else:
            options = SessionOptions(media_mode='relayed')
            vonage_session: VideoSession = vonage_client.video.create_session(options)
            session_id = vonage_session.session_id
            vonage_infos = {"group": player.group.id_in_subsession,
                             "otree_session_id": player.participant.session.code,
                             "current_app": player.participant._current_app_name,
                             "vonage_session_id": session_id}
            db_mongo.otreedb.insert_one(vonage_infos)
            vonage_token = vonage_client.video.generate_client_token(TokenOptions(session_id=session_id)).decode("utf-8")

        vonage_session_id = vonage_infos['vonage_session_id']
        return dict(vonage_session_id=vonage_session_id, vonage_token=vonage_token,
                    otree_session_id=player.participant.session.code,
                    otree_user_session_id=player.participant.code, user_name="Member " + str(player.id_in_group),
                    vonage_app_id=app_id)

    @staticmethod
    def before_next_page(player, timeout_happened):
        all_users = [i for i in db_mongo.otreedb_users.find({}, {'_id': 0})]
        df = pd.DataFrame(all_users)
        df.to_csv(
            'C:/Users/.../VideoChatFolder/session_audiodata_testfile.csv')  # Replace with the path to your audio data folder.
        # df.to_csv('/home/otree/oTree/session_audiodata.csv')  # "#" needs to be removed on server

    pass



class Dummy(Page):
    pass


page_sequence = [VideoChat,
                 Dummy
                 ]
