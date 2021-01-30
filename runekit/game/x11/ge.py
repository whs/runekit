import xcffib

opcode_cache = {}


def get_extension_by_opcode(connection, opcode):
    if opcode in opcode_cache:
        return opcode_cache[opcode]

    for name in connection.core.ListExtensions().reply().names:
        ext_opcode = (
            connection.core.QueryExtension(name.name_len, name.name)
            .reply()
            .major_opcode
        )
        opcode_cache[ext_opcode] = xcffib.ExtensionKey(name.name.to_string())

    try:
        return opcode_cache[opcode]
    except KeyError:
        raise ExtensionNotFound(opcode)


class ExtensionNotFound(Exception):
    def __init__(self, opcode):
        self.opcode = opcode
        super().__init__(f"Extension with opcode {opcode} was not found")


class GeGenericEvent(xcffib.Event):
    def __init__(self, unpacker):
        if isinstance(unpacker, xcffib.Protobj):
            unpacker = xcffib.MemoryUnpacker(unpacker.pack())

        super().__init__(unpacker)
        try:
            base = unpacker.offset
            (
                self.extension,
                self.sequence_number,
                self.length,
                self.evtype,
            ) = unpacker.unpack("xBHIH")
            self.payload = xcffib.List(unpacker, "I", 8 + self.length)
            self.bufsize = unpacker.offset - base
        except:
            import traceback

            traceback.print_exc()
            raise

    def to_event(self, connection):
        extension = get_extension_by_opcode(connection, self.extension)

        constructor = xcffib.extensions[extension][1][self.evtype]
        unpacker = xcffib.MemoryUnpacker(self.payload.buf())
        try:
            return constructor(unpacker)
        except:
            import traceback

            traceback.print_exc()
            raise


xcffib.core_events[35] = GeGenericEvent
