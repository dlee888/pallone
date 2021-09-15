import discord
from discord.ext import commands
from discord.ext.commands.core import command

from util import stonks

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
        embed = stonks.make_company_embed(company)
        if embed is None:
            await ctx.send(f'Company `{company.upper()}` not found.')
            return
        price = stonks.get_price(company)
        embed.description = f'Price: ${price}'
        await ctx.send(embed=embed)