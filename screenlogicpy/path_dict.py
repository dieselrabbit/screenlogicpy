from data import ATTR


class path_dict(dict):
    def get_data(self, *keypath, default=None):
        next = self

        def get_next(key):
            if current is None:
                return None
            if isinstance(current, dict):
                return current.get(key)
            if isinstance(current, list) and key in current:
                return current[key]
            return default

        for key in keypath:
            current = next
            next = get_next(key)
            if next is None:
                return default
        return next

    def get_name(self, *keypath, default=None):
        name_path = (*keypath, ATTR.NAME)
        return self.get_data(*name_path, default=default)

    def get_value(self, *keypath, default=None):
        value_path = (*keypath, ATTR.VALUE)
        return self.get_data(*value_path, default=default)
