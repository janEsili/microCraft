import random

from quarry.net.server import ServerProtocol, ServerFactory
from twisted.internet import reactor


class MainProtocol(ServerProtocol):

    random.seed()

    def __init__(self, factory, remote_addr):
        super().__init__(factory, remote_addr)
        self.alive_key = 0

    def player_joined(self):
        ServerProtocol.player_joined(self)

        # Send "Join Game" packet
        self.send_packet("join_game",
                         self.buff_type.pack("iBqiB",
                                             0,  # entity id
                                             3,  # game mode
                                             0,  # dimension
                                             0,  # hashed seed
                                             0),  # max players
                         self.buff_type.pack_string("flat"),  # level type
                         self.buff_type.pack_varint(32),  # view distance
                         self.buff_type.pack("??",
                                             False,  # reduced debug info
                                             False))  # show respawn screen

        # Send "Player Position and Look" packet
        self.send_packet("player_position_and_look",
                         self.buff_type.pack("dddff?",
                                             0,  # x
                                             255,  # y
                                             0,  # z
                                             0,  # yaw
                                             0,  # pitch
                                             0b00000),  # flags
                         self.buff_type.pack_varint(0))  # teleport id

        # Start sending "Keep Alive" packets
        self.ticker.add_loop(20, self.keep_alive())

        # Announce player joined
        self.factory.send_chat(u"\u00a7e%s has joined." % self.display_name)

    def player_left(self):
        ServerProtocol.player_left(self)

        # Announce player left
        self.factory.send_chat(u"\u00a7e%s has left." % self.display_name)

    def keep_alive(self):
        self.alive_key = random.getrandbits(32)
        self.send_packet("keep_alive", self.buff_type.pack("l", self.alive_key))

    def packet_unhandled(self, buff, name):
        if name == "keep_alive":
            if buff != self.alive_key:
                ServerProtocol.close(self, "Invalid keep-alive packet.")
        else:
            buff.discard()


class MainFactory(ServerFactory):
    protocol = MainProtocol
    motd = "microCraft Server"

    def send_chat(self, message):
        for player in self.players:
            player.send_packet("chat_message", player.buff_type.pack_chat(message) + player.buff_type.pack('B', 0))

    def bees(self):
        for player in self.players:
            player.send_packet("spawn_living_entity",
                               player.buff_type.pack_varint(),     # Entity ID
                               player.buff_type.pack_uuid(),       # Entity UUID
                               player.buff_type.pack_varint(36),   # Entity type
                               player.buff_type.pack_position(0, 5, 0), # Entity XYZ
                               player.buff_type.pack_rotation(0, 0, 0), # TODO
                               )


def main(argv):
    # Parse options
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("-a", "--host", default="", help="address to listen on")
    parser.add_argument("-p", "--port", default=25565, type=int, help="port to listen on")
    args = parser.parse_args(argv)

    # Create factory
    factory = MainFactory()

    # Listen
    factory.listen(args.host, args.port)

    reactor.run()


if __name__ == "__main__":
    import sys
    main(sys.argv[1:])