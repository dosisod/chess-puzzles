from dataclasses import dataclass, field
from typing import Callable
import io
import json

import chess.pgn
import requests

WHITE_TILE_COLOR = 0x00597a
BLACK_TILE_COLOR = 0x383838
WHITE_PIECE_COLOR = 0x318eaf
BLACK_PIECE_COLOR = 0x1e1e1e
BORDER = BLACK_PIECE_COLOR

BLACK_COLOR_FG = "\x1b[30m"
RESET = "\x1b[0m"
LEFT_HALF_BLOCK = "\u258c"


@dataclass
class Color:
    color: int

    def as_foreground(self):
        return hex_to_color(self.color, True)

    def as_background(self):
        return hex_to_color(self.color, False)


@dataclass
class FlippableColor(Color):
    flip: Callable[[], "FlippableColor"] = field(init=False)

    @classmethod
    def make(cls, colors):
        first = FlippableColor(colors[0])
        second = FlippableColor(colors[1])

        first.flip = lambda: second
        second.flip = lambda: first

        return first


@dataclass
class ColorConfig:
    tile: FlippableColor
    piece: FlippableColor
    border: Color


COLORS = ColorConfig(
    tile=FlippableColor.make([WHITE_TILE_COLOR, BLACK_TILE_COLOR]),
    piece=FlippableColor.make([WHITE_PIECE_COLOR, BLACK_PIECE_COLOR]),
    border=Color(BORDER),
)


def get_tile_color(x, y):
    color = COLORS.tile

    if is_white_tile(x, y):
        return color

    return color.flip()


def get_piece_color(c):
    color = COLORS.piece

    if is_white_piece(c):
        return color

    return color.flip()


def hex_to_rgb(color):
    return (
        color >> 16,
        (color & 0xFF00) >> 8,
        color & 0xFF,
    )


def hex_to_color(color: int, is_fg: bool) -> str:
    r, g, b = hex_to_rgb(color)
    code = 38 if is_fg else 48

    return f"\x1b[{code};2;{r};{g};{b}m"


def is_white_tile(x, y):
    return (y + x) % 2 == 0


def is_white_piece(c):
    return c.isupper()


def colorize_half_block(lhs: Color, rhs: Color):
    return (
        lhs.as_foreground() +
        rhs.as_background() +
        LEFT_HALF_BLOCK
    )


def colorize_tile(x, y, c):
    tile_color = get_tile_color(x, y)

    lhs_block = colorize_half_block(
        COLORS.border if x == 0 else tile_color.flip(),
        tile_color,
    )

    rhs_block = (
        colorize_half_block(tile_color, COLORS.border)
        if x == 7
        else ""
    )

    return (
        lhs_block +
        tile_color.as_background() +
        get_piece_color(c).as_foreground() +
        c.replace(".", " ") +
        rhs_block +
        RESET
    )

def print_board(board):
    board = str(board)
    border_colors = (
        COLORS.piece.as_foreground() + COLORS.border.as_background()
    )

    row_header = f"{border_colors}  a b c d e f g h  {RESET}\n"
    out = row_header

    for y, row in enumerate(board.splitlines()):
        tmp = ""

        for x, col in enumerate(row.split()):
            tmp += colorize_tile(x, y, col)

        num = 8 - y
        out += f"{border_colors}{num}{tmp}{border_colors}{num}{RESET}\n"

    out += row_header

    print(out)


print("""\
Enter moves in UCI format
? for hint
q to exit
! print raw API request (debug)
""")

puzzle = requests.get("https://api.chess.com/pub/puzzle/random").json()
title = puzzle["title"]
pgn = puzzle["pgn"]

game = chess.pgn.read_game(io.StringIO(pgn))
assert game, "Could not load game"

board = game.board()

moves = iter(game.mainline_moves())
move = next(moves)

print(f"{title}\n")
print_board(board)

while True:
    guess = input("> ")

    if guess == "q":
        break

    if guess == "?":
        print(f"Hint: {move.uci()}")

    elif guess == "!":
        print(json.dumps(puzzle))

    elif guess == move.uci():
        board.push_san(guess)
        next_move = next(moves, None)

        print("Correct!\n")
        print_board(board)

        if not next_move:
            input("You won! ")
            break

        board.push_san(next_move.uci())
        move = next(moves)

        print(f"Black plays {next_move.uci()}")
        input("OK ")

        print_board(board)

    else:
        print("Incorrect")
