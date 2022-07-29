import io
import json

import chess.pgn
import requests


def print_board(board):
    board = str(board)
    out = ""

    for i, row in enumerate(board.splitlines()):
        out += f"{8 - i} {row}\n"

    out += "  a b c d e f g h\n"

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
