import os

import pandas as pd
from atproto import Client

url = "http://183.176.244.72/kawabou-mng/customizeMyMenuKeika.do?GID=05-5101&userId=U1001&myMenuId=U1001_MMENU003&PG=1&KTM=2"

# 現在
dt_now = pd.Timestamp.now(tz="Asia/Tokyo").tz_localize(None)
dt_now

df = (
    pd.read_html(url, na_values=["-", "閉局", "欠測"])[1]
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

df_date = df["日時"].str.extract("(\d{2}/\d{2})? *(\d{2}:\d{2})").fillna(method="ffill")

df_date["year"] = dt_now.year

df_date[["month", "day"]] = (
    df_date[0].str.strip().str.split("/", expand=True).astype(int)
)

df_date[["hour", "minute"]] = (
    df_date[1].str.strip().str.split(":", expand=True).astype(int)
)

df_date["datetime"] = pd.to_datetime(
    df_date[["year", "month", "day", "hour", "minute"]]
)

df_date["year"].mask(dt_now < df_date["datetime"], df_date["year"] - 1, inplace=True)

df["日時"] = pd.to_datetime(df_date[["year", "month", "day", "hour", "minute"]])

# 貯水率が欠損の行を削除
df.dropna(subset=["貯水率"], inplace=True)

df.set_index("日時", inplace=True)

df

at_user = os.environ["AT_USER"]
at_pass = os.environ["AT_PASS"]

client = Client()
client.login(at_user, at_pass)

if len(df) > 0:

    se = df.iloc[-1]
    d = {}
    d["rate"] = se["貯水率"]
    d["time"] = se.name.strftime("%H:%M")

    text = f'ただいまの玉川ダムの貯水率は{d["rate"]}%です（{d["time"]}）'

    client.send_post(text)

    print(text)
