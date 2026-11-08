#!/bin/bash
# Builds the single file and runs the whole headless suite. Run from anywhere.
cd "$(dirname "$0")/.." || exit 1
python3 build.py >/dev/null || exit 1
fail=0
for t in "t_boot.py" "t_ui.py" "t_text.py" "t_world.py --secrets" "t_world.py --secrets --nodj" "t_save.py" "t_map.py" "t_newgame.py" "t_music.py" "t_pads.py" "t_spawn.py" "t_coop.py" "t_perf.py" "t_fuzz.py 1" "t_fuzz.py 2" "t_louhi.py" "t_perf_v12.py" "t_boss.py" "t_vellamo.py" "v13_input.py" "v13_gate_bog.py" "v131_visual.py" "v132_regressions.py"; do
  echo "== $t"; python3 tests/$t 2>&1 | grep -v "^pygame\|^Hello" | tail -12; [ "${PIPESTATUS[0]}" -eq 0 ] || { echo "FAILED: $t"; fail=1; }
done
exit $fail
