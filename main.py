import discord
from discord.ext import commands
from discord.ext import tasks

import random
import os

import reddit

bot = commands.Bot(command_prefix=commands.when_mentioned_or('pallone '))


@bot.event
async def on_ready():
    game = discord.Game('"pallone help"')
    await bot.change_presence(status=discord.Status.dnd, activity=game)
    read_memes.start()
    print('Bot is ready')

@bot.command()
async def ping(ctx):
    '''Is the bot online?'''
    await ctx.send(f'Pong! Latency = {round(bot.latency * 1000, 3)} ms')

@bot.command(name='meme')
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
    
@tasks.loop(seconds=41)
async def read_memes():
    await reddit.get_submissions('pallone', 13)

if __name__ == "__main__":
    bot.run(os.environ['BOT_TOKEN'])
