#!/usr/bin/env python3
"""
Determinant Tic-Tac-Toe -- exhaustive check of the danger-score strategy.

Player 1 writes 1s, Player 0 writes 0s, Player 1 moves first, 5 ones + 4 zeros.
Player 0 wins if det = 0.

Each cell lies on exactly one positive Sarrus diagonal (a, b, c) and one
negative Sarrus diagonal (d, e, f), so each cell is a "pair" of letters:

        ae  bf  cd
        cf  ad  be
        bd  ce  af

Danger score = for every ALIVE letter (no 0 on that diagonal yet), the number
of Player 1's pairs containing it, summed.  Dead letters count 0.

Player 0's strategy: after each of Player 0's moves, keep the danger score <= 1.

What this program checks, for EVERY possible sequence of Player 1 moves:
  * Player 0 always has a move that brings the score back to <= 1
  * no letter ever reaches 3 Player 1 pairs (no full diagonal of 1s)
  * at the end all six letters are dead
  * the final determinant is 0

With --all-p0 it also branches over EVERY Player 0 move that keeps the score
<= 1 (not just the first one found), so any tie-break is verified too.

Usage:
  python3 det_tictactoe.py                  # exhaustive check, summary only
  python3 det_tictactoe.py --all-p0         # also branch over every valid P0 move
  python3 det_tictactoe.py --show 1         # full log of game #1 (of the exhaustive run)
  python3 det_tictactoe.py --show-all       # full log of every game (long!)
  python3 det_tictactoe.py --moves ad,bf,cf,cd,be   # log a specific Player 1 line
  python3 det_tictactoe.py --random 3       # logs of 3 random games
"""

import argparse
import random
import sys

# ----------------------------------------------------------------- the board
CELL_PAIRS = [
    ["ae", "bf", "cd"],
    ["cf", "ad", "be"],
    ["bd", "ce", "af"],
]
CELL_NAMES = [
    ["top-left", "top-middle", "top-right"],
    ["middle-left", "center", "middle-right"],
    ["bottom-left", "bottom-middle", "bottom-right"],
]
POS, NEG = "abc", "def"
LETTERS = POS + NEG
PAIRS = [p for row in CELL_PAIRS for p in row]          # 9 pairs, row by row
CELL_OF = {CELL_PAIRS[r][c]: (r, c) for r in range(3) for c in range(3)}


def sanity_check_labels():
    """Recompute the pair table straight from Sarrus's diagonals."""
    diag = {  # cells (row, col) on each Sarrus diagonal
        "a": [(0, 0), (1, 1), (2, 2)],
        "b": [(0, 1), (1, 2), (2, 0)],
        "c": [(0, 2), (1, 0), (2, 1)],
        "d": [(2, 0), (1, 1), (0, 2)],
        "e": [(2, 1), (1, 2), (0, 0)],
        "f": [(2, 2), (1, 0), (0, 1)],
    }
    for r in range(3):
        for c in range(3):
            on = "".join(x for x in LETTERS if (r, c) in diag[x])
            assert on == CELL_PAIRS[r][c], (r, c, on)
    assert sorted(PAIRS) == sorted(p + n for p in POS for n in NEG)


# ----------------------------------------------------------- game utilities
def det3(m):
    return (m[0][0] * (m[1][1] * m[2][2] - m[1][2] * m[2][1])
            - m[0][1] * (m[1][0] * m[2][2] - m[1][2] * m[2][0])
            + m[0][2] * (m[1][0] * m[2][1] - m[1][1] * m[2][0]))


def dead_letters(p0_pairs):
    return set("".join(p0_pairs))


def counts(p1_pairs, p0_pairs):
    """Danger count per alive letter."""
    dead = dead_letters(p0_pairs)
    return {x: sum(x in p for p in p1_pairs) for x in LETTERS if x not in dead}


def danger_score(p1_pairs, p0_pairs):
    return sum(counts(p1_pairs, p0_pairs).values())


def free_pairs(p1_pairs, p0_pairs):
    return [p for p in PAIRS if p not in p1_pairs and p not in p0_pairs]


def good_p0_moves(p1_pairs, p0_pairs):
    """Every free pair that leaves the danger score <= 1."""
    return [p for p in free_pairs(p1_pairs, p0_pairs)
            if danger_score(p1_pairs, p0_pairs + [p]) <= 1]


def board_matrix(p1_pairs, p0_pairs):
    m = [[None] * 3 for _ in range(3)]
    for p in p1_pairs:
        r, c = CELL_OF[p]; m[r][c] = 1
    for p in p0_pairs:
        r, c = CELL_OF[p]; m[r][c] = 0
    return m


# --------------------------------------------------------------- pretty log
def fmt_board(p1_pairs, p0_pairs, last=None):
    m = board_matrix(p1_pairs, p0_pairs)
    lines = []
    for r in range(3):
        cells = []
        for c in range(3):
            v = m[r][c]
            s = "." if v is None else str(v)
            if last is not None and CELL_OF[last] == (r, c):
                s = f"[{s}]"
            else:
                s = f" {s} "
            cells.append(s)
        pair_row = "  ".join(CELL_PAIRS[r])
        lines.append("      | " + " ".join(cells) + " |      " + pair_row)
    return "\n".join(lines)


def fmt_counts(p1_pairs, p0_pairs):
    cs = counts(p1_pairs, p0_pairs)
    shown = [f"{x}:{n}" for x, n in cs.items() if n > 0]
    return ", ".join(shown) if shown else "-"


def log_game(game, out=sys.stdout):
    """game = list of (player, pair) in order."""
    p1, p0 = [], []
    out.write("      board (latest move in [ ])      pair labels\n")
    out.write(fmt_board(p1, p0) + "\n")
    out.write("      danger score: 0\n\n")
    for i, (who, pair) in enumerate(game, 1):
        (p1 if who == 1 else p0).append(pair)
        r, c = CELL_OF[pair]
        score = danger_score(p1, p0)
        dead = "".join(sorted(dead_letters(p0))) or "none"
        tag = ""
        if who == 0:
            tag = "  OK (<= 1)" if score <= 1 else "  RULE BROKEN"
        out.write(f"Move {i}: Player {who} takes {pair} ({CELL_NAMES[r][c]}) "
                  f"-> writes {who}\n")
        out.write(fmt_board(p1, p0, last=pair) + "\n")
        out.write(f"      dead letters: {dead}   counts: {fmt_counts(p1, p0)}"
                  f"   danger score: {score}{tag}\n\n")
    m = board_matrix(p1, p0)
    d = det3(m)
    out.write(f"Final: dead letters = {''.join(sorted(dead_letters(p0)))}, "
              f"det = {d}  ->  {'Player 0 wins' if d == 0 else 'Player 1 wins'}\n")


# ------------------------------------------------------------ exhaustive run
class Stats:
    def __init__(self):
        self.games = 0
        self.p0_decisions = 0
        self.max_score_before_p0 = 0
        self.max_p1_on_alive_letter = 0
        self.failures = []
        self.det_values = {}


def play_all(all_p0, record=None):
    """Depth-first search over every Player 1 move (and every valid P0 move
    if all_p0).  Returns Stats; optionally records every finished game."""
    st = Stats()

    def check_final(p1, p0, game):
        st.games += 1
        m = board_matrix(p1, p0)
        d = det3(m)
        st.det_values[d] = st.det_values.get(d, 0) + 1
        ones = sum(v == 1 for row in m for v in row)
        if ones != 5 or len(dead_letters(p0)) != 6 or d != 0:
            st.failures.append(("bad final position", list(game)))
        if record is not None:
            record.append(list(game))

    def p1_turn(p1, p0, game):
        free = free_pairs(p1, p0)
        if not free:
            check_final(p1, p0, game)
            return
        for pair in free:
            p1.append(pair); game.append((1, pair))
            # no alive letter may reach 3 Player 1 pairs
            worst = max(counts(p1, p0).values(), default=0)
            st.max_p1_on_alive_letter = max(st.max_p1_on_alive_letter, worst)
            if worst >= 3:
                st.failures.append(("Player 1 completed a diagonal", list(game)))
            elif not free_pairs(p1, p0):
                check_final(p1, p0, game)
            else:
                p0_turn(p1, p0, game)
            p1.pop(); game.pop()

    def p0_turn(p1, p0, game):
        st.p0_decisions += 1
        st.max_score_before_p0 = max(st.max_score_before_p0,
                                     danger_score(p1, p0))
        options = good_p0_moves(p1, p0)
        if not options:
            st.failures.append(("no move keeps score <= 1", list(game)))
            return
        for pair in (options if all_p0 else options[:1]):
            p0.append(pair); game.append((0, pair))
            p1_turn(p1, p0, game)
            p0.pop(); game.pop()

    p1_turn([], [], [])
    return st


def play_line(p1_moves):
    """Play a given list of Player 1 pairs against the strategy."""
    p1, p0, game = [], [], []
    for pair in p1_moves:
        if pair not in free_pairs(p1, p0):
            sys.exit(f"Pair {pair!r} is not free at that point.")
        p1.append(pair); game.append((1, pair))
        if not free_pairs(p1, p0):
            break
        options = good_p0_moves(p1, p0)
        if not options:
            sys.exit("Strategy failed: no move keeps the score <= 1.")
        p0.append(options[0]); game.append((0, options[0]))
    if free_pairs(p1, p0):
        sys.exit("Give all 5 of Player 1's moves (e.g. ad,bf,cf,cd,be).")
    return game


# ---------------------------------------------------------------------- main
def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--all-p0", action="store_true",
                    help="branch over every Player 0 move that keeps score <= 1")
    ap.add_argument("--show", type=int, metavar="N",
                    help="print the full log of game number N")
    ap.add_argument("--show-all", action="store_true",
                    help="print the full log of every game")
    ap.add_argument("--moves", metavar="P1,P1,...",
                    help="log one game for a given sequence of Player 1 pairs")
    ap.add_argument("--random", type=int, metavar="K",
                    help="print logs of K random games")
    args = ap.parse_args()

    sanity_check_labels()

    if args.moves:
        log_game(play_line([m.strip() for m in args.moves.split(",")]))
        return

    games = []
    st = play_all(args.all_p0, record=games)

    if args.show is not None:
        if not 1 <= args.show <= len(games):
            sys.exit(f"Game number must be between 1 and {len(games)}.")
        print(f"=== Game {args.show} of {len(games)} ===\n")
        log_game(games[args.show - 1])
        return
    if args.show_all:
        for i, g in enumerate(games, 1):
            print(f"=== Game {i} of {len(games)} ===\n")
            log_game(g)
            print()
    if args.random:
        for g in random.sample(games, min(args.random, len(games))):
            print(f"=== Game {games.index(g) + 1} of {len(games)} ===\n")
            log_game(g)
            print()

    mode = "every valid Player 0 move" if args.all_p0 else "first valid Player 0 move"
    print("=" * 62)
    print("EXHAUSTIVE CHECK")
    print("=" * 62)
    print(f"Player 1:                 every possible move, every turn")
    print(f"Player 0:                 {mode}")
    print(f"Complete games played:    {st.games}")
    print(f"Player 0 decisions made:  {st.p0_decisions}")
    print(f"Highest score P0 faced:   {st.max_score_before_p0}  (proof says <= 3)")
    print(f"Most P1 pairs on an alive letter, ever: "
          f"{st.max_p1_on_alive_letter}  (3 would be a full diagonal)")
    print(f"Final determinants seen:  {dict(sorted(st.det_values.items()))}")
    if st.failures:
        print(f"\nFAILURES: {len(st.failures)}")
        for why, g in st.failures[:5]:
            print(" ", why, g)
        sys.exit(1)
    print("\nResult: in every game the danger score was brought back to <= 1")
    print("after each Player 0 move, all six letters died, and det = 0.")
    print("Player 0 wins every time.")


if __name__ == "__main__":
    main()
