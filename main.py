import discord
from discord.ext import commands
from discord.ext import tasks

import random
import os
import asyncio
import traceback

import reddit

bot = commands.Bot(command_prefix=commands.when_mentioned_or('pallone '))


@bot.event
async def on_ready():
    asyncio.create_task(reddit.get_submissions('pallone', 100))
    
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
    
    im = discord.File(f'submissions/pallone/{meme}', filename=f'meme{meme_ext}')
    embed = discord.Embed()
    embed.title = title
    embed.url = f'https://www.reddit.com{link}'
    embed.set_image(url=f'attachment://meme{meme_ext}')
    embed.set_footer(text=f'{score} upvotes, {comments} comments')
    await ctx.send(file=im, embed=embed)
    
@tasks.loop(seconds=69)
async def read_memes():
    await reddit.get_submissions('pallone', 13)

@bot.event
async def on_command_error(ctx, exc):
    if type(exc) == commands.errors.BotMissingPermissions:
        await ctx.send(f'The bot is missing permissions.\nThe missing permissions are: {" ".join(exc.missing_perms)}')
    elif type(exc) == commands.errors.MissingRequiredArgument:
        await ctx.send(f'Missing required argument.\nPlease enter a value for: {exc.param}')
    elif (type(exc) == commands.errors.ArgumentParsingError or
          type(exc) == commands.errors.ExpectedClosingQuoteError or
          type(exc) == commands.errors.BadUnionArgument or
          type(exc) == commands.errors.UserInputError):
        await ctx.send(f'There was an error parsing your argument')
    elif type(exc) == commands.errors.TooManyArguments:
        await ctx.send(f'Bruh what why are there so many arguments?')
    elif type(exc) == commands.errors.CommandOnCooldown:
        await ctx.send(f'You are on cooldown. Try again in {round(exc.retry_after, 3)} seconds')
    elif type(exc) == commands.errors.CommandNotFound:
        # await ctx.send('Command not found.')
        pass
    elif type(exc) == commands.errors.MissingPermissions:
        await ctx.send(f'You are missing permissions.\nThe missing permissions are: {" ".join(exc.missing_perms)}')
    else:
        print('Command error found')

        # get data from exception
        etype = type(exc)
        trace = exc.__traceback__

        # 'traceback' is the stdlib module, `import traceback`.
        lines = traceback.format_exception(etype, exc, trace)

        # format_exception returns a list with line breaks embedded in the lines, so let's just stitch the elements together
        traceback_text = ''.join(lines)

        print(traceback_text)

        error_channel = bot.get_channel(849471377144021023)
        try:
            await error_channel.send('Command Error:\n'
                                     f'Author: {ctx.author} ({ctx.author.id})\n'
                                     f'Guild: {ctx.guild} ({ctx.guild.id})\n'
                                     f'```\n{traceback_text}\n```')
        except:
            with open('data/message.txt', 'w') as file:
                file.write(traceback_text)
            await error_channel.send(f'Command Error:\n', discord.File('data/message.txt'))

if __name__ == "__main__":
    bot.run(os.environ['BOT_TOKEN'])
