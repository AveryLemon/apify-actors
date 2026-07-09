with open('/Users/averylemonflower/Desktop/Apify-Actors/HANDOFF.md') as f:
    lines = f.readlines()

# Lines 19, 20, 21 (0-indexed: 18, 19, 20) need fixing
# First, fix lines 17 (RAM) and 18 (Disk) - they have extra pipe
# Actually looking at context display, they show || not ||| 
# Let's just fix lines 19 and 21

# Line 19 (0-indexed 18): corrupted swap+cycles merge
# Split it into two lines
lines[18] = '| Swap | 1729.56Mi/3072Mi used (56.3%) -- encrypted '
lines[18] += '| '
lines[18] += 'Improved from 92.5% -- swap does NOT drain automatically (requires restart or pressure) |\n'

# Line 20 (0-indexed 19) originally blank between tables - let me check what's actually there
# Line 20: the consecutive cycles line needs to be a new line
# Let me insert new line 19 for cycles
cycles_line = '| Consecutive cycles | **72** (blue ocean uncontested -- RAM '
cycles_line += '89%, no tickets remain) | RAM at 89% -- healthy baseline, no active blockers |\n'

# Insert cycles line and blank line after swap
lines.insert(19, '\n')
lines.insert(19, cycles_line)

# Line 21 (now 0-indexed 21 after insert): fix competitive watch
old_siphon = 'siphon: primary query timed out, retry succeeded -- no competitors found'
new_siphon = 'siphon: no new competitors found'
if old_siphon in lines[21]:
    lines[21] = lines[21].replace(old_siphon, new_siphon)

# Also change the arrow symbol
lines[21] = lines[21].replace(' ', ' ')

with open('/Users/averylemonflower/Desktop/Apify-Actors/HANDOFF.md', 'w') as f:
    f.writelines(lines)

print('Fixed')
with open('/Users/averylemonflower/Desktop/Apify-Actors/HANDOFF.md') as f:
    for i, line in enumerate(f.readlines()):
        if any(x in line for x in ['RAM on MacBook', 'Disk |', 'Swap |', 'Consecutive cycles', 'Competitive watch']):
            print(f'L{i+1}: {line.rstrip()}')
