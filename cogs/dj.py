import discord
from discord.ext import commands

import asyncio
import os

from util import util
from util import reddit


class DJ(commands.Cog):

    def __init__(self, client) -> None:
        self.client = client

    @commands.command(name='djenzyme', aliases=['dj', 'enzyme'])
    @commands.cooldown(1, 10, commands.BucketType.guild)
    async def djenzyme(self, ctx):
        voice_channel = None
        for channel in ctx.guild.voice_channels:
            if 'dj' in channel.name and 'enzyme' in channel.name:
                voice_channel = channel
                break
        if voice_channel is None:
            await ctx.send('No valid dj enzyme channels found!')
            return
        await voice_channel.connect()

        voice = discord.utils.get(
            self.client.voice_clients, guild=ctx.guild)
        if not voice.is_connected():
            await voice_channel.connect()
        voice.play(discord.FFmpegPCMAudio('./assets/test.mp3'))
        # await voice.disconnect()
