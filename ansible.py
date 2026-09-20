from discord.ext import commands
from discord.commands import Option
import discord
import os
import io
import stat
import paramiko
import base64
from dotenv import load_dotenv

load_dotenv()
class play_select(discord.ui.Select):
    def __init__(self, playbooks, ssh_client, playbook_dir):
        options= []
        self.ssh_client = ssh_client
        self.playbook_dir = playbook_dir
        for play in playbooks:
            options.append(discord.SelectOption(label=play))
        super().__init__(placeholder="Select a command to run", max_values=1, min_values=1, options=options)
    async def callback(self, interaction: discord.Interaction):
        await interaction.response.defer()
        stdin, stdout, stderr = self.ssh_client.exec_command("ansible-playbook " + self.playbook_dir + "/" + self.values[0])
        wait_for_exit = stdout.channel.recv_exit_status()
        content=stdout.read().decode('utf8').strip()
        await interaction.followup.send(content=content or "no output", ephemeral=False, delete_after=60)

#view for dropdown menu
class play_view(discord.ui.View):
    def __init__(self, playbooks, ssh_client, playbook_dir, *, timeout = 15.0):
        super().__init__(timeout=timeout)
        self.dropdown = play_select(playbooks, ssh_client, playbook_dir)
        self.add_item(self.dropdown)
    async def on_timeout(self):
         self.clear_items()


class Ansible(commands.Cog, name="Ansible"):
    def __init__(self, wbot: commands.Bot):
        self.bot = wbot
        # init ssh client
        self.ssh_client = paramiko.SSHClient()
        # auto accept host keys, note this can be dangerous, take this out later - gh
        self.ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())



        # set ssh parameters
        self.ssh_host = os.getenv("SSH_HOST")
        self.ssh_port = os.getenv("SSH_PORT")
        self.ssh_user = os.getenv("SSH_USER")
        self.playbook_dir = os.getenv("ANSIBLE_PLAY_DIR")
        #import private key
        pkey_obj = io.StringIO(base64.b64decode(os.getenv("SSH_KEY_B64")).decode('utf-8'))
        #note key has to be ed25519 because paramiko cannot auto detect when its not a file; come back to this in the future to have auto detection work properly - gh
        self.ssh_key = paramiko.Ed25519Key.from_private_key(pkey_obj)
        self.ssh_key_passphrase = os.getenv("SSH_KEY_PASSPHRASE") or None

    @discord.slash_command(name='run', description='run a playbook')
    async def run(self,ctx):
        try:
            self.ssh_client.connect(self.ssh_host, port=self.ssh_port, username=self.ssh_user, pkey=self.ssh_key)
            sftp = self.ssh_client.open_sftp()
            playbooks = sorted(
                file.filename for file in sftp.listdir_attr(self.playbook_dir)
                if stat.S_ISREG(file.st_mode)
            )
            play_menu = play_view(playbooks, self.ssh_client, self.playbook_dir)
            await ctx.respond("Please select a Command", view = play_menu, delete_after=15)



            #await ctx.respond(stdout.read().decode('utf8').strip())
        except Exception as e:
            await ctx.respond(e)

def setup(wbot):
    wbot.add_cog(Ansible(wbot))

