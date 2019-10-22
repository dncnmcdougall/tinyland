from pythonosc import udp_client

localIP     = "127.0.0.1"
localPort   = 20001

client = udp_client.SimpleUDPClient(localIP, localPort)

# Message format: shape/name/x/y/w/h/
message = 'rectangle/{}/{}/{}/{}/{}/'.format("paddle1", 100, 200, 20, 40)
client.send_message(message, 'nonsense')
# message = 'rectangle/{}/{}/{}/'.format("paddle2", x+100, y+150)
# client.send_message(message, 'nonsense')