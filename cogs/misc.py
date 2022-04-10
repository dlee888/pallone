import discord
from discord.ext import commands


import asyncio
import os
import io
import textwrap
from contextlib import redirect_stdout
import traceback

from util import util
from util import reddit


class Misc(commands.Cog):

    def __init__(self, client) -> None:
        self.client = client

    @commands.Cog.listener()
    async def on_ready(self):
        print('Reading memes...')
        asyncio.create_task(reddit.get_submissions('pallone', 50, trace=True, fresh=False))

        game = discord.Game('"pallone help"')
        await self.client.change_presence(status=discord.Status.dnd, activity=game)
        print('Bot is ready')


    @commands.command()
    async def ping(self, ctx):
        '''Is the bot online?'''
        await ctx.send(f'Pong! Latency = {round(self.client.latency * 1000, 3)} ms')
        
    def cleanup_code(self, content):
        """Automatically removes code blocks from the code."""
        if content.startswith('```') and content.endswith('```'):
            return '\n'.join(content.split('\n')[1:-1])
        return content.strip('` \n')


    @commands.command(pass_context=True, hidden=True)
    async def debug(self, ctx, *, body: str):
        """Evaluates a code"""
        if ctx.author.id != 716070916550819860:
            return
        
        env = {
            'bot': self.client,
            'ctx': ctx,
            'channel': ctx.channel,
            'author': ctx.author,
            'guild': ctx.guild,
            'message': ctx.message,
        }

        env.update(globals())

        body = self.cleanup_code(body)
        stdout = io.StringIO()

        to_compile = f'async def func():\n{textwrap.indent(body, "  ")}'

        try:
            exec(to_compile, env)
        except Exception as e:
            return await ctx.send(f'```py\n{e.__class__.__name__}: {e}\n```')

        func = env['func']
        try:
            with redirect_stdout(stdout):
                ret = await func()
        except Exception as e:
            value = stdout.getvalue()
            await ctx.send(f'```py\n{value}{traceback.format_exc()}\n```')
        else:
            value = stdout.getvalue()
            try:
                await ctx.message.add_reaction('\u2705')
            except:
                pass

            if ret is None:
                if value:
                    await ctx.send(f'```py\n{value}\n```')
            else:
                await ctx.send(f'```py\n{value}{ret}\n```')

    @commands.command(hidden=True)
    async def kill(self, ctx):
        if ctx.author.id == 716070916550819860:
            await ctx.send('Dying...')
            os._exit(69)

    @commands.command(hidden=True)
    async def restart(self, ctx):
        if ctx.author.id == 716070916550819860:
            await ctx.send('Restarting...')
            os._exit(0)