import discord, markovify, asyncio, json, re

##########
# CONFIG #
##########

# owner userid
ownerid = 197463298151677953

# Set this to the path your text is
textfile = "cache.txt"

# cache
cachefile = "cache.json"
# initial message count on new channels
cachesize = 300

# Bot token goes here
tokenfile = 'token.txt'

# set to False if you want it to seperate sentences based on periods instead of newlines
newline = True

# Set the commands to trigger a markov.
prefix = '.'
command = ".markov"
altcommand = ".mk"

################

client = discord.Client()

def getLinesNo():
    with open(textfile) as f:
        return sum(1 for _ in f)

def getCached():
    try:
        with open(cachefile) as f:
            d = json.loads(f.read())
        return d
    except:
        return json.loads('[]')

def setCached(c):
    with open(cachefile, "w") as f:
        f.write(json.dumps(c))

def scInCache(server, channel):
    cached = getCached()
    for s in cached:
        if s['id'] == server.id:
            for c in s['channels']:
                if c == channel.id:
                    return True
    return False

def appendSc(server, channel):
    cached = getCached()
    serv = None

    for i,s in enumerate(cached):
        if s['id'] == server.id:
            serv = i
            break
    if serv == None:
        serv = {"id": server.id, "channels": [channel.id], "blacklist": []}
        cached.append(serv)
    else:
        cached[serv]['channels'].append(channel.id)

    print(cached)
    setCached(cached)

def isBlacklisted(server, channel):
    cached = getCached()
    for s in cached:
        if s['id'] == server.id:
            for c in s['blacklist']:
                if c == channel.id:
                    return True
    return False

async def blacklist(server, from_channel, channel):
    cached = getCached()
    serv = None

    for i,s in enumerate(cached):
        if s['id'] == server.id:
            serv = i
            break
    if serv == None:
        return False
    elif channel.id in cached[serv]['blacklist']:
        await from_channel.send('Channel %s is already on the blacklist.' % channel.mention)
        return False
    else:
        await from_channel.send('Added %s to the blacklist.' % channel.mention)
        cached[serv]['blacklist'].append(channel.id)

    setCached(cached)
    return True

async def unBlacklist(server, from_channel, channel):
    cached = getCached()
    serv = None

    for i,s in enumerate(cached):
        if s['id'] == server.id:
            serv = i
            break
    if serv == None:
        return False
    elif channel.id not in cached[serv]['blacklist']:
        await from_channel.send('Channel %s is not on the blacklist.' % channel.mention)
        return False
    else:
        cached[serv]['blacklist'].remove(channel.id)
        await from_channel.send('Channel %s is no longer on the blacklist.' % channel.mention)

    setCached(cached)
    return True

def getChannelMentions(server):
    cached = getCached()

    for s in cached:
        if s['id'] == server.id:
            m = ""
            for c in s['channels']:
                channel = server.get_channel(c)
                m += "%s\n" % channel.mention
            return m

    return ""


@client.event
async def on_ready():
    print('Logged in as:\n{0.name}, {0.id}\n'.format(client.user))

@client.event
async def on_message(message):
    if message.author == client.user or (message.content == '' and len(message.attachments) == 0):
        return

    if not isBlacklisted(message.guild, message.channel):
        if not scInCache(message.guild, message.channel):
            print('%s not in cache. Caching %d messages from history.' % (message.channel, cachesize))
            appendSc(message.guild, message.channel)   
            await markovcache(message.channel)
        elif not message.content.startswith('.'):
            with open(textfile, "a") as f:
                if message.content:
                    print('Appending message %s' % message.content)
                    f.write('%s\n' % message.content)
                if len(message.attachments) > 0:
                    attachment = message.attachments[0]
                    url = attachment.url
                    print('Appending url %s' % url)
                    f.write('%s\n' % url)

    args = message.content.lower().split(' ')

    if args[0] == command or args[0] == altcommand:
        sentence = await markov()
        sentence = re.sub(r'<@.*>', '', sentence)
        print('Sending "%s" to %s' % (sentence, message.channel.name))
        await message.channel.send(sentence)
    elif args[0] == '.mkstats':
        lines = getLinesNo()
        channels_cached = getChannelMentions(message.guild).strip()
        await message.channel.send('I have `%d` lines of random messages :)\n\nI have those channels cached:\n%s' % (lines, channels_cached))
    elif args[0] == '.mkblacklist':
        if len(args) == 2:
            if message.author.guild_permissions.administrator or message.author.id == ownerid:
                await blacklist(message.guild, message.channel, message.guild.get_channel(int(args[1])))
            else:
                await message.channel.send('You have to be an Administrator to do that.')
    elif args[0] == '.mkunblacklist':
        if len(args) == 2:
            if message.author.guild_permissions.administrator or message.author.id == ownerid:
                await unBlacklist(message.guild, message.channel, message.guild.get_channel(int(args[1])))
            else:
                await message.channel.send('You have to be an Administrator to do that.')


async def markov():
    # TODO: Optimise this
    with open(textfile, "r") as t:
        text = t.read()

    if newline:
        model = markovify.text.NewlineText(text, well_formed=False)
    else:
        model = markovify.Text(text, well_formed=False)

    # return one random sentence to send
    m = None
    while m == None or m == '':
        m = model.make_sentence()
    return m

async def markovcache(channel):
    msgs = await channel.history(limit=cachesize).flatten()

    o = ""
    for msg in msgs:
        content = msg.content
        o += '%s\n' % content

    with open(textfile, "a+") as f:
        f.write(o)

with open(tokenfile) as f:
    bottoken = f.read()
client.run(bottoken)
