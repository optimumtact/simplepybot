import network


network.connect(("irc.segfault.net.nz", 6668), "parrot", "wolololol", "homeland.net.nz",
        "francis is a francis is a francis")

network.join("bots")

while True:
    for message in network.get_messages():
        print message
