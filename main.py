from cogs.misc import Misc
from cogs.memes import Memes
from cogs.dj import DJ
from cogs.stonks import Stonks

from util import misc

import discord
from discord.ext import commands


import os
import traceback
import logging
from logging.handlers import TimedRotatingFileHandler


class MyHelpCommand(commands.MinimalHelpCommand):
    async def send_pages(self):
        destination = self.get_destination()
        e = discord.Embed(
            title='Help', color=discord.Color.blurple(), description='')
        for page in self.paginator.pages:
            e.description += page
        await destination.send(embed=e)


bot = commands.Bot(command_prefix=commands.when_mentioned_or(
    'pallone '), case_insensitive=True)
bot.help_command = MyHelpCommand()


@bot.event
async def on_command_error(ctx, exc):
    if type(exc) == commands.errors.BotMissingPermissions:
        await ctx.send(f'The bot is missing permissions.\nThe missing permissions are: {" ".join(exc.missing_perms)}')
    elif type(exc) == commands.errors.MissingRequiredArgument:
        await ctx.send(f'Missing required argument.\nPlease enter a value for: `{exc.param}`')
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
        await ctx.send(embed=misc.error_embed('Uh Oh', 'Something went wrong.'))
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
            await error_channel.send(f'Command Error:\n', file=discord.File('data/message.txt'))


bot.add_cog(DJ(bot))
bot.add_cog(Memes(bot))
bot.add_cog(Misc(bot))
bot.add_cog(Stonks(bot))

# logging to console and file on daily interval
os.makedirs('data/logs', exist_ok=True)
logging.basicConfig(format='{asctime}:{levelname}:{name}:{message}', style='{',
                    datefmt='%d-%m-%Y %H:%M:%S', level=logging.INFO,
                    handlers=[logging.StreamHandler(),
                                TimedRotatingFileHandler('data/logs/pallone.log', when='D',
                                                        backupCount=3, utc=True)])
if __name__ == "__main__":
    bot.run(os.getenv('PALLONE_TOKEN'))
