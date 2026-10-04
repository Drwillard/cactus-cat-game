GBDK ?= tools/gbdk
ROM = build/cactus-cat-v8.gbc

all: $(ROM)
	cp $(ROM) build/cactus-cat.gbc
	cp build/cactus-cat-v8.noi build/cactus-cat.noi

src/art.h: tools/make_art.py
	python3 tools/make_art.py

$(ROM): src/main.c src/art.h src/music.h
	mkdir -p build
	$(GBDK)/bin/lcc -Wm-yc -Wm-yn"CACTUS CAT V8" -Wl-m -Wl-j -o $(ROM) src/main.c

clean:
	rm -f build/cactus-cat.*

.PHONY: all clean
