class ItemFormatter:
    DEDUP_MARKER = '+ '

    @staticmethod
    def unique_format(items, converter):
        unique = {}
        for item in items:
            arr = unique.get(item['name'], [])
            arr.append(item)
            unique[item['name']] = arr

        strings = []
        for name, arr in unique.items():
            if len(arr) == 1:
                strings.append(converter(arr[0]))
            else:
                strings.append(
                    f"{ItemFormatter.DEDUP_MARKER}{name}")

        return "\n".join(strings)

    @staticmethod
    def group_format(items, converter):
        strings = []
        index = 1
        for item in items:
            strings.append(f"#{index}: {converter(item)}")
            index += 1

        return '\n'.join(strings)


class ConverterFactory:
    @staticmethod
    def create(fields, delim=": ", delim2=","):
        def converter(item):
            values = []
            for f in fields:
                hierarchy = f.split(".")
                value = item.get(hierarchy[0])
                for h in hierarchy[1:]:
                    if value is None:
                        break
                    if isinstance(value, list):
                        for idx, v in enumerate(value):
                            value[idx] = v.get(h)
                    else:
                        value = value.get(h)
                        if isinstance(value, list):
                            value = list(value)

                if value is None:
                    value = 'None'

                if isinstance(value, list):
                    values.append(delim2.join(value))
                else:
                    values.append(value)

            return delim.join(values)

        return converter
