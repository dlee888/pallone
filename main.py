import discord
from discord.ext import commands
from discord.ext import tasks

import random
import os
import asyncio
import traceback
import io
import textwrap
from contextlib import redirect_stdout

import reddit
import util
import misc

bot = commands.Bot(command_prefix=commands.when_mentioned_or('pallone '))


@bot.event
async def on_ready():
    print('Reading memes...')
    await reddit.get_submissions('pallone', 20, True)

    game = discord.Game('"pallone help"')
    await bot.change_presence(status=discord.Status.dnd, activity=game)
    read_memes.start()
    print('Bot is ready')


@bot.command()
async def ping(ctx):
    '''Is the bot online?'''
    await ctx.send(f'Pong! Latency = {round(bot.latency * 1000, 3)} ms')


@bot.command(name='meme')
@commands.cooldown(1, 3, commands.BucketType.user)
async def sendmeme(ctx):
    '''Sends a spicy meme taken from r/Pallone'''
    meme = random.choice(os.listdir('submissions/pallone'))
    meme_id = meme[:-4]
    meme_ext = meme[-4:]
    title, link, score, comments = await reddit.get_info(meme_id)

    im = discord.File(
        f'submissions/pallone/{meme}', filename=f'meme{meme_ext}')
    embed = discord.Embed()
    embed.title = title
    embed.url = f'https://www.reddit.com{link}'
    embed.set_image(url=f'attachment://meme{meme_ext}')
    embed.set_footer(text=f'{score} upvotes, {comments} comments')
    await ctx.send(file=im, embed=embed)


@tasks.loop(seconds=69)
async def read_memes(trace=False):
    await reddit.get_submissions('pallone', 13, trace)


@bot.event
async def on_command_error(ctx, exc):
    if type(exc) == commands.errors.BotMissingPermissions:
        await ctx.send(f'The bot is missing permissions.\nThe missing permissions are: {" ".join(exc.missing_perms)}')
    elif type(exc) == commands.errors.MissingRequiredArgument:
        await ctx.send(f'Missing required argument.\nPlease enter a value for: {exc.param}')
    elif issubclass(type(exc), commands.errors.UserInputError):
        await ctx.send(f'There was an error parsing your argument')
    elif type(exc) == commands.errors.TooManyArguments:
        await ctx.send(f'Bruh what why are there so many arguments?')
    elif type(exc) == commands.errors.CommandOnCooldown:
        await misc.send_cooldown_embed(ctx, exc.retry_after)
    elif type(exc) == commands.errors.CommandNotFound:
        # await ctx.send('Command not found.')
        pass
    elif type(exc) == commands.errors.MissingPermissions:
        await ctx.send(f'You are missing permissions.\nThe missing permissions are: {" ".join(exc.missing_perms)}')
    else:
        print('Command error found')

        etype = type(exc)
        trace = exc.__traceback__

        lines = traceback.format_exception(etype, exc, trace)
        traceback_text = ''.join(lines)

        msg = ('Command Error:\n'
               f'Author: {ctx.author} ({ctx.author.id})\n'
               f'Guild: {ctx.guild} ({ctx.guild.id})\n'
               f'```\n{traceback_text}\n```')
        print(msg)
        error_channel = bot.get_channel(849471377144021023)
        try:
            await error_channel.send(msg)
        except:
            with open('data/message.txt', 'w') as file:
                file.write(msg)
            await error_channel.send(f'Command Error:\n', discord.File('data/message.txt'))


def cleanup_code(content):
    """Automatically removes code blocks from the code."""
    if content.startswith('```') and content.endswith('```'):
        return '\n'.join(content.split('\n')[1:-1])
    return content.strip('` \n')


@bot.command(pass_context=True, hidden=True)
async def debug(ctx, *, body: str):
    """Evaluates a code"""

    if ctx.author.id != 716070916550819860:
        return

    env = {
        'bot': bot,
        'ctx': ctx,
        'channel': ctx.channel,
        'author': ctx.author,
        'guild': ctx.guild,
        'message': ctx.message,
    }

    env.update(globals())

    body = cleanup_code(body)
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

if __name__ == "__main__":
    bot.run(util.get_var('PALLONE_TOKEN'))
