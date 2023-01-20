"""
Generate a wireshark dissector based on the protocol information in the pyatem module
Based on the atem_dissector.lua wireshark plugin from https://github.com/peschuster/wireshark-atem-dissector
"""
import os
import pyatem.protocol
import pyatem.field


def make_pf_fields():
    result = "local pf_fields = {}\nlocal VALS = {}\n"
    for name, cls in pyatem.field.__dict__.items():
        if not name.endswith('Field'):
            continue
        cmd = cls.CODE

        in_field_table = False
        parsed_field_table = False
        has_header = False
        for line in cls.__doc__.splitlines(keepends=False):
            line = line.strip()
            if not in_field_table and not parsed_field_table and line.startswith("======"):
                in_field_table = True
                has_header = False
                continue
            if in_field_table and not has_header and line.startswith("======"):
                has_header = True
                continue
            if in_field_table and has_header and line.startswith("======"):
                in_field_table = False
                parsed_field_table = True
                continue
            if in_field_table and has_header:
                part = line.split(maxsplit=3)
                if len(part) < 3:
                    continue
                if not part[0].isnumeric():
                    continue
                offset = int(part[0])
                size = int(part[1]) if part[1].isnumeric() else 0
                dtype = part[2]
                label = part[3]

                code = label.split('[')[0].split('(')[0].split(',')[0].strip()
                code = code.lower().replace(" ", "_").replace('m/e', 'me').replace('?', '')
                ftype = "ftypes.STRING"
                valuestring = "nil"
                base = "base.NONE"
                if dtype == "u8":
                    ftype = "ftypes.UINT8"
                    base = "base.DEC"
                elif dtype == "u16":
                    ftype = "ftypes.UINT16"
                    base = "base.DEC"
                elif dtype == "u32":
                    ftype = "ftypes.UINT32"
                    base = "base.DEC"
                elif dtype == "i8":
                    ftype = "ftypes.INT8"
                    base = "base.DEC"
                elif dtype == "i16":
                    ftype = "ftypes.INT16"
                    base = "base.DEC"
                elif dtype == "i32":
                    ftype = "ftypes.INT32"
                    base = "base.DEC"
                elif dtype == "bool":
                    ftype = "base.UINT8"
                    base = "base.HEX"

                if 'mask' in label.lower() and base == "base.DEC":
                    base = "base.HEX"

                result += f'pf_fields["pf_cmd_{cmd}_{code}"] = ProtoField.new ("{label}", "atem.cmd.{cmd}.{code}", {ftype}, {valuestring}, {base})\n'
        result += "\n"
    return result


def make_cmd_labels():
    result = "local cmd_labels = {}\n"
    for label in pyatem.protocol.AtemProtocol.FIELDNAME_PRETTY:
        pretty = pyatem.protocol.AtemProtocol.FIELDNAME_PRETTY[label]
        result += f'cmd_labels["{label}"] = "{pretty}"\n'
    return result


def main():
    template_path = os.path.join(os.path.dirname(__file__), 'atem_dissector.tpl')
    with open(template_path) as handle:
        template = handle.read()

    fields = make_pf_fields()
    fields += make_cmd_labels()

    template = template.replace('@@FIELDS', fields)
    template = template.replace('@@REGS', '')
    template = template.replace('@@CMDS', '')
    print(template)


if __name__ == '__main__':
    main()
