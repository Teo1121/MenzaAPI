import discord
import requests
import json
import os

class MyClient(discord.Client):
    COMMANDS = {"!list"   : lambda args : requests.get("http://127.0.0.1:8081/menza?menza="+'%20'.join(args)).json(),
                "!signup" : lambda args : requests.post("http://127.0.0.1:8081/email",json={"email":args[0],"subs":args[1]}).json(),
                "!help"   : lambda args : {"message":"!list <menza> - check out today's menu!\n!signup <email> <subs> - signup to the email subscription"}}

    async def on_ready(self):
        print('Logged on as {0}!'.format(self.user))

    async def on_message(self, message : discord.message.Message):
        if message.author == self.user:
            return

        print('Message from {0.author}: {0.content}'.format(message))
        command = message.content.split(' ')

        if command[0] in MyClient.COMMANDS:
            response = MyClient.COMMANDS[command[0]](command[1:])
            if 'data' in response:
                try:
                    await message.channel.send(json.dumps(response['data'], ensure_ascii=False, indent=4))
                except discord.errors.HTTPException as e:
                    await message.channel.send(e.text)
            else:
                await message.channel.send(response['message'])

client = MyClient()
client.run(os.environ['DISCORD_KEY'])