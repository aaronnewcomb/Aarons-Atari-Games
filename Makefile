.PHONY: all octo-game octo-game-manual clean help

all: octo-game

octo-game:
	$(MAKE) -C games/octo-game

octo-game-manual:
	$(MAKE) -C games/octo-game manual

clean:
	$(MAKE) -C games/octo-game clean

help:
	@echo "make                  Build all games"
	@echo "make octo-game        Build and verify Octo Game"
	@echo "make octo-game-manual Rebuild the Octo Game manual PDF"
	@echo "make clean            Remove generated game build files"
