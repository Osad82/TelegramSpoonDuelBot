
import threading
import struct
import sqlite3
import os
import time
import random
import sys
import logging
import asyncio
import configparser
from telethon import TelegramClient, events

from telethon.tl.types import (
    Channel, ChannelForbidden, Chat, ChatEmpty, ChatForbidden, ChatFull, ChatPhoto,
    PeerChannel, InputPeerChat, InputPeerUser, InputPeerEmpty,
    MessageMediaDocument, MessageMediaPhoto, PeerChannel, InputChannel,
    UserEmpty, InputUser, InputUserEmpty, InputUserSelf, InputPeerSelf,
    PeerChat, PeerUser, User, UserFull, UserProfilePhoto, Document,
    MessageMediaContact, MessageMediaEmpty, MessageMediaGame, MessageMediaGeo,
    MessageMediaUnsupported, MessageMediaVenue, InputMediaContact,
    InputMediaDocument, InputMediaEmpty, InputMediaGame,
    InputMediaGeoPoint, InputMediaPhoto, InputMediaVenue, InputDocument,
    DocumentEmpty, InputDocumentEmpty, Message, GeoPoint, InputGeoPoint,
    GeoPointEmpty, InputGeoPointEmpty, Photo, InputPhoto, PhotoEmpty,
    InputPhotoEmpty, ChatPhotoEmpty, UserProfilePhotoEmpty, InputMediaUploadedDocument, ChannelFull,
    InputMediaUploadedPhoto, DocumentAttributeFilename, photos,
    TopPeer, InputNotifyPeer, UserStatusOnline, UserStatusOffline, InputMessageID, MessageEntityCode, UserStatusEmpty, UserStatusRecently, UserStatusLastWeek, UserStatusLastMonth
)
from telethon.tl.functions import *
from telethon.tl.types import MessageMediaDocument
from telethon.tl.functions.channels import EditBannedRequest,DeleteMessagesRequest
from telethon.tl.functions.messages import SendMessageRequest, EditMessageRequest
from telethon.tl.types import InputMessageEntityMentionName
from telethon.tl.functions.users import GetFullUserRequest
from telethon.tl.types import MessageEntityTextUrl
from telethon.tl.types import MessageEntityMentionName
from telethon.tl.functions.channels import GetMessagesRequest
from telethon.tl.types import MessageEntityUnknown
from telethon.tl.types import UserStatusOnline
from telethon.tl.types import MessageEntityItalic
from telethon.tl.types import ReplyInlineMarkup
from telethon.tl.types import KeyboardButtonRow
from telethon.tl.types import KeyboardButtonCallback
from telethon.tl.types import KeyboardButtonSwitchInline
from telethon.tl.functions.messages import EditInlineBotMessageRequest
from telethon.tl.functions.messages import SendInlineBotResultRequest
from telethon.tl.types import InputBotInlineMessageID
from telethon.tl.functions.messages import SetBotCallbackAnswerRequest
from telethon.tl.functions.channels import GetParticipantsRequest
from telethon.tl.types import ChannelParticipantsSearch
from telethon.tl.functions.channels import GetFullChannelRequest
from telethon.tl.types import MessageEntityBold
from telethon.tl.functions.channels import GetAdminedPublicChannelsRequest
from telethon.tl.functions.channels import GetParticipantRequest
from telethon.tl.types import ChannelParticipantAdmin
from telethon.tl.types import ChannelParticipantCreator
from telethon.tl.types import UpdateBotInlineQuery
from telethon.tl.functions.messages import SetInlineBotResultsRequest
from telethon.tl.types import InputBotInlineResult
from telethon.tl.types import InputBotInlineMessageText
from telethon.tl.types import InputWebDocument
from telethon.tl.types import DocumentAttributeImageSize
from telethon.tl.functions.messages import SendMediaRequest

API_ID = None#
API_HASH = None#
BOT_TOKEN = None#
client = None# bot.session file will be created; do not delete!
conn = None # gamelogs.sqlite file will be created; do not delete it too!
                # there are 5 fields in the table named GameScores:
                # name      |   the name of each player by the time of his first game
                # user_id   |   the id of each player
                # score     |   the score of each player
                # kicked    |   whether the player has been kicked from the Tournament; default value: 0
                # round     |   the round of the player participating in the Tournament; if kicked set to 0; default value: 1
cursor = None
help_message="Я стану секундантом в твоей дуэли, если захочешь показать негодяям, кто тут главный. Просто ответь " \
             "на сообщение оппонента 'Вызываю тебя на дуэль!' - дословно и без кавычек: " \
             "я чувствителен к регистру и к лишним символам. Я оповещу оппонента " \
             "сообщением с двумя кнопками. Чтобы начать дуэль, оппонент должен принять твой вызов, нажав " \
             "на ❤️️. Если кто-то из вас двоих нажмёт на 💔, дуэль не состоится.\n\n" \
             "Далее отправляйте друг другу сообщения с эмодзи-ложками. Каждое " \
             "отправленное сообщение с ложкой с вероятностью 35% окажется фатальным для противника " \
             "и приведёт к его поражению, о чем я вас незамедлительно оповещу.\n\n❗️Нет необходимости " \
             "отправлять много ложек в одном сообщении или присылать ложки после оповещения о поражении.\n\n" \
             "Обратная связь: @themaster44"
tournament_help_message="Турнир - состязание на ложках, состоящее из нескольких раундов. Каждый раз " \
                        "игроки сражаются с противником, находящемся в том же рауне, что и они. Бот " \
                        "автоматически определяет принадлежость двух противников к одному раунду. В " \
                        "результате сражения проигравший навсегда выбывает из турнира, а победитель " \
                        "двигается на один раунд вперёд."
begin_phrase="был вызван на дуэль! Бери ложку и защищайся!\n\n" \
                 "Правила дуэли: вы и соперник отправляете друг другу смайл '🥄' " \
                 "до тех пор, пока я не скажу, что кто-то из вас победил.\n\n" \
                 "❤️️ - Принять вызов!\n💔 - Аннулировать вызов!"
end_phrases=["Противник убит прямым попаданием в голову!"
             "Соперник съеден ложкой.",
             "Голова соперника не выдерживает натиск металла и лопается!",
             "Вы разбили голову противника и теперь с наслаждением пробуете на вкус его мозги.",
             "Оказывается, глаза соперника идеально подходят для выковыривания ложкой!",
             "Вы закормили соперника досмерти мёдом.",
             "Ваш оппонент подавился ложкой. Насмерть.",
             "Вы использовали ложку для превращения соперника в отбивную!",
             "Ещё один кусает пыль!",
             "Ваш соперник испугался вашей огромной ложки и благоразумно решил капитулировать.",
             "Ваша ложка настолько велика и устрашающа, что соперник сам сдался.",
             "При виде вашей большой ложки противнику стало стыдно, и он убежал.",
             "Вы задушили соперника своей алюминиевой ложкой!",
             "Вы пытали противника несколько часов с помощью ложки, и он умер.",
             "Вы заставили соперника выкопать себе могилу своей же ложкой!",
             "Вы накормили противника с ложки супом из мухоморов!",
             "Ложка взорвалась и убила соперника насмерть.",
             "Соперник был зверски избит ложкой и убежал плакать.",
             "Ложка вырвалась у вас из рук и вцепилась своими зазубринами прямо в глотку противнику!",
             "Вы взглядом согнули ложку соперника...",
             "Ложка соперника оказалась зачарована на неудачу, поэтому он проиграл.",
             "Бог всех Ложек, Черпаков и Ложечек сошёл с небес и покарал соперника!",
             "Соперник испугался своего отражения в ложке и умер от страха!",
             "Ложка соперника оказалась мусульманкой и взорвалась.",
             "У соперника была слишком маленькая ложечка...",
             "Противник сказал, что ложки нет. Ну, по крайней мере, его собственной.",
             "Противник открыл коробочку, а там ложка ему по лицу даёт.",
             "Ложка противника внезапно оказалась сделанной из урана-238.",
             "Ложка соперника вызвала меметическое заражение и недееспособность соперника.",
             "Магнит в на борту пролетавшего мимо НЛО вырвал ложечку соперника из рук и воткнул её прямо в серце.",
             "У врага отняли ложку и обозвали угнетателем проходившие мимо форкистки.",
             "Ложка соперника оказалась шоколадной и растаяла прямо у него в руках.",
             "Противник не понял, чё надо делать с ложкой, и вы его победили!",
             "Ваша ложка сказала противнику то, чего он боялся услышать больше всего. Противник морально умер.",
             "Ложка противника оказалась бракованной, и он не смог вас одолеть.",
             "Противник оказался австралийским аборигеном и не умеет пользоваться ложками.",
             "Противник отказался защищаться ложкой из-за своего вероисповедания.",
             "Ваша ложка соблазнила ложку соперника, а потом коварно её умертвила!"
             ]
preferences_message="С помощью этого сообщения администраторы чата могут настроить меня, " \
                    "чтобы я работал так, как им угодно. Для этого внизу я оставил кнопки-" \
                    "переключатели, назначение которых сейчас поясню.\n\n" \
                    "Удалять сразу : должен ли бот удалять сразу же все сообщения, содержа" \
                    "щие ложку-эмоджи. Функция полезна для предотвращения флуда в чате.\n" \
                    "Удалять после дуэли : должен ли бот удалять сообщения с ложками-эмоджи," \
                    " отправленными во время дуэли.\n\n❗️Заметьте, что надпись на кнопке указывает" \
                    " на то, что именно будет приводиться в исполнение после нажатия на кнопку.\n\n❗️" \
                    "Заметьте, что данные функции будут приводиться в исполнение только после выдачи" \
                    " боту прав администратора."
peers=[]
win_probability_percents=35
logging.basicConfig(level=logging.WARNING)