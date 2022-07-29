# Chess Puzzle

A CLI chess puzzle that pulls data from the chess.com API.

```
$ python3 main.py
Enter moves in UCI format
? for hint
q to exit
! print raw API request (debug)

Mate in 3

8 q . . . n r . k
7 . . . . r p . p
6 . . b . . P p .
5 . . p N n . P .
4 . . . p . R . Q
3 . p P P . . . P
2 . P . . . . B .
1 . R . . . . . K
  a b c d e f g h

>
```

## Installing

```
$ python3 -m virtualenv .venv
$ source .venv/bin/activate
$ pip3 install -r requirements.txt
```
