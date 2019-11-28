class ItemFormatter:
    """Formatter converting bw item lists to lists of strings for Rofi"""

    DEDUP_MARKER = '+ '

    @staticmethod
    def unique_format(items):
        """Return a list of items names, and group duplicates items by name"""

        unique = {}
        for item in items:
            arr = unique.get(item['name'], [])
            arr.append(item)
            unique[item['name']] = arr

        strings = []
        for name, arr in unique.items():
            if len(arr) == 1:
                strings.append(name)
            else:
                strings.append(
                    f"{ItemFormatter.DEDUP_MARKER}{name}")

        return "\n".join(strings)

    @staticmethod
    def group_format(items, converter):
        """
        Return a list of numbered items transformed by a converter
        """

        strings = []
        indexed = []
        index = 1
        for item in items:
            name = converter(item)
            if name is not None:
                indexed.append(item)
                strings.append(f"#{index}: {converter(item)}")
                index += 1

        return (indexed, '\n'.join(strings))


def create_converter(fields, ignore=None, delim=": ", delim2=","):
    """Return a custm converter based on fields and an ignore list"""
    def converter(item):
        values = []
        for field in fields:
            hierarchy = field.split(".")
            value = item.get(hierarchy[0])
            for level in hierarchy[1:]:
                if value is None:
                    break
                if isinstance(value, list):
                    for idx, elem in enumerate(value):
                        value[idx] = elem.get(level)
                else:
                    value = value.get(level)
                    if isinstance(value, list):
                        value = list(value)

            if value is None:
                value = 'None'

            if ignore is not None:
                if isinstance(value, list):
                    value = [elem for elem in value if elem not in ignore]
                elif value.strip() in ignore:
                    continue

            if isinstance(value, list):
                if len(value) > 0:
                    values.append(delim2.join(value))
            else:
                values.append(value)

        if len(values) <= 0:
            return None

        return delim.join(values)

    return converter
