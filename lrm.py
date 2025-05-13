from enum import IntEnum
from sys import argv, stderr
from typing import Final

CHARSET: Final[
    str
] = "\n ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789!\"£$%^&*(){}[]-=_+;'#~@:,./?><\\|`\t"
ILLEGAL_CHARACTER_INDICES: Final[frozenset[int]] = frozenset({98, 99})


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
    try:
        with open(argv[1]) as source:
            field: list[str] = list(source.readline())
    except OSError:
        print("There was an issue accessing the file you requested.", file=stderr)
    else:
        a: int = 0
        command: str
        f: int
        f_slice: slice
        pointer_direction: Direction = Direction.right
        pointer_location: int = 0
        input_text: str = input(
            "Give the program some input. To type multiple lines, end each line except the last with a \\. To type a literal \\, type \\\\ instead.\n"
        )
        while input_text.endswith("\\") and not input_text.endswith("\\\\"):
            input_text = f"{input_text[:-1]}\n{input()}"
        try:
            input_buffer: map = map(
                CHARSET.index, input_text.replace("\\\\", "\\")
            )
        except ValueError:
            print("Illegal character in input stream.", file=stderr)
        else:
            while 0 <= pointer_location < len(field):
                command = field[pointer_location]
                if not command.isdigit():
                    match pointer_direction:
                        case Direction.left:
                            f_slice = slice(pointer_location - 2, pointer_location)
                        case Direction.right:
                            f_slice = slice(pointer_location + 1, pointer_location + 3)
                    try:
                        f = int("".join(field[f_slice]))
                    except (IndexError, ValueError):
                        print(
                            f"\n-----\nERROR\n-----\n{''.join(field)}\n{' ' * pointer_location}^\nAttempted to run command with invalid number while moving {pointer_direction.name}.\nA = {str(a).zfill(2)}",
                            file=stderr,
                        )
                        break
                    match command:
                        case "a":
                            a += f
                        case "b":
                            if a != 0:
                                pointer_location += f * pointer_direction
                        case "c":
                            a = f
                        case "d":
                            try:
                                a //= f
                            except ZeroDivisionError:
                                print(
                                    f"\n-----\nERROR\n-----\n{''.join(field)}\n{' ' * pointer_location}^\nAttempted to divide by zero while moving {pointer_direction.name}.\nA = {str(a).zfill(2)}",
                                    file=stderr,
                                )
                                break
                        case "e":
                            if a in ILLEGAL_CHARACTER_INDICES:
                                print(
                                    f"\n-----\nERROR\n-----\n{''.join(field)}\n{' ' * pointer_location}^\nAttempted to extend program with invalid character while moving {pointer_direction.name}.\nA = {str(a).zfill(2)}",
                                    file=stderr,
                                )
                                break
                            else:
                                match pointer_direction:
                                    case Direction.left:
                                        field.insert(
                                            max(pointer_location - f, 0), CHARSET[a]
                                        )
                                        pointer_location += 1
                                    case Direction.right:
                                        field.insert(
                                            min(pointer_location + f + 1, len(field)),
                                            CHARSET[a],
                                        )
                        case "i":
                            a = next(input_buffer, 99)
                        case "j":
                            pointer_location += f * pointer_direction
                        case "l":
                            pointer_direction = Direction.left
                        case "m":
                            a *= f
                        case "p":
                            if a in ILLEGAL_CHARACTER_INDICES:
                                print(
                                    f"\n-----\nERROR\n-----\n{''.join(field)}\n{' ' * pointer_location}^\nAttemted to print invalid character while moving {pointer_direction.name}.\nA = {str(a).zfill(2)}",
                                    file=stderr,
                                )
                                break
                            else:
                                print(CHARSET[a], end="")
                        case "r":
                            pointer_direction = Direction.right
                        case "s":
                            a -= f
                        case "w":
                            field[f_slice] = list(str(a).zfill(2))
                        case _:
                            print(
                                f"\n-----\nERROR\n-----\n{''.join(field)}\n{' ' * pointer_location}^\nAttempted to run invalid command while moving {pointer_direction.name}.\nA = {str(a).zfill(2)}",
                                file=stderr,
                            )
                    a %= 100
                pointer_location += pointer_direction
