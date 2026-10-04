"""Measure actual ROM jump arcs through A/Up input for cat, dog and ghost."""
from pathlib import Path
from pyboy import PyBoy

symbols={}
for line in Path('build/cactus-cat.noi').read_text().splitlines():
    parts=line.split()
    if len(parts)==3 and parts[0]=='DEF': symbols[parts[1]]=int(parts[2],16)
p=PyBoy('build/cactus-cat.gbc',window='null',sound_emulated=False)
p.set_emulation_speed(0)
def get(name,size=1):
    return sum(p.memory[symbols['_'+name]+i] << (8*i) for i in range(size))
def put(name,n,size=1):
    for i in range(size): p.memory[symbols['_'+name]+i]=(n >> (8*i)) & 255
def arc(button,hold,repress=False):
    p.button_release('a'); p.button_release('up'); p.tick(4)
    put('cat_y',112*16,2); put('velocity',0,2)
    put('cactus_x',3000,2); put('fish_active',0); put('jump_buffer',0)
    lowest=112*16
    p.button_press(button)
    landed=False
    for t in range(100):
        if t==hold: p.button_release(button)
        if repress and t==hold+3: p.button_press(button)
        p.tick(1)
        lowest=min(lowest,get('cat_y',2))
        if t>5 and get('cat_y',2)==112*16:
            landed=True
            break
    assert landed and get('running')==1
    if hold>=60:
        p.tick(10)
        assert get('cat_y',2)==112*16, 'Holding jump causes unwanted auto-jumps'
    p.button_release(button); p.tick(4)
    return (112*16-lowest)/16
try:
    p.tick(180); p.button_press('start'); p.tick(3)
    p.button_release('start'); p.tick(12)
    for pet in (0,4,5):
        put('character',pet)
        for speed in (2,4):
            put('speed',speed)
            for button in ('a','up'):
                heights=[arc(button,n) for n in (1,6,12,60)]
                assert all(a<b for a,b in zip(heights,heights[1:])), heights
                assert heights[0]<20 and heights[-1]>55, heights
                assert arc(button,1,repress=True)==heights[0], 'Midair repress restores lift'
                print(f'pet={pet} speed={speed} {button}: tap/6/12/hold heights {heights}')
    print('PASS: progressive jump heights, A and Up, cat, dog and ghost, both speeds, landing and no double jump')
finally:
    p.stop(save=False)
