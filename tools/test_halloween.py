"""Verify the ghost world, real scoring transitions and themed sprite choices."""
from pathlib import Path
from pyboy import PyBoy
symbols={}
for line in Path('build/cactus-cat.noi').read_text().splitlines():
    fields=line.split()
    if len(fields)==3 and fields[0]=='DEF': symbols[fields[1]]=int(fields[2],16)
p=PyBoy('build/cactus-cat.gbc',window='null',sound_emulated=True)
p.set_emulation_speed(0)
def get(name,size=1): return sum(p.memory[symbols['_'+name]+i]<<(8*i) for i in range(size))
def put(name,n,size=1):
    for i in range(size): p.memory[symbols['_'+name]+i]=(n>>(8*i))&255
def press(button):
    p.button_press(button); p.tick(4); p.button_release(button); p.tick(12)
def until(fn):
    for _ in range(400):
        if fn(): return
        p.tick(1)
    raise AssertionError('Timed out')
try:
    p.tick(180)
    for _ in range(5): press('right')
    assert get('character')==5
    press('start')
    assert get('running')==1 and p.memory[0xfe02]>=72
    assert p.memory[0x9800+4*32+17]==197 and p.memory[0x9800+5*32+18]==200
    put('cactus_x',112,2); put('fish_x',88,2); put('fish_y',100)
    p.tick(3); p.screen.image.save('build/ghost-night.png')
    # Ghost can clear every pumpkin size and both witch heights.
    for kind in range(5):
        put('obstacle_kind',kind); put('obstacle_y',102 if kind==3 else 84 if kind==4 else 104)
        put('cactus_x',100,2); put('cat_y',112*16,2); put('velocity',0,2)
        put('jump_buffer',0); put('passed',0); put('fish_active',0); put('speed',2)
        p.tick(2)
        assert p.memory[0xfe12]==(84+kind*6 if kind<3 else 102)
        if kind<3:
            until(lambda: get('cactus_x',2)<=76)
            p.button_press('a')
        elif kind==3: p.button_press('down')
        cleared=get('cleared',2)
        until(lambda: get('cleared',2)>cleared or get('running')==0)
        assert get('running')==1
        p.button_release('a'); p.button_release('down'); p.tick(12)
    # At exactly 100, an on-screen pumpkin becomes a zombie immediately.
    put('obstacle_kind',0); put('obstacle_y',104); put('score',99,2)
    put('cactus_x',20,2); put('passed',0); put('fish_active',0)
    p.tick(1); assert get('zombie_mode')==0
    until(lambda: get('score',2)==100)
    p.tick(8)
    assert get('zombie_mode')==1 and p.memory[0xfe12]==110
    put('cactus_x',112,2); p.tick(2)
    p.screen.image.save('build/ghost-zombies.png')
    # Retry restores pumpkins, and candy can independently cross the threshold.
    put('cactus_x',64,2); put('cat_y',112*16,2); put('velocity',0,2)
    until(lambda: get('running')==0); p.tick(12); press('start')
    assert get('score',2)==0 and get('zombie_mode')==0 and get('character')==5
    put('cactus_x',184,2); put('fish_active',1); put('fish_x',48,2)
    put('fish_y',116); put('score',95,2)
    p.tick(2); assert p.memory[0xfe2a]==108
    until(lambda: get('fish_active')==0); p.tick(8)
    assert get('score',2)==100 and get('zombie_mode')==1
    # Cats still retain their daytime assets above the same score threshold.
    put('cactus_x',64,2); until(lambda: get('running')==0)
    p.tick(12); press('b'); press('right')
    assert get('character')==0
    press('start'); put('score',100,2); put('cactus_x',112,2)
    p.tick(4)
    assert get('zombie_mode')==0 and p.memory[0xfe02]<8 and p.memory[0xfe12]==12
    assert p.memory[0x9800+4*32+17]==128
    print('PASS: ghost selection, moon, pumpkins, witches, candy, 99-to-100 zombie transformation, candy threshold, retry reset and daytime restoration')
finally:
    p.stop(save=False)
