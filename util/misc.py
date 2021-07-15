import discord


async def send_cooldown_embed(ctx, cooldown):
    embed = discord.Embed(title='Too spicy, take a breather',
                          description=f'You\'ll be able to use this command again in {round(cooldown, 2)} seconds', color=discord.Color.blue())
    await ctx.send(embed=embed)

def info_embed(title, description):
    return discord.Embed(title=title, description=description, color=discord.Color.green())
def error_embed(title, description):
    res = discord.Embed(title=title, description=description, color=discord.Color.red())
    res.set_thumbnail(url='https://imgur.com/FKXyPgz.png')
    return res