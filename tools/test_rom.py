"""Exercise the compiled ROM through real button input in a headless emulator."""
from pathlib import Path
from pyboy import PyBoy

symbols = {}
for line in Path('build/cactus-cat.noi').read_text().splitlines():
    parts = line.split()
    if len(parts) == 3 and parts[0] == 'DEF':
        symbols[parts[1]] = int(parts[2], 16)

p = PyBoy('build/cactus-cat.gbc', window='null', sound_emulated=True)
p.set_emulation_speed(0)
def value(name, signed=False, size=1):
    addr = symbols['_' + name]
    n = sum(p.memory[addr+i] << (8*i) for i in range(size))
    return n - (1 << (size*8)) if signed and n & (1 << (size*8-1)) else n
def press(button):
    p.button_press(button); p.tick(3)
    p.button_release(button); p.tick(3)
def until(predicate, limit=400):
    for _ in range(limit):
        if predicate(): return
        p.tick(1)
    raise AssertionError('Timed out waiting for game state')
try:
    p.tick(180)
    assert value('running') == 0
    # Verify music is sequenced, produces audio, and can be muted.
    import numpy as np
    samples=[]
    for _ in range(32):
        p.tick(1); samples.append(p.sound.ndarray.copy())
    assert any(np.any(chunk) for chunk in samples), 'Silent music output'
    old_step=value('music_step'); p.tick(16)
    assert value('music_step') != old_step
    press('select'); assert value('music_muted') == 1
    old_step=value('music_step'); p.tick(16)
    assert value('music_step') == old_step and p.memory[0xff25] == 0x11
    press('select'); assert value('music_muted') == 0 and p.memory[0xff25] == 0xff
    p.screen.image.save('build/title.png')
    assert value('picking') == 1
    appearances=[]
    for choice in range(5):
        assert value('character') == choice
        p.tick(10)
        appearances.append(p.screen.ndarray[112:128,32:48,:3].copy())
        p.screen.image.save(f'build/pet-{choice}.png')
        if choice < 4:
            press('right'); p.tick(10)
    assert all(not np.array_equal(appearances[i],appearances[j])
               for i in range(5) for j in range(i+1,5))
    press('start'); p.tick(10)
    assert value('running') == 1 and value('picking') == 0
    assert p.memory[0xfe02] >= 42, 'Dog art not used in gameplay'
    panorama=p.screen.ndarray[64:112,100:160,:3].copy()
    p.tick(12)
    assert not np.array_equal(panorama,p.screen.ndarray[64:112,100:160,:3]), 'Mountains do not visibly scroll'
    p.screen.image.save('build/fish.png')
    until(lambda: value('cactus_x', True, 2) <= 78)
    p.button_press('a'); p.tick(3)
    assert value('cat_y', True, 2) < 112*16
    p.tick(8)
    p.screen.image.save('build/jump.png')
    until(lambda: value('cleared', size=2) == 1)
    p.button_release('a'); p.tick(3)
    assert value('running') == 1
    assert value('score', size=2) == 1+5*value('fish_eaten', size=2)
    press('start')
    assert value('paused') == 1
    before = value('cactus_x', True, 2)
    fish_before = value('fish_x', True, 2)
    mountain_before=value('mountain_scroll')
    p.tick(60)
    assert value('cactus_x', True, 2) == before
    assert value('fish_x', True, 2) == fish_before
    assert value('mountain_scroll') == mountain_before
    press('start')
    until(lambda: value('running') == 0)
    p.tick(10)
    assert value('cleared', size=2) == 1
    assert value('best', size=2) >= 1
    p.screen.image.save('build/game-over.png')
    press('b'); p.tick(10)
    assert value('picking') == 1 and value('character') == 4
    press('right'); p.tick(10)
    assert value('character') == 0
    press('left'); p.tick(10)
    assert value('character') == 4
    press('right'); p.tick(10)
    press('a'); p.tick(10)
    assert value('running') == 1 and value('score', size=2) == 0
    assert value('best', size=2) >= 1
    # Play enough obstacles to check all speed transitions with button input.
    seen = set(); heights=set(); gaps=set()
    for target in range(1, 61):
        speed = value('speed')
        until(lambda: value('cactus_x', True, 2) <= 32 + speed*21)
        kind = value('obstacle_kind'); seen.add(kind)
        heights.add(value('fish_y'))
        gaps.add(value('cactus_x',True,2)-value('fish_x',True,2))
        if kind < 3 or kind >= 5:
            p.button_press('a'); p.tick(3)
        elif kind == 3:
            p.button_press('down')
        if 3 <= kind <= 4:
            p.tick(4)
            p.screen.image.save(f'build/bird-{kind}.png')
        until(lambda: value('cleared', size=2) == target or value('running') == 0)
        assert value('running') == 1, f'Hazard failed {target}: kind={kind}, y={value("cat_y",True,2)/16}, x={value("cactus_x",True,2)}'
        p.button_release('a'); p.button_release('down')
        until(lambda: value('passed') == 0)
        assert 140 <= value('cactus_x', True, 2) <= 175
    assert value('speed') == 4
    assert len(heights) >= 5 and all(76 <= y <= 116 for y in heights), heights
    assert len(gaps) > 10, gaps
    assert value('score', size=2) == 60+5*value('fish_eaten', size=2)
    assert seen == set(range(7)), seen
    # Missing a fish is harmless; eating it awards once and caps the score.
    def set_value(name, n, size=1):
        for i in range(size): p.memory[symbols['_'+name]+i] = (n >> (8*i)) & 255
    eaten=value('fish_eaten', size=2); points=value('score', size=2)
    set_value('cactus_x',184,2); set_value('passed',0)
    set_value('cat_y',80*16,2); set_value('velocity',0,2)
    set_value('fish_y',116); set_value('fish_x',40,2); set_value('fish_active',1)
    p.tick(12)
    assert value('fish_eaten',size=2)==eaten and value('score',size=2)==points
    assert value('running')==1
    set_value('cactus_x',184,2); set_value('cat_y',112*16,2)
    set_value('velocity',0,2); set_value('fish_x',40,2)
    set_value('fish_y',116); set_value('fish_active',1); set_value('score',9998,2)
    p.tick(8)
    assert value('score',size=2)==9999 and value('fish_eaten',size=2)==eaten+1
    assert value('fish_active')==0 and value('running')==1
    # Elevated fish are collected by a real jump, with a hazard kept distant.
    set_value('score',0,2); set_value('cat_y',112*16,2)
    set_value('velocity',0,2); set_value('cactus_x',300,2)
    set_value('fish_x',72,2); set_value('fish_y',76)
    set_value('fish_active',1)
    p.button_press('a'); p.tick(3)
    until(lambda: value('fish_active') == 0)
    p.tick(4)
    assert value('score',size=2)==5 and value('fish_eaten',size=2)==eaten+2
    p.screen.image.save('build/fish-jump.png')
    p.button_release('a')
    until(lambda: value('cat_y',True,2)==112*16)
    # Without ducking, a low bird must cause a collision.
    p.memory[symbols['_obstacle_kind']] = 3
    p.memory[symbols['_obstacle_y']] = 102
    p.memory[symbols['_cactus_x']] = 64
    p.memory[symbols['_cactus_x']+1] = 0
    until(lambda: value('running') == 0)
    # Both terrain hazards must be jumpable and fatal without a jump.
    for terrain in (5,6):
        p.tick(12); press('a'); p.tick(10)
        set_value('obstacle_kind',terrain); set_value('cactus_x',80,2)
        set_value('fish_active',0); set_value('speed',2)
        set_value('cat_y',112*16,2); set_value('velocity',0,2)
        set_value('jump_buffer',0)
        start_scroll=value('mountain_scroll')
        p.button_press('a'); p.tick(11)
        p.screen.image.save(f'build/terrain-{terrain}.png')
        assert value('mountain_scroll') != start_scroll
        until(lambda: value('cleared',size=2)==1 or value('running')==0)
        assert value('running')==1, f'Terrain {terrain} not jumpable'
        p.button_release('a')
        until(lambda: value('cat_y',True,2)==112*16)
        set_value('obstacle_kind',terrain); set_value('cactus_x',64,2)
        set_value('passed',0); set_value('fish_active',0)
        until(lambda: value('running')==0)
        p.tick(12)
        p.screen.image.save(f'build/terrain-fail-{terrain}.png')
    print('PASS: scrolling mountains, pause, hole and river jumps and falls; randomized fish heights and gaps, jump pickup; fish eating +5, fish pause, combined scoring; 5 distinct pet previews, dog gameplay, pet switching, shorter gaps; music output, sequencing and mute; 60 hazards, all 3 cactus varieties, both bird heights, ducking, bird collision, scoring, pause and restart')
finally:
    p.stop(save=False)
