dev: runekit/_resources.py

dist/runekit.tar.gz: main.py poetry.lock $(wildcard runekit/**/*)
	poetry build -f sdist
	cd dist; cp runekit-*.tar.gz runekit.tar.gz

runekit/_resources.py: resources.qrc $(wildcard runekit/**/*.js) $(wildcard runekit/**/*.png)
	pyside2-rcc $< -o $@

dist/RuneKitApp.app: main.py poetry.lock $(wildcard runekit/**/*)
	pyinstaller -w -n RuneKitApp \
		--exclude-module tkinter \
		-s -d noarchive \
		--osx-bundle-identifier de.cupco.runekit \
		$<

.PHONY: dev
