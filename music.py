from discord.ext import commands
import discord
from yt_dlp import YoutubeDL
import json
from youtube_search import YoutubeSearch


class Music(commands.Cog):
    def __init__(self, wbot: commands.Bot):
        self.bot = wbot
        self.queue_list = []
        self.title = []

    @discord.slash_command(name='play', description='play a video')
    async def play(self, ctx, video=None):
        vc = discord.utils.get(self.bot.voice_clients, guild=ctx.guild)
        #dropdown menu
        class search_select(discord.ui.Select):
            def __init__(self, search):
                options=[  
                    discord.SelectOption(label=str(search[0]['title']),emoji="📹",description="Channel: " + str(search[0]['channel']) 
                    + ' Duration: ' + str(search[0]['duration']) + ' Published: ' + str(search[0]['publish_time'])),
                    discord.SelectOption(label=str(search[1]['title']),emoji="📹",description="Channel: " + str(search[1]['channel']) 
                    + ' Duration: ' + str(search[1]['duration']) + ' Published: ' + str(search[1]['publish_time'])),
                    discord.SelectOption(label=str(search[2]['title']),emoji="📹",description="Channel: " + str(search[2]['channel']) 
                    + ' Duration: ' + str(search[2]['duration']) + ' Published: ' + str(search[2]['publish_time'])),
                    discord.SelectOption(label=str(search[3]['title']),emoji="📹",description="Channel: " + str(search[3]['channel']) 
                    + ' Duration: ' + str(search[3]['duration']) + ' Published: ' + str(search[3]['publish_time'])),
                    discord.SelectOption(label=str(search[4]['title']),emoji="📹",description="Channel: " + str(search[4]['channel']) 
                    + ' Duration: ' + str(search[4]['duration']) + ' Published: ' + str(search[4]['publish_time'])),
                    ]
                super().__init__(placeholder="Select an option",max_values=1,min_values=1,options=options)
            async def callback(self, interaction: discord.Interaction):
                if self.values[0] == search[0]['title']:
                    SUFFIX = search[0]['url_suffix']
                elif self.values[0] == search[1]['title']:
                    SUFFIX = search[1]['url_suffix']
                elif self.values[0] == search[2]['title']:
                    SUFFIX = search[2]['url_suffix']
                elif self.values[0] == search[3]['title']:
                    SUFFIX = search[3]['url_suffix']
                elif self.values[0] == search[4]['title']:
                    SUFFIX = search[4]['url_suffix']
                URL = 'https://www.youtube.com' + SUFFIX
                add(URL)
                await interaction.response.send_message(content=f"Adding to queue {URL}!",ephemeral=False, delete_after=60)

                

        #view for dropdown menu
        class search_view(discord.ui.View):
            def __init__(self, search, *, timeout = 15.0):
                super().__init__(timeout=timeout)
                self.dropdown = search_select(search)
                self.add_item(self.dropdown)
            async def on_timeout(self):
                 self.clear_items()

        # youtube dl wrapper, returns audio url and title of video in a tuple
        def ytdl(URL):
            ydl_opts = { 'js_runtimes': {'deno': {
            'path': '/root/.deno/bin/deno'}},  # Replace with the actual path to deno executable
         'format': 'bestaudio', 'noplaylist': 'true' }
            with YoutubeDL(ydl_opts) as ydl:
                video_info = ydl.extract_info(URL, download=False)
                return video_info['url'], video_info['title']

        def queue_loop(queue_list):
            if vc.is_connected() == True and len(self.queue_list) > 0:
                source = self.queue_list[0]
                self.queue_list.pop(0)
                self.title.pop(0)
                vc.play(discord.FFmpegPCMAudio(source, before_options='-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5'),
                        after=lambda e: queue_loop(self.queue_list))
        def add(URL):
            video_data = ytdl(URL)
            self.queue_list.append(video_data[0])
            self.title.append(video_data[1])
            if not vc.is_playing():
                queue_loop(self.queue_list)   
        if ctx.user.voice is None:
            await ctx.respond("Please join a voice channel")
        elif video == None:
            vc.resume()
            await ctx.respond("Playing", delete_after=100)
        else:
            channel = ctx.user.voice.channel
            global URL
            if vc is None:
                vc = await channel.connect()
            else:
                await vc.move_to(channel)
            if "https:" in video:
                 URL = video
                 add(URL)
            else:
                search = YoutubeSearch(video, max_results=5).to_dict()
                search_dropdown = search_view(search)
                await ctx.respond('Please select a video', view = search_dropdown, delete_after=15)
       

    @discord.slash_command(name='pause', description='pause audio')
    async def pause(self, ctx):
        vc = discord.utils.get(self.bot.voice_clients, guild=ctx.guild)
        if vc is None:
            await ctx.respond('Nothing is playing???', delete_after=100)
        else:
            vc.pause()
            await ctx.respond('Audio paused', delete_after=100)

    @discord.slash_command(name='resume', description='resume audio')
    async def resume(self, ctx):
        vc = discord.utils.get(self.bot.voice_clients, guild=ctx.guild)
        if vc is None:
            await ctx.respond('Nothing is playing???', delete_after=100)
        elif vc.is_playing() is True:
            await ctx.respond('Audio is already playing', delete_after=100)
        else:
            vc.resume()
            await ctx.respond('Resumed Playback', delete_after=100)

    @discord.slash_command(name='stop', description='stops audio and clears queue')
    async def stop(self, ctx):
        vc = discord.utils.get(self.bot.voice_clients, guild=ctx.guild)
        if vc.is_playing is False:
            await ctx.respond('Nothing is playing???', delete_after=100)
        else:
            vc.stop()
            self.queue_list.clear()
            self.title.clear()
            await ctx.respond('Stopped Playback', delete_after=100)

    @discord.slash_command(name='skip', description='skips what is playing')
    async def stop(self, ctx):
        vc = discord.utils.get(self.bot.voice_clients, guild=ctx.guild)
        if vc.is_playing is False:
            await ctx.respond('Nothing is playing???', delete_after=100)
        else:
            vc.stop()
            await ctx.respond('Skipped', delete_after=100)

    @discord.slash_command(name='queue', description='show queue')
    async def queue(self, ctx):
        if len(self.title) > 0:
            queue_num = 0
            queue_list = ''
            for title in self.title:
                queue_num += 1
                number = str(queue_num)
                queue_list = queue_list + number + ': ' + title + ' \n'
            await ctx.respond(queue_list, delete_after=100)
        else:
            await ctx.respond('Nothing is queued', delete_after=100)


def setup(wbot):
    wbot.add_cog(Music(wbot))
