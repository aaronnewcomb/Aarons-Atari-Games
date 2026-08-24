PROJECT := octo-game
BUILD_DIR := build
ROM := $(BUILD_DIR)/$(PROJECT).a26
LISTING := $(BUILD_DIR)/$(PROJECT).lst
SYMBOLS := $(BUILD_DIR)/$(PROJECT).sym
SOURCE := src/main.asm
TITLE_SCENE := src/title_scene.inc
INCLUDES := resources/includes/vcs.h resources/includes/macro.h
LOCAL_DASM := resources/tools/dasm-2.20.17/dasm

ifeq ($(wildcard $(LOCAL_DASM)),)
DASM ?= dasm
else
DASM ?= $(LOCAL_DASM)
endif

.PHONY: all verify rominfo run clean help

all: $(ROM) verify

$(BUILD_DIR):
	mkdir -p $(BUILD_DIR)

$(ROM): $(SOURCE) $(TITLE_SCENE) $(INCLUDES) | $(BUILD_DIR)
	$(DASM) $(SOURCE) -f3 -v0 -Iresources/includes -o$(ROM) -l$(LISTING) -s$(SYMBOLS)

verify: $(ROM)
	python3 scripts/verify_rom.py $(ROM)

rominfo: all
	@if command -v stella >/dev/null 2>&1; then \
		stella -rominfo $(ROM); \
	else \
		python3 scripts/run_bundled_stella.py -rominfo $(ROM); \
	fi

run: all
	@if command -v stella >/dev/null 2>&1; then \
		stella -audio.enabled 1 $(ROM); \
	else \
		python3 scripts/run_bundled_stella.py \
			-basedir $(BUILD_DIR)/stella-config \
			-userdir $(BUILD_DIR)/stella-user \
			-audio.enabled 1 \
			$(ROM); \
	fi

clean:
	find $(BUILD_DIR) -maxdepth 1 -type f ! -name .gitkeep -delete

help:
	@echo "make        Build and verify the 4 KiB ROM"
	@echo "make rominfo  Inspect the ROM with Stella"
	@echo "make run    Build and launch Octo Game in Stella"
	@echo "make clean  Remove generated build files"
