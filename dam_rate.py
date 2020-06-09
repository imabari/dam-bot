import re
import os

import requests
import tweepy
from bs4 import BeautifulSoup

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; WOW64; Trident/7.0; rv:11.0) like Gecko"
}


def dam_rate(dam):

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

    url = f"http://i.river.go.jp/_-p01-_/p/ktm1801070/?mtm=10&swd=&prf=3801&twn=3801202&rvr=&den={dam['den']}"

    r = requests.get(url, headers=headers)
    r.raise_for_status()
    soup = BeautifulSoup(r.content, "html5lib")

    contents = soup.find("a", {"name": "contents"}).get_text("\n", strip=True)

    temp = re.sub(r"■\d{1,2}時間履歴\n単位：千m3\n", "", contents)

    lines = [i.split() for i in temp.splitlines()]

    result = []

    for line in lines:

        try:
            time, _rate = line
            rate = float(_rate)
        except:
            continue

        else:
            result.append({"time": time, "rate": rate})

    # 結果確認
    # print(result)

    n = len(result)

    if n:

        tw = result[0]

        # 最新3件確認

        if n > 2:

            for j in result[:3]:
                if j["time"] in ["06:00", "12:00", "18:00"]:
                    tw = j
                    break

        diff = tw["rate"] - before

        twit = f'ただいまの{dam["name"]}の貯水率は{tw["rate"]}%です（{tw["time"]}）\n前回比{diff:+.1f}ポイント\n#今治 #{dam["name"]} #貯水率'

        # print(twit)
        api.update_status(twit)


if __name__ == "__main__":

    dams = [
        {
            "name": "玉川ダム",
            "id": "BotTamagawaDam",
            "den": "0972900700006",
            "CK": os.environ["TAMAGAWA_CK"],
            "CS": os.environ["TAMAGAWA_CS"],
            "AT": os.environ["TAMAGAWA_AT"],
            "AS": os.environ["TAMAGAWA_AS"],
        },
        {
            "name": "台ダム",
            "id": "BotUtenaDam",
            "den": "0972900700007",
            "CK": os.environ["UTENA_CK"],
            "CS": os.environ["UTENA_CS"],
            "AT": os.environ["UTENA_AT"],
            "AS": os.environ["UTENA_AS"],
        },
    ]

    for dam in dams:
        dam_rate(dam)
