#!/usr/bin/env python3
import base64
import os
from urllib.parse import parse_qs

from Crypto.Cipher import AES
from flask import Flask, render_template, request

FLAG = open('flag.txt', 'r').read().strip()
KEY = os.urandom(16)
NONCE = os.urandom(8)

ITEMS = {
    'destroyer_set': {
        'name': 'Cassin',
        'price': 120,
        'rarity': 'R',
        'tagline': 'Eagle Union destroyer. Simple, dependable, and useful for any early fleet.',
        'image': 'https://azurlane.netojuu.com/images/c/c9/Cassin.png',
        'available': True,
    },
    'royal_cruiser': {
        'name': 'Belfast',
        'price': 850,
        'rarity': 'SR',
        'tagline': 'Royal Navy light cruiser with polished support utility and enduring popularity.',
        'image': 'https://azurlane.netojuu.com/images/8/86/Belfast.png',
        'available': True,
    },
    'enterprise_gold': {
        'name': 'Enterprise',
        'price': 4800,
        'rarity': 'SSR',
        'tagline': 'Iconic Eagle Union carrier with one of the most recognizable kits in the game.',
        'image': 'https://azurlane.netojuu.com/images/4/40/Enterprise.png',
        'available': True,
    },
    'celestial_waifu': {
        'name': 'Shinano',
        'price': 999999,
        'rarity': 'UR',
        'tagline': 'Sakura Empire carrier with top-tier power and a premium collector release.',
        'image': 'https://azurlane.netojuu.com/images/a/a9/Shinano.png',
        'available': False,
    },
}

HERO_IMAGE = 'https://azurlane.netojuu.com/images/a/a9/Shinano.png'
HERO_TITLE = 'Azur Lane Preorder Desk'
HERO_COPY = 'Browse featured shipgirl releases, check out as a guest, and bring your sealed order confirmation to the preorder desk. Shinano remains locked behind the premium lottery queue.'
HERO_BADGE = 'Guest checkout · Standard shipping · Encrypted orders'
HERO_FEATURE = 'Featured drop · Shinano'

app = Flask(__name__)


def crypt(data):
    cipher = AES.new(KEY, AES.MODE_CTR, nonce=NONCE)
    return cipher.encrypt(data)


def encode_order(fields):
    body = '&'.join(f'{k}={v}' for k, v in fields.items()).encode()
    return base64.urlsafe_b64encode(crypt(body)).decode().rstrip('=')


def decode_order(token):
    raw = base64.urlsafe_b64decode(token + '=' * (-len(token) % 4))
    body = crypt(raw)
    return {k: v[-1] for k, v in parse_qs(body.decode(), keep_blank_values=True).items()}


@app.get('/')
def index():
    return render_template(
        'index.html',
        items=ITEMS,
        hero_image=HERO_IMAGE,
        hero_title=HERO_TITLE,
        hero_copy=HERO_COPY,
        hero_badge=HERO_BADGE,
        hero_feature=HERO_FEATURE,
    )


@app.get('/checkout')
def checkout():
    item_id = request.args.get('item', '')
    item = ITEMS.get(item_id)
    if item is None:
        return render_template('result.html', ok=False, title='Item not found', message='That product is not in the catalog.'), 404
    if not item['available']:
        return render_template('result.html', ok=False, title='Preorder closed', message='This item is currently reserved for verified lottery winners.'), 403
    return render_template('checkout.html', item_id=item_id, item=item)


@app.post('/order')
def order():
    item_id = request.form.get('item', '')
    item = ITEMS.get(item_id)
    if item is None or not item['available']:
        return render_template('result.html', ok=False, title='Order failed', message='The cashier could not create this order.'), 400

    token = encode_order({
        'item': item_id,
        'price': str(item['price']).zfill(6),
        'buyer': 'guest',
        'ship': 'standard',
    })
    return render_template('order.html', item=item, token=token)


@app.post('/claim')
def claim():
    token = request.form.get('order_token', '')
    try:
        order_data = decode_order(token)
    except Exception:
        return render_template('result.html', ok=False, title='Order review', message='The fulfillment desk could not verify this order.'), 400

    if order_data.get('item') == 'celestial_waifu' and order_data.get('price') == '000000':
        return render_template('result.html', ok=True, title='Preorder secured', message=FLAG)

    name = ITEMS.get(order_data.get('item', ''), {}).get('name', 'unknown item')
    return render_template('result.html', ok=False, title='Order reviewed', message=f'Your order for {name} is valid, but it is not eligible for the limited preorder bonus.')


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
