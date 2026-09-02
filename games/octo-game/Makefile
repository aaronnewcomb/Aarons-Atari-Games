PROJECT := octo-game
BUILD_DIR := build
ROM := $(BUILD_DIR)/$(PROJECT).a26
FINAL_ROM := $(BUILD_DIR)/$(PROJECT)-title-stage6-music-8k.a26
LISTING := $(BUILD_DIR)/$(PROJECT).lst
SYMBOLS := $(BUILD_DIR)/$(PROJECT).sym
SOURCE := src/main.asm
TITLE_SCENE := src/title_scene.inc
INCLUDES := resources/includes/vcs.h resources/includes/macro.h
LOCAL_DASM := $(firstword $(wildcard resources/tools/dasm-2.20.17/dasm ../../resources/tools/dasm-2.20.17/dasm))

ifeq ($(wildcard $(LOCAL_DASM)),)
DASM ?= dasm
else
DASM ?= $(LOCAL_DASM)
endif

.PHONY: all release-rom legacy-4k verify rominfo run manual title-stage1-8k title-stage2-8k title-stage3-8k title-stage4-8k title-stage5-8k title-stage6-8k title-stage6-music-8k clean help

all: release-rom verify

$(BUILD_DIR):
	mkdir -p $(BUILD_DIR)

legacy-4k: $(SOURCE) $(TITLE_SCENE) $(INCLUDES) | $(BUILD_DIR)
	$(DASM) $(SOURCE) -f3 -v0 -Iresources/includes -o$(ROM) -l$(LISTING) -s$(SYMBOLS)

release-rom: | $(BUILD_DIR)
	python3 scripts/build_title_stage6_music_8k.py
	cp $(FINAL_ROM) $(ROM)

verify:
	python3 scripts/verify_rom.py $(ROM)

title-stage1-8k:
	python3 scripts/build_title_stage1_8k.py
	@python3 -c 'from pathlib import Path; p=Path("build/octo-game-title-stage1-8k.a26"); d=p.read_bytes(); assert len(d)==8192; print(f"verified {p}: {len(d)} bytes, F8 bank pair")'

title-stage2-8k:
	python3 scripts/build_title_stage2_8k.py
	@python3 -c 'from pathlib import Path; p=Path("build/octo-game-title-stage2-8k.a26"); d=p.read_bytes(); assert len(d)==8192; print(f"verified {p}: {len(d)} bytes, F8 bank pair")'

title-stage3-8k:
	python3 scripts/build_title_stage3_8k.py
	@python3 -c 'from pathlib import Path; p=Path("build/octo-game-title-stage3-8k.a26"); d=p.read_bytes(); assert len(d)==8192; print(f"verified {p}: {len(d)} bytes, F8 bank pair")'

title-stage4-8k:
	python3 scripts/build_title_stage4_8k.py
	@python3 -c 'from pathlib import Path; p=Path("build/octo-game-title-stage4-8k.a26"); d=p.read_bytes(); assert len(d)==8192; print(f"verified {p}: {len(d)} bytes, F8 bank pair")'

title-stage5-8k:
	python3 scripts/build_title_stage5_8k.py
	@python3 -c 'from pathlib import Path; p=Path("build/octo-game-title-stage5-8k.a26"); d=p.read_bytes(); assert len(d)==8192; print(f"verified {p}: {len(d)} bytes, F8 bank pair")'

title-stage6-8k:
	python3 scripts/build_title_stage6_8k.py
	@python3 -c 'from pathlib import Path; p=Path("build/octo-game-title-stage6-8k.a26"); d=p.read_bytes(); assert len(d)==8192; print(f"verified {p}: {len(d)} bytes, F8 bank pair")'

title-stage6-music-8k:
	python3 scripts/build_title_stage6_music_8k.py
	@python3 -c 'from pathlib import Path; p=Path("build/octo-game-title-stage6-music-8k.a26"); d=p.read_bytes(); assert len(d)==8192; print(f"verified {p}: {len(d)} bytes, F8 bank pair")'

rominfo: all
	@command -v stella >/dev/null 2>&1 || { echo "Stella is not installed"; exit 1; }
	stella -rominfo $(ROM)

run: all
	@command -v stella >/dev/null 2>&1 || { echo "Stella is not installed"; exit 1; }
	stella -audio.enabled 1 $(ROM)

manual:
	python3 scripts/build_manual.py

clean:
	find $(BUILD_DIR) -maxdepth 1 -type f ! -name .gitkeep -delete

help:
	@echo "make        Build and verify the release 8 KiB F8 ROM"
	@echo "make legacy-4k  Build the preserved 4 KiB gameplay checkpoint"
	@echo "make rominfo  Inspect the ROM with Stella"
	@echo "make title-stage1-8k  Build the clean-room stage 1 O title"
	@echo "make title-stage2-8k  Add white CTO and G to the verified stage 1 title"
	@echo "make title-stage3-8k  Add the coral-filled A to the verified stage 2 title"
	@echo "make title-stage4-8k  Add the white M to the verified stage 3 title"
	@echo "make title-stage5-8k  Add the striped E to the verified stage 4 title"
	@echo "make title-stage6-8k  Complete the lower title scene and footer"
	@echo "make title-stage6-music-8k  Restore music without changing stage-6 graphics"
	@echo "make run    Build and launch Octo Game in Stella"
	@echo "make manual Rebuild docs/manual.pdf and its page images"
	@echo "make clean  Remove generated build files"
