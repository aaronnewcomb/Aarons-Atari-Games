.PHONY: all octo-game clean help

all: octo-game

octo-game:
	$(MAKE) -C games/octo-game

clean:
	$(MAKE) -C games/octo-game clean

help:
	@echo "make                  Build all games"
	@echo "make octo-game        Build and verify Octo Game"
	@echo "make clean            Remove generated game build files"
