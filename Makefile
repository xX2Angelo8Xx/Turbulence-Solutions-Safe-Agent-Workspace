# Makefile — Agent Environment Launcher (INS-026)
#
# Targets
#   install-macos    Install from source on macOS into ~/.local/share/TurbulenceSolutions/
#   update-macos     Pull latest changes and re-install
#   uninstall-macos  Print manual uninstall instructions (non-destructive automation)
#
# Usage:
#   make install-macos
#   make update-macos
#   make uninstall-macos

SHELL := /usr/bin/env bash

INSTALL_SCRIPT := scripts/install-macos.sh
INSTALL_BASE   := $(HOME)/.local/share/TurbulenceSolutions
VENV_DIR       := $(INSTALL_BASE)/venv
VENV_PYTHON    := $(VENV_DIR)/bin/python

.PHONY: install-macos update-macos uninstall-macos

install-macos:
	@echo "==> Running macOS source install..."
	@bash $(INSTALL_SCRIPT)

update-macos:
	@echo "==> Pulling latest changes..."
	@git pull
	@echo "==> Re-installing package..."
	@$(VENV_PYTHON) -m pip install . --quiet
	@echo "==> Update complete."

uninstall-macos:
	@echo ""
	@echo "To uninstall, run the following commands manually:"
	@echo ""
	@echo "  rm -rf $(INSTALL_BASE)"
	@echo ""
	@echo "Then remove the PATH line from your shell profile (~/.zshrc or ~/.bashrc)."
	@echo ""
	@echo "This Makefile target does NOT delete files automatically to prevent"
	@echo "accidental data loss. Please run the commands above yourself."
	@echo ""
