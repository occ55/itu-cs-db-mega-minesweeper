class DeleteBuilder:
    def __init__(self, data):
        self.data = data

    def AndWhere(self, q, params={}):
        self.data["where"].append((True, q, params))
        return self

    def OrWhere(self, q, params={}):
        self.data["where"].append((False, q, params))
        return self

    def po(self):
        self.data["where"].append(0)
        return self

    def pc(self):
        self.data["where"].append(1)
        return self

    def Build(self):
        parts = []
        parts.append(f'{self.data["method"]} FROM {self.data["table"]} ')

        # Where
        if len(self.data["where"]) > 0:
            parts.append(f'WHERE ( ')
            p_oppened = True
            for w in self.data["where"]:
                if w == 0:
                    parts.append("( ")
                    p_oppened = True
                elif w == 1:
                    parts.append(") ")
                    p_oppened = False
                else:
                    # type modification
                    for key in w[2]:
                        if isinstance(w[2][key], int) or isinstance(
                                w[2][key], float):
                            w[2][key] = str(w[2][key])
                        else:
                            w[2][key] = f"'{w[2][key]}'"
                    if not p_oppened:
                        parts.append("AND " if w[0] else "OR ")
                    parts.append(f'({w[1].format(**w[2])}) ')
                    p_oppened = False
            parts.append(")\n")

        return BuiltDeleteBuilder(self.data, "".join(parts))

    def Execute(self):
        return self.Build().Execute()


class BuiltDeleteBuilder:
    def __init__(self, data, q):
        self.data = data
        self.q = q

    def Execute(self):
        cursor = self.data["cursor"]
        conn = self.data["connection"]
        cursor.execute(self.q)
        conn.commit()
        return cursor.rowcount

    def Explain(self):
        print(self.q)
        return self
