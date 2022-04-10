import discord
from discord.ext import commands
from discord.ext import tasks

import asyncio
import os

from util import util
from util import reddit
from util import misc


class Memes(commands.Cog):

    def __init__(self, client) -> None:
        self.client = client
        self.read_memes.start()

    @tasks.loop(seconds=69)
    async def read_memes(self):
        await asyncio.wait_for(reddit.get_submissions('pallone', 13), timeout=21)

    @commands.command(name='meme')
    @commands.cooldown(1, 3, commands.BucketType.user)
    async def sendmeme(self, ctx):
        '''Sends a spicy meme taken from r/Pallone'''
        await util.send_random_meme(ctx, 'pallone')

    @ commands.command(name='getmeme', aliases=['gm'])
    @ commands.cooldown(1, 10, commands.BucketType.user)
    async def getmeme(self, ctx, subreddit):
        '''
        Retrieves a meme from a subreddit of your choice
        Usage:
                For example: `pallone getmeme memes` to get memes from r/memes
                                        `pallone getmeme dankmemes` to get memes from r/dankmemes
        You can also use the shorthand `pallone gm <subreddit>`
        '''
        await ctx.send(embed=misc.info_embed(f'Reading memes from r/{subreddit}...', '(This may take a while)'))
        try:
            await asyncio.wait_for(reddit.get_submissions(subreddit, 69), timeout=9)
        except Exception:
            await ctx.send(embed=misc.error_embed('Reading memes failed.', 'I didn\'t find any memes...'))
            return
        if len(os.listdir(f'submissions/{subreddit}')) == 0:
            await ctx.send(embed=misc.error_embed('Reading memes failed.', 'I didn\'t find any memes...'))
            return
        await util.send_random_meme(ctx, subreddit)
