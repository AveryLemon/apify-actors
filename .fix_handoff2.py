with open('/Users/averylemonflower/Desktop/Apify-Actors/HANDOFF.md') as f:
    lines = f.readlines()

fixes = 0
for i, line in enumerate(lines):
    # Fix triple-pipe on RAM line
    if 'RAM on MacBook' in line and line.startswith('|||'):
        lines[i] = '|| RAM on MacBook | 89% free | '
        fixes += 1
    
    # Fix triple-pipe on Disk line
    if 'Disk | 104Gi' in line and line.startswith('|||'):
        lines[i] = '|| Disk | 104Gi available | Healthy |'
        fixes += 1
    
    # Fix swap value - replace whole line
    if 'Swap |' in line and '17.1Gi' in line:
        lines[i] = '| Swap | 1729.56Mi/3072Mi used (56.3%) -- encrypted '
        fixes += 1
    
    # Fix swap status
    if 'Still critically high' in line:
        lines[i] = lines[i].replace('Still critically high', 'Improved from 92.5%')
        fixes += 1
    
    # Fix cycles counter **71**
    if 'Consecutive cycles' in line and '**71**' in line:
        lines[i] = lines[i].replace('**71**', '**72**')
        fixes += 1
    
    # Fix cycles RAM reference
    if 'RAM at 44%' in line:
        lines[i] = lines[i].replace('RAM at 44%', 'RAM at 89%')
        fixes += 1
    
    # Fix competitive watch cycle counter
    if '71st cycle' in line:
        lines[i] = lines[i].replace('71st cycle', '72nd cycle')
        fixes += 1
    
    # Fix watch siphon result text
    if 'siphon: primary query timed out' in line:
        lines[i] = lines[i].replace('siphon: primary query timed out, retry succeeded -- no competitors found', 'siphon: no new competitors found')
        fixes += 1

with open('/Users/averylemonflower/Desktop/Apify-Actors/HANDOFF.md', 'w') as f:
    f.writelines(lines)

print(f'{fixes} fixes applied')

# Verify key lines
with open('/Users/averylemonflower/Desktop/Apify-Actors/HANDOFF.md') as f:
    for i, line in enumerate(f.readlines()):
        if any(x in line for x in ['RAM on MacBook', 'Disk |', 'Swap |', 'Consecutive', 'Competitive watch']):
            print(f'L{i+1}: {line.rstrip()}')
