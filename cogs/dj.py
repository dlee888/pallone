import discord
from discord.ext import commands
from discord.ext import tasks

import os
import youtube_dl
import random
import youtubesearchpython as ytsearch

from util import misc


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
        self.queues = {}
        self.queries = {}
        self.voicechannels = {}
        self.bound_channels = {}
        self.refresh_queues.start()

    @tasks.loop(seconds=2)
    async def refresh_queues(self):
        for guild in self.queues.keys():
            voice = discord.utils.get(
                self.client.voice_clients, guild=await self.client.fetch_guild(guild))

            if voice is not None and not voice.is_playing() and not voice.is_paused():
                if len(self.queues[guild]) == 0:
                    await self.bound_channels[guild].send(embed=misc.info_embed('Queue is empty', 'Add more songs to start playing again.'))
                    self.queues.pop(guild)
                    self.queries.pop(guild)
                else:
                    await self.bound_channels[guild].send(embed=misc.info_embed('Now playing', self.queries[guild][0]))
                    voice.play(discord.FFmpegPCMAudio(self.queues[guild][0]))
                    self.queries[guild].remove(self.queries[guild][0])
                    self.queues[guild].remove(self.queues[guild][0])

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

    @dj.command(aliases=['c'])
    async def connect(self, ctx):
        """Connects to a voice channel.
        If you are connected to a voice channel, then it will connect to the same voice channel.
        Otherwise, it defaults to the first channel with "dj enzyme" in the channel name."""
        voice = discord.utils.get(
            self.client.voice_clients, guild=ctx.guild)
        if voice is not None:
            await ctx.send(misc.error_embed('DJ Enzyme is already connected', 'Use `pallone dj leave` before connecting to a different channel.'))

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

        await voice_channel.connect()
        self.voicechannels[ctx.guild.id] = voice_channel
        self.bound_channels[ctx.guild.id] = ctx.channel
        member = await ctx.guild.fetch_member(self.client.user.id)
        try:
            await member.edit(nick='DJ Enzyme')
        except discord.Forbidden:
            pass
        await ctx.send(embed=misc.info_embed('Connected', f'DJ Enzyme has successfully connected to channel "{voice_channel.name}"'))

    @dj.command(name='enzyme', aliases=['play', 'p'])
    @commands.cooldown(1, 3, commands.BucketType.guild)
    async def enzyme(self, ctx, url):
        """Plays a music from youtube
        Usage: `pallone dj enzyme <youtube link>`"""

        voice = discord.utils.get(
            self.client.voice_clients, guild=ctx.guild)

        if voice is None:
            await ctx.send(embed=misc.error_embed('DJ Enzyme not connected.', 'Use `pallone dj connect` to connect to a voice channel'))
            return

        file = await self.download_yt(url)
        # await ctx.send('Done downloading video.')

        if not voice.is_playing():
            await ctx.send(embed=misc.info_embed('Now playing', url))
            voice.play(discord.FFmpegPCMAudio(file))
        else:
            if not ctx.guild.id in self.queues.keys():
                self.queries[ctx.guild.id] = []
                self.queues[ctx.guild.id] = []
            self.queues[ctx.guild.id].append(file)
            self.queries[ctx.guild.id].append(url)
            await ctx.send(embed=misc.info_embed('Added to queue', f'Song {url} added to queue'))
            
    @dj.command()
    async def search(self, ctx, *, query):
        """Searches for songs on youtube"""
        voice = discord.utils.get(
            self.client.voice_clients, guild=ctx.guild)

        if voice is None:
            await ctx.send(embed=misc.error_embed('DJ Enzyme not connected.', 'Use `pallone dj connect` to connect to a voice channel'))
            return
        
        videosSearch = ytsearch.VideosSearch(query, limit=1)
        result = videosSearch.result()
        video = result['result'][0]
        print(video)
        file = await self.download_yt(video['link'])
        embed = misc.info_embed(f'''Result: "{video['title']}"''', video['link'])
        embed.set_thumbnail(url=video['thumbnails'][0]['url'])
        embed.add_field(name='Length', value=video['duration'])
        embed.set_footer(text=f"{video['viewCount']['short']}, requested by {ctx.author}", icon_url=ctx.author.avatar_url)
        await ctx.send(embed=embed)

        if not voice.is_playing():
            await ctx.send(embed=misc.info_embed('Now playing', video['link']))
            voice.play(discord.FFmpegPCMAudio(file))
        else:
            if not ctx.guild.id in self.queues.keys():
                self.queries[ctx.guild.id] = []
                self.queues[ctx.guild.id] = []
            self.queues[ctx.guild.id].append(file)
            self.queries[ctx.guild.id].append(video['link'])
            await ctx.send(embed=misc.info_embed('Added to queue', f'''Song {video['link']} added to queue'''))

    @ dj.command(aliases=['disconnect', 'dc'])
    async def leave(self, ctx):
        """Disconnects from the vc"""
        voice = discord.utils.get(self.client.voice_clients, guild=ctx.guild)
        if voice.is_connected():
            await voice.disconnect()
            self.voicechannels.pop(ctx.guild.id)
            if ctx.guild.id in self.queues.keys():
                self.queues.pop(ctx.guild.id)
                self.queries.pop(ctx.guild.id)
            self.bound_channels.pop(ctx.guild.id)
            member = await ctx.guild.fetch_member(self.client.user.id)
            try:
                await member.edit(nick='Pallone Memer')
            except discord.Forbidden:
                pass
        else:
            await ctx.send(embed=misc.error_embed('DJ Enzyme not connected.', 'Use `pallone dj connect` to connect to a voice channel'))

    @ dj.command()
    async def pause(self, ctx):
        """Pauses the music"""
        voice = discord.utils.get(self.client.voice_clients, guild=ctx.guild)
        if voice is not None and voice.is_playing():
            voice.pause()
        else:
            await ctx.send(misc.error_embed('Cannot pause audio', "Currently no audio is playing."))

    @ dj.command()
    async def resume(self, ctx):
        """Resumes the music"""
        voice = discord.utils.get(self.client.voice_clients, guild=ctx.guild)
        if voice is not None and voice.is_paused():
            voice.resume()
        else:
            await ctx.send(misc.error_embed("The audio is not paused", 'Nice try tho'))

    @ dj.command(aliases=['skip'])
    async def stop(self, ctx):
        """Stops playing music"""
        voice = discord.utils.get(self.client.voice_clients, guild=ctx.guild)
        if voice is not None:
            voice.stop()
        else:
            await ctx.send(misc.error_embed("There are no songs playing", 'Next time you try actually add songs to skip.'))

    @dj.command(aliases=['q'])
    async def queue(self, ctx):
        """Sends the queue"""
        if ctx.guild.id in self.queries.keys():
            await ctx.send(embed=misc.info_embed('Queue', '\n'.join(self.queries[ctx.guild.id])))
        else:
            await ctx.send(embed=misc.error_embed('No queue found', 'There is no queue for this server.'))

    @dj.command(aliases=['clr'])
    async def clear(self, ctx):
        """Clears the queue"""
        if ctx.guild.id in self.queries.keys():
            self.queues.pop(ctx.guild.id)
            self.queries.pop(ctx.guild.id)
            await ctx.send(embed=misc.info_embed('Queue cleared', 'Queue is now empty.'))
        else:
            await ctx.send(embed=misc.error_embed('No queue found', 'There is no queue for this server.'))

    @dj.command()
    async def shuffle(self, ctx):
        if ctx.guild.id in self.queries.keys():
            random.shuffle(self.queues[ctx.guild.id])
            random.shuffle(self.queries[ctx.guild.id])
            await ctx.send(embed=misc.info_embed('Queue shuffled', 'Queue:\n' + '\n'.join(self.queries[ctx.guild.id])))
        else:
            await ctx.send(embed=misc.error_embed('No queue found', 'There is no queue for this server.'))
