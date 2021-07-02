import discord
from discord.ext import commands

import youtube_dl


class MyLogger(object):
    def debug(self, msg):
        pass

    def warning(self, msg):
        pass

    def error(self, msg):
        print(msg)


def my_hook(d):
    if d['status'] == 'finished':
        print('Done downloading, now converting ...')


class DJ(commands.Cog):

    def __init__(self, client) -> None:
        self.client = client
        self.id = 0

    async def dl(self, url):
        path = f'assets/downloads/{self.id}.mp3'
        ydl_format = {'format': 'bestaudio/best',
                      'postprocessors': [{
                          'key': 'FFmpegExtractAudio',
                          'preferredcodec': 'mp3',
                          'preferredquality': '192',
                      }],
                      'outtmpl': path,
                      'logger': MyLogger(),
                      'progress_hooks': [my_hook], }
        self.id += 1
        with youtube_dl.YoutubeDL(ydl_format) as ydl:
            ydl.download([url])
        print('Done')
        return path

    @ commands.command(name='djenzyme', aliases=['dj', 'enzyme'])
    @ commands.cooldown(1, 10, commands.BucketType.guild)
    async def djenzyme(self, ctx, url):
        voice_channel = None
        if ctx.author.voice is None:
            for channel in ctx.guild.voice_channels:
                if 'dj' in channel.name and 'enzyme' in channel.name:
                    voice_channel = channel
                    break
            if voice_channel is None:
                await ctx.send('No valid dj enzyme channels found!')
                return
        else:
            voice_channel = ctx.author.voice.channel
            
        file = await self.dl(url)
        await ctx.send('Done downloading video.')
        await voice_channel.connect()

        voice = discord.utils.get(
            self.client.voice_clients, guild=ctx.guild)
        if not voice.is_connected():
            await voice_channel.connect()
        voice.play(discord.FFmpegPCMAudio(file))

    @ commands.command()
    async def leave(self, ctx):
        voice = discord.utils.get(self.client.voice_clients, guild=ctx.guild)
        if voice.is_connected():
            await voice.disconnect()
        else:
            await ctx.send("The bot is not connected to a voice channel.")

    @ commands.command()
    async def pause(self, ctx):
        voice = discord.utils.get(self.client.voice_clients, guild=ctx.guild)
        if voice.is_playing():
            voice.pause()
        else:
            await ctx.send("Currently no audio is playing.")

    @ commands.command()
    async def resume(self, ctx):
        voice = discord.utils.get(self.client.voice_clients, guild=ctx.guild)
        if voice.is_paused():
            voice.resume()
        else:
            await ctx.send("The audio is not paused.")

    @ commands.command()
    async def stop(self, ctx):
        voice = discord.utils.get(self.client.voice_clients, guild=ctx.guild)
        voice.stop()
