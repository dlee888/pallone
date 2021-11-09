import discord
from discord.ext import commands

from typing import Union

from util import stonks
from util.data import data
from util import misc


class Stonks(commands.Cog):

    def __init__(self, client):
        self.client = client

    @commands.group(brief='Stonks', invoke_without_command=True)
    async def stonks(self, ctx):
        """Virtual stonks trading."""
        await ctx.send_help('stonks')

    @stonks.command()
    @commands.cooldown(1, 3, commands.BucketType.user)
    async def price(self, ctx, company):
        """Gets the current price of a stock"""
        company = company.upper()
        embed = stonks.make_company_embed(company)
        if embed is None:
            await ctx.send(f'Company `{company.upper()}` not found.')
            return
        price = stonks.get_price(company)
        embed.description = f'Price: ${price}'
        filename = f'plot_{ctx.message.id}.png'
        stonks.plot_historical_price(filename, company)
        embed.set_image(f'attachment://{filename}')
        await ctx.send(file=discord.File(filename), embed=embed)

    @stonks.command(aliases=['bal'])
    async def balance(self, ctx, person: Union[discord.Member, discord.User] = None):
        """Shows how much money and which stocks you have"""
        if person is None:
            person = ctx.author
        bal = data.get_money(person.id)
        if bal is None:
            if person == ctx.author:
                data.change_money(person.id, 0)
                await ctx.send(embed=misc.stonks_intro_embed())
            else:
                await ctx.send(embed=misc.info_embed('Person not found', f'{person} has not yet traded any stonks.'))
            return
        stonks_owned = data.get_stonks(person.id)
        net = bal
        embed = misc.info_embed(f'{person}\'s balance')
        embed.add_field(name='Money', value=f'`{round(bal, 8)}`')
        description = ''
        for stonk in stonks_owned.items():
            description += f'`{stonk[0]}`: `{round(stonk[1], 8)}` shares\n'
            net += stonk[1] * stonks.get_price(stonk[0])
        if len(stonks_owned) == 0:
            description = 'No stonks owned.\n'
        embed.add_field(name='Stonks', value=description)
        embed.add_field(name='Net worth', value=f'`{net}`')
        await ctx.send(embed=embed)

    @stonks.command()
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def buy(self, ctx, company, amount: float):
        """
        Buys some stonks. 
        Note: you can buy negative values to sell, your total balance can be negative (you owe money), and you can own a negative amount of stock (sort of like short selling).
        """
        if data.get_money(ctx.author.id) is None:
            data.change_money(ctx.author.id, 0)
            await ctx.send(embed=misc.stonks_intro_embed())
            return
        company = company.upper()
        price = stonks.get_price(company)
        if price is None:
            await ctx.send(embed=misc.error_embed('Company not found', f'Company `{company}` was not found.'))
            return
        data.change_money(ctx.author.id, -price * amount)
        data.change_stonks(ctx.author.id, company, amount)
        await ctx.send(embed=misc.info_embed('Purchase success', f'{amount} shares of {company} bought for `${price}` per share.'))
