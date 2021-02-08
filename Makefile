dev: runekit/_resources.py

dist/runekit.tar.gz: runekit/ main.py runekit/_resources.py
	poetry build -f sdist
	cd dist; cp runekit-*.tar.gz runekit.tar.gz

runekit/_resources.py: resources.qrc $(wildcard **/*.js) $(wildcard **/*.png)
	pyside2-rcc $< -o $@

.PHONY: dev
