from sys import argv, stderr
from typing import Final

if len(argv) < 2:
    print(
        "Pass the location of the script to run as a command-line argument.",
        file=stderr,
    )
elif len(argv) > 2:
    print("Unknown command-line arguments passed.", file=stderr)
else:
    bracket_level: int = 0
    code: str = ""
    try:
        with open(argv[1], encoding="utf8") as source:
            for char in source.read():
                if char == "[":
                    bracket_level += 1
                    code += char
                elif char == "]":
                    if bracket_level:
                        bracket_level -= 1
                        code += char
                    else:
                        raise SyntaxError("Unmatched brackets detected.")
                elif char in frozenset("*.<>[]"):
                    code += char
            if bracket_level:
                raise SyntaxError("Unmatched brackets detected.")
    except OSError:
        print("There was an issue accessing the file you requested.", file=stderr)
    except SyntaxError as e:
        print(e, file=stderr)
    else:
        cc: bool = False
        cp: int = 0
        pc: int = 0
        wh: Final[list[int]] = [256]

        while pc != len(code):
            match code[pc]:
                case "<":
                    if cp:
                        cp -= 1
                case ">":
                    cp += 1
                    if cp == len(wh):
                        wh.append(0)
                case "*":
                    if cc:
                        cc = False
                        wh[cp] += 1
                    elif wh[cp]:
                        cc = True
                        wh[cp] -= 1
                case ".":
                    print("" if cp == 13 else chr(wh[cp]), end="")
                case "[":
                    if not cc:
                        bracket_level = 1
                        while bracket_level:
                            pc += 1
                            match code[pc]:
                                case "[":
                                    bracket_level += 1
                                case "]":
                                    bracket_level -= 1
                case "]":
                    bracket_level = -1
                    pc -= 1
                    while bracket_level:
                        match code[pc]:
                            case "[":
                                bracket_level += 1
                            case "]":
                                bracket_level -= 1
                        pc -= 1
            pc += 1
