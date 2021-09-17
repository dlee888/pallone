import discord
import requests
import os
import json

API_KEY = os.getenv('STONKS_KEY')

BASE_URL = 'https://financialmodelingprep.com/api/v3/'
QUOTE_URL = BASE_URL + 'quote/'
PROFILE_URL = BASE_URL + 'profile/'

def get_response(url : str):
    r = requests.get(url)
    json_data = json.loads(r.text)
    return json_data

def get_quote(company : str):
    json_data = get_response(f'{QUOTE_URL}{company.upper()}?apikey={API_KEY}')
    if len(json_data) == 0:
        return None
    assert(len(json_data) == 1)
    return json_data[0]

def get_profile(company : str):
    json_data = get_response(f'{PROFILE_URL}{company.upper()}?apikey={API_KEY}')
    if len(json_data) == 0:
        return None
    assert(len(json_data) == 1)
    return json_data[0]

def get_price(company : str):
    return get_quote(company)['price']

def make_company_embed(company: str):
    res = discord.Embed(title=company, color=0xdd0000)
    profile = get_profile(company)
    if profile is None:
        return None
    res.set_thumbnail(url=profile['image'])
    return res