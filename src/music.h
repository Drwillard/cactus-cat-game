/* Original 80s-style E minor synth arpeggio. Music uses channels 2-4;
   channel 1 remains available for jump, score and collision effects. */
uint8_t music_step, music_clock, music_muted;
static const uint16_t lead_notes[] = {1849,1881,1915,1881,1849,1881,1936,1915,1849,1881,1915,1881,1825,1881,1915,1881,1798,1849,1881,1849,1798,1849,1915,1881,1798,1849,1881,1849,1783,1849,1881,1849,1714,1783,1825,1783,1714,1783,1899,1825,1714,1783,1825,1783,1750,1783,1825,1783,1825,1860,1899,1860,1825,1860,1923,1899,1825,1860,1899,1860,1860,1899,1936,1899};
static const uint16_t bass_notes[] = {1253,1046,711,1155};
static void music_tick(void) {
    uint16_t note;
    if (paused || music_muted) return;
    if (++music_clock < 8) return;
    music_clock=0;
    note=lead_notes[music_step];
    NR21_REG=0x80 | 0x30; NR22_REG=0x72;
    NR23_REG=(uint8_t)note; NR24_REG=0xc0 | (note >> 8);
    if (!(music_step & 3)) {
        note=bass_notes[music_step >> 4];
        NR31_REG=0xc0; NR32_REG=0x20;
        NR33_REG=(uint8_t)note; NR34_REG=0xc0 | (note >> 8);
    }
    /* Kick on beats 1/3, snare on 2/4, with quiet offbeat hats. */
    NR41_REG=0x38;
    if ((music_step & 15)==0 || (music_step & 15)==8) {
        NR42_REG=0xa1; NR43_REG=0x53;
    } else if ((music_step & 15)==4 || (music_step & 15)==12) {
        NR42_REG=0x91; NR43_REG=0x25;
    } else { NR42_REG=0x31; NR43_REG=0x13; }
    NR44_REG=0xc0;
    music_step=(music_step+1) & 63;
}
static void music_init(void) {
    static const uint8_t wave[] = {0x01,0x23,0x45,0x67,0x89,0xab,0xcd,0xef,
                                 0xfe,0xdc,0xba,0x98,0x76,0x54,0x32,0x10};
    NR30_REG=0;
    for (uint8_t i=0;i<16;++i) ((volatile uint8_t *)0xff30)[i]=wave[i];
    NR30_REG=0x80;
    add_VBL(music_tick);
}
