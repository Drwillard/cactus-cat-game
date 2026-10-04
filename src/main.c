#include <gb/gb.h>
#include <gb/cgb.h>
#include <gbdk/console.h>
#include <gbdk/font.h>
#include <stdio.h>
#include "art.h"

#define FLOOR 112
#define CAT_X 32
uint16_t score, best, random_state = 0xace1u;
int16_t cat_y, velocity, cactus_x;
uint8_t running, paused, frame, speed, passed;
volatile uint8_t input_pressed, input_held;
static void sample_input(void) {
    uint8_t buttons=joypad();
    input_pressed |= buttons & ~input_held;
    input_held=buttons;
}
uint8_t obstacle_kind, obstacle_y, ducking;
uint8_t character, picking=1;
int16_t fish_x;
uint8_t fish_active, fish_y, jump_buffer, jump_cut;
uint16_t cleared, fish_eaten;
uint8_t mountain_scroll, scenery_clock;
static void scenery_vblank(void) { SCX_REG=0; LYC_REG=64; }
static void scenery_scanline(void) {
    if (LYC_REG==64) {
        SCX_REG=running ? mountain_scroll : 0; LYC_REG=112;
    } else { SCX_REG=0; LYC_REG=64; }
}
#include "music.h"
static const uint8_t obstacle_tiles[] = {12,18,24,30,30};
static const uint8_t obstacle_tops[] = {10,14,2,5,5};
static const palette_color_t bg_colors[] = { RGB(27,29,25), RGB(24,21,13), RGB(19,14,8), RGB(6,9,10) };
static const palette_color_t mountain_colors[] = {RGB(27,29,25),RGB(23,26,23),RGB(20,24,21),RGB(6,9,10)};
static const palette_color_t river_colors[] = {RGB(27,29,25),RGB(19,28,31),RGB(19,14,8),RGB(6,17,25)};
static const palette_color_t hole_colors[] = {RGB(27,29,25),RGB(12,10,8),RGB(19,14,8),RGB(3,4,6)};
static const palette_color_t fish_colors[] = { RGB(27,29,25), RGB(10,26,31), RGB(31,25,8), RGB(3,9,16) };
static const palette_color_t cat_colors[] = { RGB(27,29,25), RGB(30,19,7), RGB(31,11,15), RGB(6,6,9) };
static const palette_color_t cactus_colors[] = { RGB(27,29,25), RGB(13,24,10), RGB(6,17,8), RGB(3,9,6) };

static void message(const char *line);
static const palette_color_t pet_colors[][4] = {
    { RGB(27,29,25), RGB(30,19,7), RGB(31,11,15), RGB(6,6,9) },
    { RGB(27,29,25), RGB(9,11,16), RGB(31,11,15), RGB(2,3,5) },
    { RGB(27,29,25), RGB(31,31,30), RGB(31,14,19), RGB(8,9,12) },
    { RGB(27,29,25), RGB(13,21,31), RGB(31,11,15), RGB(4,7,16) },
    { RGB(27,29,25), RGB(22,14,7), RGB(31,12,16), RGB(5,4,3) }
};
static const char *pet_names[] = {"ORANGE CAT", "BLACK CAT", "WHITE CAT", "BLUE CAT", "BROWN DOG"};
static void landscape(uint8_t show) {
    uint8_t attrs[32];
    for (uint8_t i=0;i<32;++i) attrs[i]=show ? 1 : 0;
    for (uint8_t y=8;y<14;++y) {
        if (_cpu==CGB_TYPE) { VBK_REG=1; set_bkg_tiles(0,y,32,1,attrs); VBK_REG=0; }
        if (show) set_bkg_tiles(0,y,32,1,mountain_map+(y-8)*32);
        else { uint8_t blank[32]; for (uint8_t i=0;i<32;++i) blank[i]=128;
            set_bkg_tiles(0,y,32,1,blank); }
    }
}
static void picker(void) {
    landscape(0); picking=1; running=0; paused=0; ducking=0; cat_y=FLOOR*16;
    cactus_x=184; fish_active=0;
    if (_cpu == CGB_TYPE) set_sprite_palette(0,1,pet_colors[character]);
    gotoxy(0,3); printf("   CACTUS CAT V8     ");
    message("   CHOOSE YOUR PET");
    gotoxy(0,9); printf("  < %s >     ",pet_names[character]);
    gotoxy(0,10); printf(" LEFT/RIGHT: CHANGE ");
    gotoxy(0,11); printf(" A / START: PLAY    ");
    gotoxy(0,12); printf(" SELECT: MUSIC      ");
    gotoxy(0,1); printf(" A:JUMP B/DOWN:DUCK ");
    gotoxy(0,5); printf("    EAT FISH +5     ");
    gotoxy(0,6); printf(" TAP:HOP HOLD:JUMP  ");
}
static uint8_t random_gap(void) {
    random_state ^= random_state << 7;
    random_state ^= random_state >> 9;
    random_state ^= random_state << 8;
    return (uint8_t)(random_state % 64u);
}
static void sound(uint8_t kind) {
    NR10_REG = kind == 0 ? 0x16 : 0x00;
    NR11_REG = 0x80;
    NR12_REG = 0x92;
    NR13_REG = kind == 2 ? 0x20 : (kind == 3 ? 0xf0 : 0xc0);
    NR14_REG = kind == 2 ? 0x83 : 0x86;
}
static void message(const char *line) {
    gotoxy(0,7); printf("                    ");
    gotoxy(0,7); printf("%s",line);
}
static void hud(void) {
    gotoxy(0,0);
    printf("%s %u%u%u%u BEST %u%u%u%u", character==4 ? "DOG" : "CAT",
        score/1000, (score/100)%10, (score/10)%10, score%10,
        best/1000, (best/100)%10, (best/10)%10, best%10);
}
static void spawn_fish(void) {
    fish_x=cactus_x-40-(random_gap() & 31);
    /* Six reachable heights: ground-level snacks through jump pickups. */
    fish_y=76+8*(random_gap() % 6);
    fish_active=1;
}
static void spawn(void) {
    /* Introduce every hazard within the first five obstacles. */
    if (cleared < 7) obstacle_kind=(uint8_t)cleared;
    else {
        uint8_t roll=random_gap() % 24;
        obstacle_kind=roll < 16 ? roll % 3 : (roll < 20 ? 3+(roll & 1) : 5+(roll & 1));
    }
    obstacle_y = obstacle_kind == 3 ? 102 : (obstacle_kind == 4 ? 84 : 104);
    cactus_x = 160 + (random_gap() & 15); passed = 0;
    spawn_fish();
}
static void draw(void) {
    uint8_t base = running && !paused && cat_y == FLOOR * 16 && (frame & 8) ? 4 : 0;
    uint8_t y = (uint8_t)(cat_y / 16);
    if (ducking) base=8;
    if (character==4) base+=42;
    for (uint8_t i = 0; i != 4; ++i) {
        set_sprite_tile(i,base+i);
        move_sprite(i,CAT_X+8+(i & 1)*8,y+16+(i >> 1)*8);
    }
    for (uint8_t i=0; i<2; ++i) {
        set_sprite_tile(i+10,54+i);
        set_sprite_prop(i+10,_cpu == CGB_TYPE ? 3 : 0);
        if (fish_active && fish_x > -16 && fish_x < 160)
            move_sprite(i+10,(uint8_t)(fish_x+8+i*8),(uint8_t)(fish_y+16));
        else hide_sprite(i+10);
    }
    for (uint8_t i=0;i<8;++i) {
        if (obstacle_kind>=5 && cactus_x>-32 && cactus_x<160) {
            set_sprite_tile(i+12,(obstacle_kind==5 ? 56 : 64)+i);
            set_sprite_prop(i+12,_cpu==CGB_TYPE ? (obstacle_kind==5 ? 5 : 4) : 0);
            move_sprite(i+12,(uint8_t)(cactus_x+8+(i & 3)*8),(uint8_t)(144+(i >> 2)*8));
        } else hide_sprite(i+12);
    }
    for (uint8_t i=0; i<6; ++i) {
        if (obstacle_kind>=5) { hide_sprite(i+4); continue; }
        uint8_t tile_base = obstacle_tiles[obstacle_kind];
        if (obstacle_kind >= 3 && (frame & 8)) tile_base=36;
        set_sprite_tile(i+4,tile_base+i);
        set_sprite_prop(i+4,_cpu == CGB_TYPE ? (obstacle_kind >= 3 ? 2 : 1) : 0);
        if (cactus_x > -16 && cactus_x < 160)
            move_sprite(i+4,(uint8_t)(cactus_x+8+(i & 1)*8),obstacle_y+16+(i >> 1)*8);
        else hide_sprite(i+4);
    }
}
static void eat_fish(void) {
    if (!fish_active) return;
    fish_x-=speed;
    if (fish_x < -16) { fish_active=0; return; }
    if (fish_x+15 > CAT_X+3 && fish_x+1 < CAT_X+13
        && cat_y/16+14 > fish_y+1 && cat_y/16+(ducking ? 10 : 2) < fish_y+7) {
        fish_active=0; ++fish_eaten;
        score=score > 9994 ? 9999 : score+5;
        sound(3); hud();
    }
}
static void restart(void) {
    cleared=0; fish_eaten=0; jump_buffer=0;
    score = 0; speed = 2; cat_y = FLOOR * 16; velocity = 0;
    obstacle_kind=0; obstacle_y=104; ducking=0;
    cactus_x = 184; spawn_fish(); passed = 0; running = 1; paused = 0;
    mountain_scroll=0; scenery_clock=0; landscape(1);
    picking=0; message(""); hud();
}
void main(void) {
    uint8_t buttons, pressed, tile;
    DISPLAY_OFF;
    font_init(); font_set(font_load(font_ibm));
    BGP_REG = 0xe4; OBP0_REG = 0xe4;
    if (_cpu == CGB_TYPE) {
        set_bkg_palette(0,1,bg_colors);
        set_bkg_palette(1,1,mountain_colors);
        set_sprite_palette(0,1,cat_colors);
        set_sprite_palette(1,1,cactus_colors);
        set_sprite_palette(2,1,cat_colors);
        set_sprite_palette(3,1,fish_colors);
        set_sprite_palette(4,1,river_colors);
        set_sprite_palette(5,1,hole_colors);
    }
    set_bkg_data(128,3,scene_art);
    for (uint8_t y=0; y<18; ++y) {
        for (uint8_t x=0; x<20; ++x) {
            tile = y>=16 ? 129 : 128;
            if (y == 4 && (x==3 || x==12 || x==13)) tile=130;
            set_bkg_tiles(x,y,1,1,&tile);
        }
    }
    set_bkg_data(131,sizeof(mountain_art)/16,mountain_art);
    set_sprite_data(0,72,sprite_art);
    for (uint8_t i=0; i<4; ++i) {
        set_sprite_tile(i+4,8+i);
        set_sprite_prop(i+4,_cpu == CGB_TYPE ? 1 : 0);
    }
    NR52_REG=0x80; NR50_REG=0x77; NR51_REG=0xff;
    music_init();
    add_VBL(sample_input);
    add_VBL(scenery_vblank); add_LCD(scenery_scanline);
    LYC_REG=64; STAT_REG |= STATF_LYC;
    set_interrupts(VBL_IFLAG | LCD_IFLAG);
    cat_y=FLOOR*16; cactus_x=132; obstacle_y=104;
    hud(); picker();
    SHOW_BKG; SHOW_SPRITES; DISPLAY_ON;
    while (1) {
        vsync(); ++frame;
        /* Keep brief button presses even while the HUD updates. */
        disable_interrupts();
        buttons=input_held; pressed=input_pressed; input_pressed=0;
        enable_interrupts();
        if (pressed & J_SELECT) {
            music_muted=!music_muted; NR51_REG=music_muted ? 0x11 : 0xff;
        }
        if (!running) {
            if (!picking && (pressed & J_B)) picker();
            if (picking && (pressed & (J_LEFT | J_RIGHT))) {
                character=(character+(pressed & J_RIGHT ? 1 : 4)) % 5;
                picker(); hud();
            }
            if (pressed & (J_START | J_A)) {
                gotoxy(0,3); printf("                    ");
                gotoxy(0,5); printf("                    ");
                gotoxy(0,6); printf("                    ");
                gotoxy(0,12); printf("                    ");
                gotoxy(0,9); printf("                    ");
                gotoxy(0,10); printf("                    ");
                gotoxy(0,11); printf("                    ");
                restart();
            }
        } else {
            if (pressed & J_START) { paused=!paused; message(paused ? "       PAUSED" : ""); }
            if (!paused) {
                ducking = (buttons & (J_DOWN | J_B)) && cat_y == FLOOR*16;
                if (pressed & (J_A | J_UP)) jump_buffer=6;
                if (jump_buffer && !ducking && cat_y == FLOOR*16) {
                    velocity=-88; jump_buffer=0; jump_cut=0; sound(0);
                }
                if (jump_buffer) --jump_buffer;
                /* Releasing during ascent cuts lift once; pressing again in
                   midair cannot restore it or start a second jump. */
                if (!jump_cut && velocity<0 && !(buttons & (J_A | J_UP))) {
                    jump_cut=1;
                    if (velocity < -32) velocity=-32;
                }
                cat_y += velocity;
                velocity += 4;
                if (cat_y >= FLOOR*16) { cat_y=FLOOR*16; velocity=0; }
                if (++scenery_clock>=4) { scenery_clock=0; ++mountain_scroll; }
                cactus_x -= speed;
                eat_fish();
                /* Slightly inset hitboxes make near misses feel fair. */
                if ((obstacle_kind>=5 && cactus_x+32 > CAT_X+4 && cactus_x < CAT_X+12 && cat_y>=FLOOR*16-16)
                    || (obstacle_kind<5 && cactus_x+13 > CAT_X+3 && cactus_x+3 < CAT_X+13
                    && cat_y/16+14 > obstacle_y+obstacle_tops[obstacle_kind]
                    && cat_y/16+(ducking ? 10 : 2) < obstacle_y+(obstacle_kind >= 3 ? 12 : 23))) {
                    running=0; sound(2);
                    if (score>best) best=score;
                    landscape(0); hud();
                    message(obstacle_kind==6 ? "   SPLASH! RETRY" : (obstacle_kind==5 ? "    FELL! RETRY" : "     OUCH! RETRY"));
                    gotoxy(2,9); printf("A:RETRY B:PET");
                } else if (!passed && cactus_x+(obstacle_kind>=5 ? 32 : 16) <= CAT_X) {
                    passed=1; ++cleared; if (score<9999) ++score;
                    speed=2+(cleared/10>2 ? 2 : cleared/10);
                    sound(1); hud();
                }
                if (cactus_x < (obstacle_kind>=5 ? -32 : -16)) spawn();
            }
        }
        draw();
    }
}
