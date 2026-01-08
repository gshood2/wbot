from discord.ext import commands
from discord.commands import Option
import os
import discord
import requests
from ddgs import DDGS
from dotenv import load_dotenv
import asyncio
import newspaper
from openai import AsyncClient

load_dotenv()
class Ai(commands.Cog, name="Ai"):
    def __init__(self, wbot: commands.Bot):
        self.bot = wbot
        self.client = AsyncClient(base_url=os.getenv("OPENWEBUI_HOST"), api_key=os.getenv("OPENWEBUI_KEY"))
        
    @discord.slash_command(name='ask', description='ask JoeyBot')
    async def ask(self, ctx, prompt, search: Option(bool, "enable or disable search", default=False)):
        await ctx.response.defer()
        buffer = ""
        last_edit = 0
        msg = None
        try:
            # perform duck duck go search if search is requested
            if search is True:
                site_content = ""
                results = DDGS().text(prompt, max_results=2)
                #print(results)
                #extract text from the results
                for result in results:
                    url = result.get('href')
                    site = newspaper.article(url)
                    site.download()
                    site.parse()
                    # save the first 3000 characters
                    site_content += site.text[:3000]
                final_prompt = site_content + " Please use the above information to help answer. " + prompt
                prompt = final_prompt
                print(prompt)
        except Exception as e:
            #send error message if search fails
            if msg is None:
                await ctx.followup.send(content=f"Error searching: {e}")


        try:
            #send request to open web ui and stream the results
            response = await self.client.chat.completions.create(
                model=os.getenv("MODEL"),
                messages=[{"role":"user","content": prompt }],
                temperature=0.6,
                max_tokens=400,
                stream=True
            )
            async for chunk in response:
                delta = chunk.choices[0].delta
                if delta.content:
                    buffer += delta.content
                    # throttle edits
                    if len(buffer) - last_edit > 50:
                        if msg is None:
                            msg = await ctx.followup.send(buffer)
                            last_edit = len(buffer)
                        else:
                            await msg.edit(content=buffer)
                            last_edit = len(buffer)
                       
            final_text = buffer.strip() or "(No response generated)"
            if msg is None:
                await ctx.followup.send(final_text[:2000])
            else:
                await msg.edit(content=final_text[:2000])
        except Exception as e:
        # fallback in case of streaming error
            if msg is None:
                await ctx.followup.send(content=f"Error generating response: {e}")
            else:
                await msg.edit(content=f"Error generating response: {e}")

def setup(wbot):
    wbot.add_cog(Ai(wbot))
