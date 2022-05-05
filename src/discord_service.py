import discord
import requests
import json
import os

def subscribe(args):
    restaurants = list(map(lambda x : x.strip(),' '.join(args[1:]).split(',')))
    try:
        restaurants = list(map(int,restaurants))
        key = "ids"
    except ValueError:
        key = "names"
    return requests.post("http://127.0.0.1:8081/email/sub",json={"uuid":args[0], key : restaurants}).json()

class MyClient(discord.Client):
    COMMANDS = {"!list"      : lambda args : requests.get("http://127.0.0.1:8081/menza/list").json(),
                "!menza"     : lambda args : requests.get("http://127.0.0.1:8081/menza/"+" ".join(args)).json(),
                "!signup"    : lambda args : requests.post("http://127.0.0.1:8081/email",json={"email":args[0]}).json(),
                "!subscribe" : subscribe,
                "!help"      : lambda args : {"message":
"""!list - list available restaurants
!menza <restaurant_identifier> - check out today's menu!
!signup <email> - signup to the email subscription
!subscribe <uuid> <restaurant_identifiers> - subscribe to a restaurant
"""}}

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