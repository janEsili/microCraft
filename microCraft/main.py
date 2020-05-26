import random

from quarry.net.server import ServerProtocol, ServerFactory
from twisted.internet import reactor

from microCraft.packethandler import packet_dictionary


class MainProtocol(ServerProtocol):

    random.seed()
    alive_key = 0

    def player_joined(self):
        ServerProtocol.player_joined(self)

        # Send "Join Game" packet
        self.send_packet("join_game",
                         self.buff_type.pack("iBilB",
                                             0,  # entity id
                                             3,  # game mode
                                             0,  # dimension
                                             0,  # hashed seed
                                             0),  # max players
                         self.buff_type.pack_string("flat"),  # level type
                         self.buff_type.pack_varint(1),  # view distance
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
        self.ticker.add_loop(20, self.send_packet("keep_alive", self.keep_alive))

        # Announce player joined
        self.factory.send_chat(u"\u00a7e%s has joined." % self.display_name)

        def player_left(self):
            ServerProtocol.player_left(self)

            # Announce player left
            self.factory.send_chat(u"\u00a7e%s has left." % self.display_name)

        def keep_alive(self):
            alive_key = random.getrandbits(32)
            self.buff_type.pack("l", alive_key)

        def packet_unhandled(self, buff, name):
            packet_dictionary.get(name, ServerProtocol.packet_unhandled(self, buff, name))(self, buff, alive_key)




class MainFactory(ServerFactory):
    protocol = MainProtocol
