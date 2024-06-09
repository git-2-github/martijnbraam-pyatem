from pyatem.command import AuxSourceCommand
from pyatem.field import InputPropertiesField, AuxOutputSourceField


class Routing:
    def __init__(self, connection):
        self.connection = connection
        self.source = {}
        self.output = {}
        self.aux_map = {}

    def reset(self):
        pass

    def add_output(self, output: InputPropertiesField):
        if output.index in self.output:
            return

        self.output[output.index] = output

        self.aux_map = {}
        for i, port in enumerate(sorted(self.output)):
            self.aux_map[port] = i

    def aux_changed(self, aux: AuxOutputSourceField):
        pass

    def port_index_to_aux_index(self, port):
        return self.aux_map[port]

    def aux_index_to_port_index(self, aux):
        for a in self.aux_map:
            if self.aux_map[a] == aux:
                return a

    def change(self, destination, source):
        aux_idx = self.aux_map[destination]
        cmd = AuxSourceCommand(aux_idx, source=source)
        self.connection.mixer.send_commands([cmd])
