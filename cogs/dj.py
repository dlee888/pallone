import discord
from discord.ext import commands

import os
import youtube_dl


class MyLogger(object):
    def debug(self, msg):
        pass

    def warning(self, msg):
        pass

    def error(self, msg):
        print(msg)


class DJ(commands.Cog):

    def __init__(self, client) -> None:
        self.client = client
        self.id = 0

    async def download_yt(self, url):
        path = f'assets/downloads/{self.id}.mp3'
        ydl_format = {'format': 'bestaudio/best',
                      'postprocessors': [{
                          'key': 'FFmpegExtractAudio',
                          'preferredcodec': 'mp3',
                          'preferredquality': '192',
                      }],
                      'outtmpl': path,
                      'logger': MyLogger(), }
        if os.path.exists(path):
            os.remove(path)
        self.id += 1
        with youtube_dl.YoutubeDL(ydl_format) as ydl:
            ydl.download([url])
        # print('Done')
        return path

    @commands.group(brief='DJ Enzyme', invoke_without_command=True)
    async def dj(self, ctx):
        """Basically a music bot. Plays music from youtube."""
        await ctx.send_help('dj')

    @dj.command(name='enzyme', aliases=['play', 'p'])
    @commands.cooldown(1, 10, commands.BucketType.guild)
    async def enzyme(self, ctx, url):
        """Plays a music from youtube
        Usage: pallone dj enzyme <youtube link>"""
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
                await ctx.send(f'You are not in a voice channel. Defaulting to channel {voice_channel.name}')
        else:
            voice_channel = ctx.author.voice.channel

        file = await self.download_yt(url)
        await ctx.send('Done downloading video.')
        member = await ctx.guild.fetch_member(self.client.user.id)
        try:
            await member.edit(nick='DJ Enzyme')
        except discord.Forbidden:
            pass
        await voice_channel.connect()

        voice = discord.utils.get(
            self.client.voice_clients, guild=ctx.guild)
        if not voice.is_connected():
            await voice_channel.connect()
        voice.play(discord.FFmpegPCMAudio(file))

    @ dj.command(aliases=['disconnect', 'dc', 'lv'])
    async def leave(self, ctx):
        """Disconnects from the vc"""
        voice = discord.utils.get(self.client.voice_clients, guild=ctx.guild)
        if voice.is_connected():
            await voice.disconnect()
            member = await ctx.guild.fetch_member(self.client.user.id)
            try:
                await member.edit(nick='Pallone Memer')
            except discord.Forbidden:
                pass
        else:
            await ctx.send("The bot is not connected to a voice channel.")

    @ dj.command()
    async def pause(self, ctx):
        """Pauses the music"""
        voice = discord.utils.get(self.client.voice_clients, guild=ctx.guild)
        if voice.is_playing():
            voice.pause()
        else:
            await ctx.send("Currently no audio is playing.")

    @ dj.command()
    async def resume(self, ctx):
        """Resumes the music"""
        voice = discord.utils.get(self.client.voice_clients, guild=ctx.guild)
        if voice.is_paused():
            voice.resume()
        else:
            await ctx.send("The audio is not paused.")

    @ dj.command()
    async def stop(self, ctx):
        """Stops playing music"""
        voice = discord.utils.get(self.client.voice_clients, guild=ctx.guild)
        voice.stop()
