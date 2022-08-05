from dataclasses import dataclass, field
from typing import Callable
import io
import json

import chess
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
RIGHT_HALF_BLOCK = "\u2590"


def get_player_color(board: chess.Board) -> str:
    return "white" if board.turn == chess.WHITE else "black"


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


def colorize_half_block(lhs: Color | None, rhs: Color | None):
    if not lhs:
        return (rhs.as_foreground() if rhs else "") + RIGHT_HALF_BLOCK

    return (
        (lhs.as_foreground() if lhs else "") +
        (rhs.as_background() if rhs else "") +
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

    border_lhs_tile = colorize_half_block(None, COLORS.border)
    border_rhs_tile = RESET + colorize_half_block(COLORS.border, None)

    def add_end_caps(line: str) -> str:
        return f"{border_lhs_tile}{border_colors}{line}{border_rhs_tile}{RESET}\n"

    out = row_header = add_end_caps("  a b c d e f g h  ")

    for y, row in enumerate(board.splitlines()):
        tmp = ""

        for x, col in enumerate(row.split()):
            tmp += colorize_tile(x, y, col)

        num = 8 - y
        out += add_end_caps(f"{num}{tmp}{border_colors}{num}")

    out += row_header

    print(out)


print("""\
Enter moves in UCI format
? for hint
q to exit
""")

puzzle = requests.get("https://api.chess.com/pub/puzzle/random").json()
title = puzzle["title"]
pgn = puzzle["pgn"]

game = chess.pgn.read_game(io.StringIO(pgn))
assert game, "Could not load game"

board = game.board()

moves = iter(game.mainline_moves())
move = next(moves)

print(f'"{title}"\n')
print(f"You are playing as {get_player_color(board)}\n")

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
        move = next(moves, None)

        print("Correct!\n")
        print_board(board)

        if not move:
            input("You won! ")
            break

        print(f"{get_player_color(board).title()} plays {move.uci()}")

        board.push_san(move.uci())
        move = next(moves)

        input("OK ")
        print()

        print_board(board)

    else:
        print("Incorrect")
