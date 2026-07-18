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

# The clock/ring indicator is centered by swaylock-effects' own default, so no
# --indicator-x/y-position override is passed (those are offsets-from-center and
# would push it off-slot). Clock font, ring radius and thickness scale with the
# resolution to match the baked panel (which is drawn relative to H/1080).
FS=$(( 46 * H / 1080 ))
R=$(( 145 * H / 1080 ))
TH=$(( 5 * H / 1080 ))
[ "$TH" -lt 2 ] && TH=2
POS=(--font-size "$FS" --indicator-radius "$R" --indicator-thickness "$TH")

python3 "$SCRIPT_DIR/wallpaper.py" --lock --out "$LOCK_IMG" --size "$SIZE"

# With -f/-F swaylock daemonizes and returns at once, so deleting the image here
# would race its load — keep it (it lives in /tmp, overwritten every lock). When
# not forking, swaylock blocks until unlock and the temp file is cleaned up.
case " $* " in
    *" -f "*|*" -F "*) swaylock --image "$LOCK_IMG" --scaling fill "${POS[@]}" "$@" ;;
    *) swaylock --image "$LOCK_IMG" --scaling fill "${POS[@]}" "$@"; rm -f "$LOCK_IMG" ;;
esac
