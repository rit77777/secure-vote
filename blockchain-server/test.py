from sre_constants import SUCCESS
import requests

TRANSACTIONS = [
    {
        "candidate": "1119p9p9,p111111",
        "voterhash": "111b6u6bu6bu1111111"
    },
    {
        "candidate": "11bu6bu6bu11111",
        "voterhash": "111b6ub6bu111111"
    },
    {
        "candidate": "11111b6ub6u1111",
        "voterhash": "1b6u6u6bu11111111"
    },
    {
        "candidate": "14ct42ct2c4t11111111",
        "voterhash": "11vyubvbut24t111"
    },
    {
        "candidate": "bu64bu6bu111111",
        "voterhash": "11111bu46bu64b111111111"
    },
    {
        "candidate": "111111ub46bu6b1111111111",
        "voterhash": "11111ub6ub6411111111111"
    },
    {
        "candidate": "111b6ub64u1111111111111",
        "voterhash": "11111b64ub64u11111111111"
    },
    {
        "candidate": "11b6u6bu64b111111",
        "voterhash": "11111u1ub6bu6b11"
    },
    {
        "candidate": "11b6u6bu11111111111111",
        "voterhash": "111111111b6u4bub46u1111111"
    },
    {
        "candidate": "11111111111b6ubu6b4u11111",
        "voterhash": "111b6u4bu64b46b1111111111111"
    },
    {
        "candidate": "111111111bu64bub6u61111111",
        "voterhash": "11bu6bu64bu6bu11111111111111"
    },
    {
        "candidate": "1111111111111111bu6b6bu",
        "voterhash": "1111111111bu6bu6bu111111"
    },
    {
        "candidate": "111111111111bu46bu6bu1111",
        "voterhash": "11111bu64bu6bu11111111111"
    },
    {
        "candidate": "111111bu6b64b6b1111111111",
        "voterhash": "1111111b6ubu6b6b111111111"
    },
    {
        "candidate": "1111111b6ub6ub64bu111111111",
        "voterhash": "1111bu6bu6bu6b111111111111"
    },
    {
        "candidate": "1111b6ub6u6b111111111111",
        "voterhash": "1111b6ub64u4b6111111111111"
    },
    {
        "candidate": "111111b6u6bu61111111111",
        "voterhash": "1111b6ub6ub6b111111111111"
    },
    {
        "candidate": "1111b6ubub64bu111111111111",
        "voterhash": "1111b6ub6bu6b111111111111"
    },
    {
        "candidate": "1111111b6ub64u64u111111111",
        "voterhash": "1b6u6b4ub6b6111111111111111"
    },
    {
        "candidate": "1111111bu64bub6111111111",
        "voterhash": "1111111114b6u64bb61111111"
    },
    {
        "candidate": "1111111b6u4b6b64111111111",
        "voterhash": "111b6u4b6ub1111111111111"
    },
    {
        "candidate": "111111135vyv5vy111111111",
        "voterhash": "1111111vy35vy53111111111"
    },
    {
        "candidate": "111111v5y5vy1111111111",
        "voterhash": "1111111v5yv5yv111111111"
    },
    {
        "candidate": "111111vy5vy51111111111",
        "voterhash": "11115vy3v1111v5yv5y53y11111111"
    },
    {
        "candidate": "111mo8m8mo1111111",
        "voterhash": "1111m8om86o1111"
    },
    {
        "candidate": "11111mo8mo86mo1111",
        "voterhash": "111mo86o8mo11111"
    },
    {
        "candidate": "111111om86mo86mo1111",
        "voterhash": "1111om86mo86mo111"
    },
    {
        "candidate": "111o1om68mo8mo1",
        "voterhash": "11186mo86mo86m1111111"
    },
    {
        "candidate": "11mo86o68mom8111111",
        "voterhash": "1111om86mo68mo1111"
    },
    {
        "candidate": "111111om86om68o111",
        "voterhash": "1111o86mo6m8o111111"
    },
    {
        "candidate": "111o8mo68mo86m1111",
        "voterhash": "1om8mo8mo1111111"
    },
    {
        "candidate": "1118om86mo1111111",
        "voterhash": "11111m8o8mo1111111"
    },
    {
        "candidate": "jn75n11",
        "voterhash": "118mo8mo11111111"
    },
    {
        "candidate": "111111v6v461111111111",
        "voterhash": "111111v61111111111"
    },
    {
        "candidate": "111111ubv264v661111111111",
        "voterhash": "111111ub6u6111111"
    },
    {
        "candidate": "bu6bu6bu1111111",
        "voterhash": "b6u6bu1111"
    }
]

def create_new_transactions():
    for i in range(len(TRANSACTIONS)):
        response = requests.post("http://127.0.0.1:5000/new_transaction/", json=TRANSACTIONS[i], headers={'Content-type': 'application/json'})
        print(f"Success: #{i}")
        requests.get("http://127.0.0.1:5000/mine_block/")


create_new_transactions()