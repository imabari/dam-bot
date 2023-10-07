import datetime
import os
import re

import pandas as pd
import requests
import tweepy

def date_parse(se, year):

    df = se.str.extract("(\d{2}/\d{2})? *(\d{2}:\d{2})").fillna(method="ffill")

    df_date = (
        df[0]
        .str.split("/", expand=True)
        .rename(columns={0: "month", 1: "day"})
        .astype(int)
    )

    df_date["year"] = year

    df_time = (
        df[1]
        .str.split(":", expand=True)
        .rename(columns={0: "hour", 1: "minute"})
        .astype(int)
    )

    return pd.to_datetime(df_date.join(df_time))

if __name__ == "__main__":

    JST = datetime.timezone(datetime.timedelta(hours=+9))

    dt_now = (datetime.datetime.now(JST) - datetime.timedelta(minutes=8)).replace(
        minute=0, second=0, microsecond=0, tzinfo=None
    )

    url = f"http://183.176.244.72/kawabou-mng/customizeMyMenuKeika.do?GID=05-5101&userId=U1001&myMenuId=U1001_MMENU003&PG=1&KTM=3"

    df = (
        pd.read_html(url, na_values=["-", "閉局"])[1]
        .rename(
            columns={
                0: "日時",
                1: "貯水位",
                2: "流入量",
                3: "放流量",
                4: "貯水量",
                5: "貯水率",
            }
        )
        .dropna(how="all", axis=1)
    )

    df["日時"] = date_parse(df["日時"], dt_now.year)

    # 貯水率が欠損の行を削除
    df.dropna(subset=["貯水率"], inplace=True)

    df.set_index("日時", inplace=True)

    if len(df) > 0:

        if dt_now in df.index:
            se = df.loc[dt_now]
        else:
            se = df.iloc[-1]

        rate = se["貯水率"]
        time = se.name.strftime("%H:%M")

        twit = f'ただいまの玉川ダムの貯水率は{rate}%です（{time}）\n#今治 #玉川ダム #貯水率'

        # Twitter
        bearer_token = os.environ["TAMAGAWA_BT"]
        consumer_key = os.environ["TAMAGAWA_CK"]
        consumer_secret = os.environ["TAMAGAWA_CS"]
        access_token = os.environ["TAMAGAWA_AT"]
        access_token_secret = os.environ["TAMAGAWA_AS"]

        client = tweepy.Client(bearer_token, consumer_key, consumer_secret, access_token, access_token_secret)

        print(twit)
        client.create_tweet(text=twit)
