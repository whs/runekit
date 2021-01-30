class ClassDict(dict[type]):
    def __getitem__(self, item):
        for key, value in self.items():
            if isinstance(item, key):
                return value

        raise KeyError
