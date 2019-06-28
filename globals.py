#encoding: utf8
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
from telethon.tl.functions import *
from telethon.tl.functions.channels import GetMessagesRequest
from telethon.tl.types import ReplyInlineMarkup
from telethon.tl.types import KeyboardButtonRow
from telethon.tl.types import KeyboardButtonCallback
from telethon.tl.types import KeyboardButtonSwitchInline
from telethon.tl.functions.messages import SetBotCallbackAnswerRequest
from telethon.tl.functions.channels import GetParticipantRequest
from telethon.tl.functions.channels import GetParticipantsRequest
from telethon.tl.types import ChannelParticipantAdmin
from telethon.tl.types import ChannelParticipantCreator
from telethon.tl.types import ChannelParticipantsSearch
from telethon.tl.types import MessageEntityBold
import test_google
from telethon.extensions import markdown

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
help_message="Я стану **секундантом** в твоей дуэли, если захочешь показать негодяям, кто тут главный. Просто ответь " \
             "на сообщение оппонента `Вызываю тебя на дуэль!` - дословно: " \
             "я чувствителен к регистру и к лишним символам. Также можешь ответить на его сообщение командой /call@spoonduelbot." \
             " Ответить значит **ответить реплаем.** Я оповещу оппонента " \
             "сообщением с двумя кнопками. Чтобы начать дуэль, оппонент должен принять твой вызов, нажав " \
             "на ❤️️. Если кто-то из вас двоих нажмёт на 💔, дуэль не состоится.\n\n" \
             "Далее отправляйте друг другу сообщения с эмодзи-ложками. Каждое " \
             "отправленное сообщение с ложкой с вероятностью 35% окажется фатальным для противника " \
             "и приведёт к его поражению, о чем я вас незамедлительно оповещу.\n\n__❗️Нет необходимости " \
             "отправлять много ложек в одном сообщении или присылать ложки после оповещения о поражении.__\n\n" \
             "__❗️На каждую дуэль даётся одна минута, по истечению которой я волен остановить сражение, " \
             "если это будет необходимо.__\n\nОбратная связь: @themaster44"
tournament_help_message="**Турнир** - состязание на ложках, состоящее из нескольких раундов. Бот " \
                        "автоматически определяет принадлежость двух противников к одному раунду и оповещает о сражении, которое произойдёт в рамках турнира. В " \
                        "результате такого сражения проигравший навсегда выбывает из турнира, а победитель " \
                        "двигается на один раунд вперёд."
begin_phrase="был вызван на дуэль! Бери ложку и защищайся!\n\n" \
                 "Правила дуэли: вы и соперник отправляете друг другу смайл `🥄` " \
                 "до тех пор, пока я не скажу, что кто-то из вас победил.\n\n" \
                 "❤️️ - Принять вызов!\n💔 - Аннулировать вызов!"
end_phrases=["__Противник убит прямым попаданием в голову!__",
             "__Соперник съеден ложкой. __",
             "__Голова соперника не выдерживает натиск металла и лопается! __",
             "__Вы разбили голову противника и теперь с наслаждением пробуете на вкус его мозги. __",
             "__Оказывается, глаза соперника идеально подходят для выковыривания ложкой! __",
             "__Вы закормили соперника досмерти мёдом. __",
             "__Ваш оппонент подавился ложкой. Насмерть. __",
             "__Вы использовали ложку для превращения соперника в отбивную! __",
             "__Ещё один кусает пыль! __",
             "__Ваш соперник испугался вашей огромной ложки и благоразумно решил капитулировать. __",
             "__Ваша ложка настолько велика и устрашающа, что соперник сам сдался. __",
             "__При виде вашей большой ложки противнику стало стыдно, и он убежал. __",
             "__Вы задушили соперника своей алюминиевой ложкой! __",
             "__Вы пытали противника несколько часов с помощью ложки, и он умер. __",
             "__Вы заставили соперника выкопать себе могилу своей же ложкой! __",
             "__Вы накормили противника с ложки супом из мухоморов! __",
             "__Ложка взорвалась и убила соперника насмерть. __",
             "__Соперник был зверски избит ложкой и убежал плакать. __",
             "__Ложка вырвалась у вас из рук и вцепилась своими зазубринами прямо в глотку противнику! __",
             "__Вы взглядом согнули ложку соперника... __",
             "__Ложка соперника оказалась зачарована на неудачу, поэтому он проиграл. __",
             "__Бог всех Ложек, Черпаков и Ложечек сошёл с небес и покарал соперника! __",
             "__Соперник испугался своего отражения в ложке и умер от страха! __",
             "__Ложка соперника оказалась мусульманкой и взорвалась. __",
             "__У соперника была слишком маленькая ложечка... __",
             "__Противник сказал, что ложки нет. Ну, по крайней мере, его собственной. __",
             "__Противник открыл коробочку, а там ложка ему по лицу даёт. __",
             "__Ложка противника внезапно оказалась сделанной из урана-238. __",
             "__Ложка соперника вызвала меметическое заражение и недееспособность соперника. __",
             "__Магнит в на борту пролетавшего мимо НЛО вырвал ложечку соперника из рук и воткнул её прямо в серце. __",
             "__У врага отняли ложку и обозвали угнетателем проходившие мимо форкистки. __",
             "__Ложка соперника оказалась шоколадной и растаяла прямо у него в руках. __",
             "__Противник не понял, чё надо делать с ложкой, и вы его победили! __",
             "__Ваша ложка сказала противнику то, чего он боялся услышать больше всего. Противник морально умер. __",
             "__Ложка противника оказалась бракованной, и он не смог вас одолеть. __",
             "__Противник оказался австралийским аборигеном и не умеет пользоваться ложками. __",
             "__Противник отказался защищаться ложкой из-за своего вероисповедания. __",
             "__Ваша ложка соблазнила ложку соперника, а потом коварно её умертвила!__"
             ]
preferences_message="С помощью этого сообщения __администраторы__ чата могут **настроить** меня, " \
                    "чтобы я работал так, как им угодно. Для этого внизу я оставил кнопки-" \
                    "переключатели, назначение которых сейчас поясню.\n\n" \
                    "**Удалять сразу** : должен ли бот удалять сразу же все сообщения, содержа" \
                    "щие ложку-эмоджи. Функция полезна для предотвращения флуда в чате.\n" \
                    "**Удалять после дуэли** : должен ли бот удалять сообщения с ложками-эмоджи," \
                    " отправленными во время дуэли.\n\n__❗Заметьте, что надпись на кнопке указывает" \
                    " на то, что именно будет приводиться в исполнение после нажатия на кнопку.\n\n❗️" \
                    "Заметьте, что данные функции будут приводиться в исполнение только после выдачи" \
                    " боту прав администратора.__"
annoyed_reply="Пожалуйста, внимательно прочитай инструкцию по использованию меня: /help@spoonduelbot." \
              " Я устал оттого, что люди вызывают кого-то на дуэль, не отвечая при этом **реплаем** " \
              "на сообщение оппонента. Как я могу понять, кого вы вызываете на дуэль?! Сколько раз нужно " \
              "напоминать о необходимости отвечать **реплаем?!**"
peers=[]
win_probability_percents=35
logging.basicConfig(level=logging.WARNING)
time_limit=60.0