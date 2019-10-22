from pythonosc import udp_client

localIP     = "127.0.0.1"
localPort   = 20001

client = udp_client.SimpleUDPClient(localIP, localPort)
x = 150
y = 100

# Message format: shape/name/x/y/
coords = 'rectangle/{}/{}/{}/'.format("paddle1", x, y)
client.send_message(coords, 'nonsense')
coords = 'rectangle/{}/{}/{}/'.format("paddle2", x+100, y+150)
client.send_message(coords, 'nonsense')