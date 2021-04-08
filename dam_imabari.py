import datetime
import os
import re

import pandas as pd
import requests
import tweepy

dams = [
    {
        "name": "玉川ダム",
        "id": "BotTamagawaDam",
        "json": "0972900700006.json",
        "CK": os.environ["TAMAGAWA_CK"],
        "CS": os.environ["TAMAGAWA_CS"],
        "AT": os.environ["TAMAGAWA_AT"],
        "AS": os.environ["TAMAGAWA_AS"],
    },
    {
        "name": "台ダム",
        "id": "BotUtenaDam",
        "json": "0972900700007.json",
        "CK": os.environ["UTENA_CK"],
        "CS": os.environ["UTENA_CS"],
        "AT": os.environ["UTENA_AT"],
        "AS": os.environ["UTENA_AS"],
    },
]


def dam_rate(dam, dt_now):

    # Twitterオブジェクトの生成
    auth = tweepy.OAuthHandler(dam["CK"], dam["CS"])
    auth.set_access_token(dam["AT"], dam["AS"])

    api = tweepy.API(auth)

    text = api.user_timeline(dam["id"])[0].text

    m = re.search(r"(\d+\.?\d*)%", text)

    if m:
        try:
            before = float(m.group(1))
        except:
            before = 0
    else:
        before = 0

    s_ymd = dt_now.strftime("%Y%m%d")
    s_hm = dt_now.strftime("%H%M")

    url = f'https://www.river.go.jp/kawabou/file/files/tmlist/dam/{s_ymd}/{s_hm}/{dam["json"]}'

    r = requests.get(url)
    r.raise_for_status()

    data = r.json()

    df = pd.json_normalize(data["min10Values"])

    df["DateTime"] = pd.to_datetime(df["obsTime"])

    # 貯水率が欠損の行を削除
    df.dropna(subset=["storPcntIrr"], inplace=True)

    se = df.iloc[0]

    tw = {}

    tw["rate"] = se["storPcntIrr"]
    tw["time"] = se["DateTime"].strftime("%H:%M")

    diff = tw["rate"] - before

    twit = f'ただいまの{dam["name"]}の貯水率は{tw["rate"]}%です（{tw["time"]}）\n前回比{diff:+.1f}ポイント\n#今治 #{dam["name"]} #貯水率 #てや'

    # print(twit)

    api.update_status(twit)


if __name__ == "__main__":

    JST = datetime.timezone(datetime.timedelta(hours=+9))
    dt_now = datetime.datetime.now(JST) - datetime.timedelta(minutes=8)

    dt_tmp = dt_now.replace(minute=5, second=0, microsecond=0, tzinfo=None)

    for dam in dams:
        dam_rate(dam, dt_tmp)
