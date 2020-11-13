class InsertBuilder:
    def __init__(self, data):
        self.data = data

    def Build(self):
        parts = []
        parts.append(f'{self.data["method"]} {self.data["table"]}(')
        keyParts = []
        valParts = []
        values = self.data["values"]
        for key in values:
            if isinstance(values[key], int) or isinstance(values[key], float):
                values[key] = str(values[key])
            else:
                values[key] = f"'{values[key]}'"

        for key in values:
            keyParts.append(key)
        parts.append(f'{",".join(keyParts)}) VALUES (')
        for key in values:
            valParts.append(values[key])
        parts.append(f'{",".join(valParts)}) ')

        if self.data["retId"]:
            parts.append(f'RETURNING id')
        return BuiltInsertBuilder(self.data, "".join(parts))

    def Execute(self):
        return self.Build().Execute()


class BuiltInsertBuilder:
    def __init__(self, data, q):
        self.data = data
        self.q = q

    def Execute(self):
        cursor = self.data["cursor"]
        conn = self.data["connection"]
        cursor.execute(self.q)
        conn.commit()
        if self.data["retId"]:
            val = cursor.fetchall()[0][0]
            return val
        else:
            return None

    def Explain(self):
        print(self.q)
        return self
