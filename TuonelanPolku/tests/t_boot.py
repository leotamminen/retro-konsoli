from lib import *
g = new_game()
pad = ScriptPad("t1"); g.add_pad(pad)
step(g, 10)
print("state", g.state_name, "status", g.title_status)
setlang("en"); step(g, 3)
for k in range(4): step(g, 2)
print("OK boot")
