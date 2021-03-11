PREFIX ?= ~/.local

all:
	@echo Run \'make install\' to install backr2 to ~/.local/bin

install:
	@mkdir -p $(PREFIX)/bin
	@cp -p backr2.py $(PREFIX)/bin/backr2.py

uninstall:
	@rm -rf $(DESTDIR)$(PREFIX)/bin/backr2.py
