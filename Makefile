dist/runekit.tar.gz: runekit/ main.py
	poetry build -f sdist
	cd dist; cp runekit-*.tar.gz runekit.tar.gz

.PHONY: flatpak
