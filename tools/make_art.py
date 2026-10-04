from pathlib import Path

cat = [
'0000000000000000',
'0000000030000300',
'0000000033003300',
'0000000031331300',
'0300000031111300',
'0330000031313300',
'0033333331121300',
'0031111113333000',
'0031111111130000',
'0031111111130000',
'0031111111130000',
'0003111111300000',
'0003313331300000',
'0003100031300000',
'0003300033300000',
'0000000000000000']
cactus = [
'0000000330000000',
'0000003223000000',
'0000003213000000',
'0033003213000000',
'0322303213003300',
'0321303213032230',
'0321303213032130',
'0321333213032130',
'0322222213332130',
'0033333212222130',
'0000003213333300',
'0000003213000000',
'0000003213000000',
'0000003213000000',
'0000003333000000',
'0000000000000000']
cat2 = cat.copy()
cat2[13] = '0000330003300000'
cat2[14] = '0000330003300000'

def tiles(rows):
    result = []
    for ty in range(0, len(rows), 8):
        for tx in range(0, len(rows[0]), 8):
            for row in rows[ty:ty+8]:
                pixels = [int(c) for c in row[tx:tx+8]]
                result += [sum((p & 1) << (7-i) for i,p in enumerate(pixels)),
                           sum(((p >> 1) & 1) << (7-i) for i,p in enumerate(pixels))]
    return result

ground = ['33333333','22222222','11111111','11131111','11111111','13111111','11111131','11111111']
cloud = ['00000000','00000000','00011000','00111100','01111110','00000000','00000000','00000000']
# Every obstacle occupies a 16x24 sprite box, anchored to the ground.
small = ['0000000000000000'] * 8 + cactus
round_cactus = ['0000000000000000'] * 12 + [
'0000033333300000','0000322222230000','0003212121223000',
'0003212121223000','0003212121223000','0003212121223000',
'0003212121223000','0003212121223000','0003212121223000',
'0000322222230000','0000033333300000','0000000000000000']
tall = cactus[:11] + [cactus[11]] * 8 + cactus[11:]
duck = ['0000000000000000'] * 8 + [
'0000000030000300','0000000033003300','0333333331331300',
'0311111111313300','0311111111111300','0031111113333000',
'0003333333330000','0000000000000000']
bird = ['0000000000000000'] * 5 + [
'0000000030000000','0000000330000000','0000003310033300',
'0000033113313130','0000331111113322','0333311111333000',
'0000033333000000','0000000000000000'] + ['0000000000000000'] * 11
bird2 = bird.copy()
bird2[5:8] = ['0000000000000000'] * 3
bird2[11:14] = ['0000033133000000','0000003310000000','0000000330000000']
dog = [
'0000000000000000','0000000003333000','0000000031113300',
'0000000031313320','0300000031113320','0330000031133300',
'0033333333333000','0031111111130000','0031111111130000',
'0031111111130000','0031111111130000','0003111111300000',
'0003313331300000','0003100031300000','0003300033300000',
'0000000000000000']
dog2 = dog.copy()
dog2[13:15] = ['0000330003300000'] * 2
dog_duck = ['0000000000000000'] * 8 + [
'0000000003333000','0000000031113300','0333333331313320',
'0311111111113320','0311111111133300','0031111113333000',
'0003333333330000','0000000000000000']
fish = [
'0000000000000000','0000000333300000','0300033111130000',
'0333311113133000','0333311111133000','0300033111130000',
'0000000333300000','0000000000000000']
hole = ['22222222222222222222222222222222'] + ['33333333333333333333333333333333']*15
river = ['22222222222222222222222222222222'] + [
    ''.join('1' if (x+y*2)%12 < 4 else '3' for x in range(32)) for y in range(15)]
# Deduplicate an original, seamless 256-pixel mountain panorama.
mountain_tiles=[]; mountain_map=[]; lookup={}
for ty in range(6):
    for tx in range(32):
        rows=[]
        for dy in range(8):
            y=ty*8+dy
            row=''
            for dx in range(8):
                x=tx*8+dx
                distance=lambda a,b: min(abs(a-b),256-abs(a-b))
                ridge=min(12+distance(x,42)*3//5, 5+distance(x,158)*2//3,
                          24+distance(x,226)//2)
                row += '2' if y>=ridge+12 else ('1' if y>=ridge else '0')
            rows.append(row)
        tile=tuple(tiles(rows))
        if tile not in lookup:
            lookup[tile]=131+len(lookup); mountain_tiles.extend(tile)
        mountain_map.append(lookup[tile])
assert max(mountain_map)<256
print(f'Mountains: {len(lookup)} unique tiles')
def blank(w=16,h=24): return [['0']*w for _ in range(h)]
def rect(c,x,y,w,h,v):
    for yy in range(y,min(y+h,len(c))):
        for xx in range(x,min(x+w,len(c[0]))):
            if xx>=0 and yy>=0: c[yy][xx]=str(v)
def rows(c): return [''.join(r) for r in c]
ghost=blank(h=16)
for y in range(1,15):
    for x in range(2,14):
        if y>=4 or (x-8)**2+(y-6)**2<26: ghost[y][x]='1'
rect(ghost,4,5,2,3,2); rect(ghost,10,5,2,3,2); rect(ghost,7,10,2,2,2)
for x in range(2,14): ghost[14][x]='1' if x%4<2 else '0'
ghost2=[r.copy() for r in ghost]
ghost2[14]=list('0011001100110000')
ghost_duck=blank(h=16)
for y in range(8,15):
    for x in range(2,14): ghost_duck[y][x]='1'
rect(ghost_duck,4,10,2,2,2); rect(ghost_duck,10,10,2,2,2)
def pumpkin(top):
    c=blank(); height=22-top
    rect(c,7,top,2,2,2)
    for y in range(top+2,23):
        for x in range(2,14):
            if ((x-8)/6)**2+((y-(top+24)/2)/max(5,height/2))**2<1.5:
                c[y][x]='1'
    eye=top+max(3,height//3)
    rect(c,4,eye,2,2,3); rect(c,10,eye,2,2,3)
    rect(c,5,min(eye+4,20),6,2,3); rect(c,7,min(eye+4,20),2,1,2)
    return rows(c)
witch=blank()
rect(witch,7,5,2,2,3); rect(witch,6,7,4,2,3); rect(witch,4,9,8,1,3)
rect(witch,7,10,3,2,1); rect(witch,6,12,5,1,3)
rect(witch,2,14,12,1,2); rect(witch,12,13,4,3,2)
candy=blank(h=8)
rect(candy,4,1,8,6,3); rect(candy,5,2,6,4,1); rect(candy,7,2,2,4,2)
rect(candy,1,2,3,4,1); rect(candy,12,2,3,4,1)
def zombie(top):
    c=blank(); rect(c,5,top,6,5,1)
    rect(c,6,top+1,1,1,3); rect(c,9,top+1,1,1,3)
    rect(c,7,top+3,3,1,3)
    rect(c,5,top+5,6,max(2,18-top),2)
    rect(c,1,top+6,5,2,1); rect(c,10,top+6,5,2,1)
    rect(c,5,21,2,2,3); rect(c,9,21,2,2,3)
    return rows(c)
moon=blank(h=16)
for y in range(16):
    for x in range(16):
        if (x-7)**2+(y-7)**2<49 and (x-11)**2+(y-4)**2>36: moon[y][x]='1'
star=['00000000','00010000','00111000','00010000']+['00000000']*4
halloween=(tiles(rows(ghost))+tiles(rows(ghost2))+tiles(rows(ghost_duck))
           +tiles(pumpkin(10))+tiles(pumpkin(14))+tiles(pumpkin(2))
           +tiles(rows(witch))+tiles(rows(candy))
           +tiles(zombie(10))+tiles(zombie(14))+tiles(zombie(2)))
data = (tiles(cat) + tiles(cat2) + tiles(duck) + tiles(small)
        + tiles(round_cactus) + tiles(tall) + tiles(bird) + tiles(bird2) + tiles(dog) + tiles(dog2) + tiles(dog_duck) + tiles(fish) + tiles(hole) + tiles(river) + halloween)
bg = tiles(['00000000'] * 8) + tiles(ground) + tiles(cloud)
def array(name, values):
    return 'const unsigned char ' + name + '[] = {\n' + ',\n'.join(
        '  ' + ','.join(f'0x{x:02x}' for x in values[i:i+16])
        for i in range(0,len(values),16)) + '\n};\n'
Path('src/art.h').write_text('/* Generated by tools/make_art.py */\n' + array('sprite_art',data) + array('scene_art',bg) + array('mountain_art',mountain_tiles) + array('mountain_map',mountain_map) + array('night_art',tiles(rows(moon))+tiles(star)))
