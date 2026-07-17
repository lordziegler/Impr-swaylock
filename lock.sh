#!/bin/bash
# imperator-swaylock launch script
# Generates a lockscreen image with clock and calls swaylock.
# Extra args are forwarded to swaylock (e.g. -f to daemonize, as swayidle needs).

SCRIPT_DIR="$(dirname "$(realpath "$0")")"
LOCK_IMG="/tmp/imperator-lock.png"

# Override with IMPERATOR_LOCK_SIZE=2560x1440 in environment if needed
SIZE="${IMPERATOR_LOCK_SIZE:-1920x1080}"
W="${SIZE%x*}"
H="${SIZE#*x}"

# The clock slot is the output center — swaylock-effects' own default indicator
# position — so no --indicator-x/y-position override is passed (those are treated
# as offsets-from-center by swaylock-effects and would push the clock off-slot).
# Only the font size is scaled to the resolution.
FS=$(( 54 * H / 1080 ))
POS=(--font-size "$FS")

python3 "$SCRIPT_DIR/wallpaper.py" --lock --out "$LOCK_IMG" --size "$SIZE"

# With -f/-F swaylock daemonizes and returns at once, so deleting the image here
# would race its load — keep it (it lives in /tmp, overwritten every lock). When
# not forking, swaylock blocks until unlock and the temp file is cleaned up.
case " $* " in
    *" -f "*|*" -F "*) swaylock --image "$LOCK_IMG" --scaling fill "${POS[@]}" "$@" ;;
    *) swaylock --image "$LOCK_IMG" --scaling fill "${POS[@]}" "$@"; rm -f "$LOCK_IMG" ;;
esac
