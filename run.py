import sys
import traceback
import json
import os
import re

import pandas as pd
from dateutil.parser import parse

import quandoo
from quandoo.QuandooModel import QuandooDatetime

from dotenv import load_dotenv


SKIP_ALL = False


def main():
    quandoo_bookings = get_quandoo_bookings()
    archtics_bookings = get_archtics_bookings()
    quandoo_merchants = get_quandoo_merchants()

    update_res_tags(quandoo_merchants)
    cancelled_orders(quandoo_bookings, archtics_bookings, quandoo_merchants)
    new_bookings(quandoo_bookings, archtics_bookings, quandoo_merchants)

    print()


def get_quandoo_bookings():
    quandoo_bookings = pd.read_json('quandoo_bookings.json', dtype=str)
    quandoo_bookings.fillna('', inplace=True)
    quandoo_bookings = quandoo_bookings.loc[quandoo_bookings['status'] == "ACTIVE"]
    quandoo_bookings['index'] = quandoo_bookings['order_num'].astype(str) + quandoo_bookings['event_name']
    quandoo_bookings.set_index('index', drop=True, inplace=True)
    return quandoo_bookings


def get_archtics_bookings():
    archtics_bookings = pd.read_csv('quandoo.csv', dtype=str)
    archtics_bookings.fillna('', inplace=True)
    archtics_bookings['index'] = archtics_bookings['order_num'].astype(str) + archtics_bookings['event_name']
    archtics_bookings.set_index('index', drop=True, inplace=True)
    return archtics_bookings


def get_quandoo_merchants():
    quandoo_merchants = pd.read_json("quandoo_merchants.json", dtype=str)
    quandoo_merchants.fillna('', inplace=True)
    return quandoo_merchants


def new_bookings(quandoo_bookings, archtics_bookings, quandoo_merchants):
    print("START:    Adding bookings that are in Archtics but not in Quandoo")
    cur_event, cur_rest = None, None
    for index, booking in archtics_bookings.iterrows():
        if cur_rest != booking['event_name'][:4]:
            cur_rest = booking['event_name'][:4]

        if booking['event_name'] != cur_event:
            cur_event = booking['event_name']
            print('\n' + '-' * 20 + booking['event_name'] + '-' * 20 + '\n')

        dt = parse(f'{booking["event_date"]} {booking["event_time"]}', dayfirst=True)
        qdt = QuandooDatetime(dt)

        if QuandooDatetime.now().datetime > qdt.datetime:
            continue

        if index in quandoo_bookings.index:
            continue

        make_booking(booking, quandoo_bookings, quandoo_merchants)
    print("FINISHED: Adding bookings that are in Archtics but not in Quandoo")


def cancelled_orders(quandoo_bookings, archtics_bookings, quandoo_merchants):
    print("START:    Removing bookings that are in Quandoo but not in Archtics")
    cur_event, cur_rest = None, None
    for index, booking in quandoo_bookings.iterrows():
        if cur_rest != booking['event_name'][:4]:
            cur_rest = booking['event_name'][:4]

        if booking['event_name'] != cur_event:
            cur_event = booking['event_name']
            print('\n' + '-' * 20 + booking['event_name'] + '-' * 20 + '\n')

        dt = parse(f'{booking["event_date"]} {booking["event_time"]}', dayfirst=True)
        qdt = QuandooDatetime(dt)

        if QuandooDatetime.now().datetime > qdt.datetime:
            continue

        if index in archtics_bookings.index:
            continue

        cancel_booking(booking, quandoo_bookings)
    print("FINISHED: Removing bookings that are in Quandoo but not in Archtics")


def make_booking(booking: pd.Series, quandoo_bookings: pd.DataFrame, quandoo_merchants: pd.DataFrame):
    agent = quandoo.Agent(AUTH_TOKEN, AGENT_ID)

    quandoo_merchant = quandoo_merchants.loc[quandoo_merchants['archtics_code'] == booking['event_name'][:4]]
    merchant_id = quandoo_merchant['merchant_id'].values[0]
    merchant = quandoo.Merchant(
        data={
            "id": merchant_id,
            "name": "",
            "location": {"address": {}}
        },
        agent=agent
    )

    dt = parse(f'{booking["event_date"]} {booking["event_time"]}', dayfirst=True)
    qdt = QuandooDatetime(dt)

    customer_email = "{}{}{}".format(booking['order_num'], booking['full_name'],
                                     booking['company_name'] if booking['company_name'] else booking['full_name'])
    customer_email = customer_email.replace(' ', '_')
    customer_email = re.sub(r'[^0-9a-zA-Z_]+', '', customer_email)
    customer = quandoo.Customer(
        {
            "id": "",
            "firstName": booking['full_name'],
            "lastName": booking['company_name'] if booking['company_name'] else booking['full_name'],
            "email": customer_email + '@tmorder.com',
            "phoneNumber": "466920029"
        },
        agent=agent
    )

    extra_info = {
        "archtics": {
            "order_num": booking['order_num'],
            "acct_id": booking['acct_id'],
            "event_name": booking['event_name'],
        }
    }

    tag = get_tag(booking['event_name'], quandoo_merchants)

    while True:

        try:
            new_res = merchant.create_reservation(
                customer, booking['pax'], qdt,
                extra_info=json.dumps(extra_info),
                reservation_tags=[tag]
            )
            booking['reservation_public_id'], booking['reservation_id'] = new_res.id, new_res.number
            booking['status'] = 'ACTIVE'
            quandoo_bookings.loc[f'{booking["order_num"]}{booking["event_name"]}'] = booking
            print("SUCCESS Booking ({}) made for ({}, {})".format(new_res.id, booking['order_num'], booking['acct_id']))
            quandoo_bookings.to_json('quandoo_bookings.json', orient='records')
            return

        except (quandoo.PoorResponse, OSError) as e:
            global SKIP_ALL
            if SKIP_ALL:
                return
            print("\nFAILURE: {}".format(e))
            print(f"\t{booking['company_name'] if booking['company_name'] else ''} {booking['full_name']}")
            print(f"\t{booking['pax']} people at {quandoo_merchant['merchant_name'].values[0]} on {qdt.pretty_date()}")
            print("Rearrange tables or add table combos to accommodate the booking")
            i = input("[ENTER] to try again, [skip] to skip, [skipall] to auto skip any remaining\n")
            if i.upper() == 'SKIP':
                return
            elif i.upper() == 'SKIPALL':
                SKIP_ALL = True
                return


def cancel_booking(booking: pd.Series, quandoo_bookings: pd.DataFrame):
    agent = quandoo.Agent(AUTH_TOKEN, AGENT_ID)
    quandoo.Reservation(booking['reservation_public_id'], agent).cancel()
    booking['status'] = 'CANCELLED'
    print(f"SUCCESS Booking ({booking['reservation_public_id']}) cancelled")
    quandoo_bookings.to_json('quandoo_bookings.json', orient='records')


def get_tag(event_name, quandoo_merchants):
    QUANDOO_TAGS = json.load(open('quandoo_tags.json'))

    quandoo_merchant = quandoo_merchants.loc[quandoo_merchants['archtics_code'] == event_name[:4]]
    merchant_id = quandoo_merchant['merchant_id'].values[0]
    merchant_tags = QUANDOO_TAGS[str(merchant_id)]['reservationTags']

    for tag in merchant_tags:
        if tag['name'].lower() == quandoo_merchant['reservation_tag'].values[0].lower():
            return tag['id']

    raise Exception(f'{event_name} has no reservation tag')


def update_res_tags(quandoo_merchants):
    print("START:    Getting most up to date reservation tags from Quandoo... This should take a few seconds per merchant")
    d = {}
    for i, quandoo_merchant in quandoo_merchants.iterrows():
        merchant = quandoo.Merchant(
            data={
                "id": quandoo_merchant['merchant_id'],
                "name": "",
                "location": {"address": {}}
            },
            agent=quandoo.Agent(AUTH_TOKEN, AGENT_ID)
        )
        tags = json.loads(merchant.get_reservation_tags())
        d[quandoo_merchant['merchant_id']] = tags
    with open('quandoo_tags.json', 'w') as f:
        json.dump(d, f)
    print("FINISHED: Getting most up to date reservation tags from Quandoo")


def get_full_class_name(obj):
    module = obj.__class__.__module__
    if module is None or module == str.__class__.__module__:
        return obj.__class__.__name__
    return module + '.' + obj.__class__.__name__


if __name__ == '__main__':
    try:
        load_dotenv()
        AUTH_TOKEN = os.environ.get('AUTH_TOKEN')
        AGENT_ID = os.environ.get('AGENT_ID')
        if not all([AUTH_TOKEN, AGENT_ID]):
            raise Exception(f'ERROR: "AUTH_TOKEN" and/or "AGENT_ID" not in .env file, ensure these are added')
        main()
        input("ALL FINISHED, you may quit")

    except quandoo.Error.QuandooException as e:
        traceback.print_exc(file=sys.stdout)
        print(f'QUANDOO_ERROR: {get_full_class_name(e)} {e}', file=sys.stderr)
        input()
        # raise e

    except Exception as e:
        traceback.print_exc(file=sys.stdout)
        print(f'PROGRAM ERROR: {get_full_class_name(e)} {e}', file=sys.stderr)
        input()
        # raise e
