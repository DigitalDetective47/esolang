from enum import IntEnum
from sys import argv, stderr
from typing import Final


class Direction(IntEnum):
    left = -1
    right = 1


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
                if char == "\u2015":
                    bracket_level += 1
                    code += char
                elif char == "\u23AF":
                    if bracket_level:
                        bracket_level -= 1
                        code += char
                    else:
                        raise SyntaxError("Unmatched looping symbols detected.")
                elif char in frozenset(
                    "-\u2010\u2011\u2012\u2013\u2014\u2043\u2212\u2E3A\u2E3B"
                ):
                    code += char
            if bracket_level:
                raise SyntaxError("Unmatched looping symbols detected.")
    except OSError:
        print("There was an issue accessing the file you requested.", file=stderr)
    except SyntaxError as e:
        print(e, file=stderr)
    else:
        input_text: str = input(
            "Give the program some input. To type multiple lines, end each line except the last with a \\. To type a literal \\, type \\\\ instead.\n"
        )
        while input_text.endswith("\\") and not input_text.endswith("\\\\"):
            input_text = f"{input_text[:-1]}\n{input()}"
        input_buffer: Final[map] = map(ord, input_text.replace("\\\\", "\\"))
        del input_text

        char_id: int
        pc: int = 0
        stack: list[int] = []
        tape: list[int] = [0]
        tape_head: int = 0

        while pc != len(code):
            match code[pc]:
                case "-":
                    stack.append(1)
                case "\u2010":
                    stack.append(next(input_buffer, -1))
                case "\u2011":
                    try:
                        char_id = stack.pop()
                    except IndexError:
                        print(
                            "\n-----\nERROR\n-----\nAttempted to pop from empty stack.",
                            file=stderr,
                        )
                        break
                    try:
                        print(chr(char_id), end="")
                    except ValueError:
                        print(
                            f"\n-----\nERROR\n-----\nAttempted to print character #{char_id} outside legal Unicode range.",
                            file=stderr,
                        )
                        break
                case "\u2012":
                    try:
                        stack.pop()
                    except IndexError:
                        print(
                            "\n-----\nERROR\n-----\nAttempted to pop from empty stack.",
                            file=stderr,
                        )
                        break
                case "\u2013":
                    if tape_head:
                        tape_head -= 1
                    else:
                        tape.insert(0, 0)
                case "\u2014":
                    tape_head += 1
                    if tape_head == len(tape):
                        tape.append(0)
                case "\u2015":
                    try:
                        if not stack.pop():
                            bracket_level = 1
                            while bracket_level:
                                pc += 1
                                match code[pc]:
                                    case "\u2015":
                                        bracket_level += 1
                                    case "\u23AF":
                                        bracket_level -= 1
                    except IndexError:
                        print(
                            "\n-----\nERROR\n-----\nAttempted to pop from empty stack.",
                            file=stderr,
                        )
                        break
                case "\u2043":
                    try:
                        stack.append(stack.pop() + tape[tape_head])
                    except IndexError:
                        print(
                            "\n-----\nERROR\n-----\nAttempted to pop from empty stack.",
                            file=stderr,
                        )
                        break
                case "\u2212":
                    try:
                        stack.append(-stack.pop())
                    except IndexError:
                        print(
                            "\n-----\nERROR\n-----\nAttempted to negate top value of empty stack.",
                            file=stderr,
                        )
                        break
                case "\u23AF":
                    bracket_level = -1
                    pc -= 1
                    while bracket_level:
                        match code[pc]:
                            case "\u2015":
                                bracket_level += 1
                            case "\u23AF":
                                bracket_level -= 1
                        pc -= 1
                case "\u2E3A":
                    try:
                        tape[tape_head] = stack.pop()
                    except IndexError:
                        print(
                            "\n-----\nERROR\n-----\nAttempted to pop from empty stack.",
                            file=stderr,
                        )
                        break
                case "\u2E3B":
                    stack.append(tape[tape_head])
            pc += 1
