import discord
from discord import player
from discord.ext import commands
from discord.ext import tasks

import os
import youtube_dl
import random
import youtubesearchpython as ytsearch
import time

from util import misc

RICK_ROLL = 'https://www.youtube.com/watch?v=dQw4w9WgXcQ'
TEMP_DIR = 'temp'

class MyLogger(object):
    def debug(self, msg):
        pass

    def warning(self, msg):
        pass

    def error(self, msg):
        print(msg)


class YTDownloader:

    def __init__(self, folder):
        self.folder = folder
        os.makedirs(folder, exist_ok=True)
        self.id = 0

    def download_yt(self, url):
        path = f'{self.folder}/{self.id}.mp3'
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
        return path


downloader = YTDownloader(os.path.join(TEMP_DIR, 'yt_dl'))


class Video:

    def __init__(self, url, requester) -> None:
        self.url = url
        self.path = downloader.download_yt(url)
        info = ytsearch.Video.getInfo(url, mode=ytsearch.ResultMode.dict)
        self.thumbnail_url = info['thumbnails'][0]['url']
        self.title = info['title']
        self.viewcount = info['viewCount']['text']
        self.info = info
        self.requester = requester

    def to_embed(self):
        embed = misc.info_embed('Now playing', f'[{self.title}]({self.url})')
        embed.set_thumbnail(url=self.thumbnail_url)
        # embed.add_field(name='Length', value=video['duration'])
        embed.set_footer(
            text=f"{self.viewcount} views. Requested by {self.requester}", icon_url=self.requester.avatar_url)
        return embed

    def __str__(self) -> str:
        return f'[{self.title}]({self.url})'

    def play(self, voice):
        voice.play(discord.FFmpegPCMAudio(self.path))


class Queue:

    def __init__(self, voicechannel, boundchannel, client) -> None:
        self.videos = []
        self.vc = voicechannel
        self.bc = boundchannel
        self.client = client
        self.warned = True
        self.playing = None
        self.self_destruct = None
        self.loop = False

    def top(self):
        return self.videos[0]

    def pop(self):
        if self.loop and self.playing is not None:
            self.videos.append(self.playing)
        self.playing = self.videos[0]
        self.videos.remove(self.videos[0])

    def push(self, video):
        if random.randint(1, 10) == 1:
            rick = Video(RICK_ROLL, self.client)
            if rick is not None:
                self.videos.append(rick)
        else:
            if video is not None:
                self.videos.append(video)
        self.warned = False
        self.self_destruct = None

    def empty(self):
        return len(self.videos) == 0

    def __str__(self) -> str:
        if len(self.videos) == 0:
            return 'Queue is empty'
        return '\n'.join([str(vid) for vid in self.videos])


class DJ(commands.Cog):

    def __init__(self, client) -> None:
        self.client = client
        self.id = 0
        self.queues = {}
        self.refresh_queues.start()

    @tasks.loop(seconds=2)
    async def refresh_queues(self):
        for guild, queue in self.queues.items():
            voice = discord.utils.get(
                self.client.voice_clients, guild=await self.client.fetch_guild(guild))

            if voice is not None and not voice.is_playing() and not voice.is_paused():
                if queue.empty():
                    if not queue.warned:
                        await queue.bc.send(embed=misc.info_embed('Queue is empty', 'Add more songs to start playing again.'))
                        queue.warned = True
                        queue.self_destruct = time.time() + 120
                    if queue.self_destruct is not None and time.time() > queue.self_destruct:
                        await voice.disconnect()
                        self.queues.pop(guild)
                else:
                    await queue.bc.send(embed=queue.top().to_embed())
                    queue.top().play(voice)
                    queue.pop()

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
            await ctx.send(misc.error_embed('DJ Enzyme is already connected', 'Use `pallone dj disconnect` before connecting to a different channel.'))

        voice_channel = None
        if ctx.author.voice is None:
            for channel in ctx.guild.voice_channels:
                if 'dj' in channel.name or 'enzyme' in channel.name:
                    voice_channel = channel
                    break
            if voice_channel is None:
                await ctx.send('No valid DJ Enzyme channels found!')
                return
        else:
            voice_channel = ctx.author.voice.channel

        await voice_channel.connect()
        self.queues[ctx.guild.id] = Queue(voice_channel, ctx.channel, self.client)
        await ctx.send(embed=misc.info_embed('Connected', f'DJ Enzyme has successfully connected to channel "{voice_channel.name}"'))

    @dj.command(aliases=['p'])
    @commands.cooldown(1, 3, commands.BucketType.guild)
    async def play(self, ctx, url):
        """Plays a music from youtube
        Usage: `pallone dj enzyme <youtube link>`"""
        url = url.strip('<>[]()')
        voice = discord.utils.get(
            self.client.voice_clients, guild=ctx.guild)

        if voice is None:
            await ctx.send(embed=misc.error_embed('DJ Enzyme not connected.', 'Use `pallone dj connect` to connect to a voice channel'))
            return

        self.queues[ctx.guild.id].push(Video(url, ctx.author))
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

        embed = misc.info_embed(
            f'''Result: "{video['title']}"''', video['link'])
        embed.set_thumbnail(url=video['thumbnails'][0]['url'])
        embed.add_field(name='Length', value=video['duration'])
        embed.set_footer(
            text=f"{video['viewCount']['short']}, requested by {ctx.author}", icon_url=ctx.author.avatar_url)
        await ctx.send(embed=embed)

        self.queues[ctx.guild.id].push(
            Video(video['link'], ctx.author))
        await ctx.send(embed=misc.info_embed('Added to queue', f'''Song {video['link']} added to queue'''))

    @dj.command(aliases=['disconnect', 'dc'])
    async def leave(self, ctx):
        """Disconnects from the vc"""
        voice = discord.utils.get(self.client.voice_clients, guild=ctx.guild)
        if voice is not None and voice.is_connected():
            await voice.disconnect()
            self.queues.pop(ctx.guild.id)
            await ctx.send(embed=misc.info_embed('Disconnected', 'DJ Enzyme has succesfully disconnected.'))
        else:
            await ctx.send(embed=misc.error_embed('DJ Enzyme not connected.', 'Use `pallone dj connect` to connect to a voice channel.'))

    @dj.command()
    async def pause(self, ctx):
        """Pauses the music"""
        voice = discord.utils.get(self.client.voice_clients, guild=ctx.guild)
        if voice is not None and voice.is_playing():
            voice.pause()
        else:
            await ctx.send(embed=misc.error_embed('Cannot pause audio', "Currently no audio is playing."))

    @dj.command()
    async def resume(self, ctx):
        """Resumes the music"""
        voice = discord.utils.get(self.client.voice_clients, guild=ctx.guild)
        if voice is not None and voice.is_paused():
            voice.resume()
        else:
            await ctx.send(embed=misc.error_embed("The audio is not paused", 'Nice try tho'))

    @dj.command(aliases=['skip'])
    async def stop(self, ctx):
        """Stops playing music"""
        voice = discord.utils.get(self.client.voice_clients, guild=ctx.guild)
        if voice is not None:
            voice.stop()
        else:
            await ctx.send(embed=misc.error_embed("There are no songs playing", 'Next time you try actually add some songs.'))

    @dj.command(aliases=['q'])
    async def queue(self, ctx):
        """Sends the queue"""
        if ctx.guild.id in self.queues.keys():
            await ctx.send(embed=misc.info_embed('Queue', str(self.queues[ctx.guild.id])))
        else:
            await ctx.send(embed=misc.error_embed('No queue found', 'There is no queue for this server.'))

    @dj.command(aliases=['np'])
    async def playing(self, ctx):
        """Sends the current song playing"""
        if ctx.guild.id in self.queues.keys():
            if self.queues[ctx.guild.id].playing is None:
                await ctx.send(embed=misc.error_embed('Nothing is playing', 'Add more songs to start playing.'))
            else:
                embed = self.queues[ctx.guild.id].playing.to_embed()
                voice = discord.utils.get(
                    self.client.voice_clients, guild=ctx.guild)
                if voice.is_paused():
                    embed.description += '\n(Song is paused)'
                await ctx.send(embed=embed)
        else:
            await ctx.send(embed=misc.error_embed('No queue found', 'There is no queue for this server.'))

    @dj.command(aliases=['clr'])
    async def clear(self, ctx):
        """Clears the queue"""
        if ctx.guild.id in self.queues.keys():
            await ctx.send(embed=misc.info_embed('Queue cleared', 'Queue is now empty.'))
        else:
            await ctx.send(embed=misc.error_embed('No queue found', 'There is no queue for this server.'))

    @dj.command()
    async def shuffle(self, ctx):
        """Shuffles the queue"""
        if ctx.guild.id in self.queues.keys():
            random.shuffle(self.queues[ctx.guild.id].videos)
            await ctx.send(embed=misc.info_embed('Queue shuffled', f'Queue:\n{self.queues[ctx.guild.id]}'))
        else:
            await ctx.send(embed=misc.error_embed('No queue found', 'There is no queue for this server.'))

    @commands.command()
    async def loop(self, ctx, looped : bool = None):
        """Loops the queue"""
        if ctx.guild.id in self.queues.keys():
            if looped is None:
                await ctx.send(embed=misc.info_embed('Queue', f'Queue is {["not looped", "looped"][self.queues[ctx.guild.id]].loop}.'))
            else:
                self.queues[ctx.guild.id].loop = looped
                await ctx.send(embed=misc.info_embed('Loop', f'Queue is now {["not looping", "looping"][looped]}.'))
        else:
            await ctx.send(embed=misc.error_embed('No queue found', 'There is no queue for this server.'))


def setup(bot):
    bot.add_cog(DJ(bot))
