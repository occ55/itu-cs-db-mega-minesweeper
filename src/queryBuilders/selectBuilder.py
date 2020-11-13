class BuiltSelectBuilder:
    def __init__(self, data, q):
        self.data = data
        self.q = q

    def Explain(self):
        print(self.q)
        return self

    def Execute(self):
        cursor = self.data["cursor"]
        cursor.execute(self.q)
        results = cursor.fetchall()
        objs = []
        for result in results:
            mainObj = {}
            for k in range(0, len(result)):
                colName = self.data["outCols"][k]
                colParts = colName.split(".")
                if colParts[0] == self.data["shid"]:
                    mainObj[colParts[1]] = result[k]
                else:
                    if not colParts[0] in mainObj:
                        mainObj[colParts[0]] = {}
                    mainObj[colParts[0]][colParts[1]] = result[k]
            objs.append(mainObj)
            print(mainObj)
        return objs


class SelectBuilder:
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

    def Limit(self, num):
        self.data["accessories"].append(f"LIMIT {num}")
        return self

    def Offset(self, num):
        self.data["accessories"].append(f"OFFSET {num}")
        return self

    def OrderBy(self, fields):
        last_list = []
        for el in fields:
            last_list.append(f"{el[0]} {el[1]}")
        self.data["accessories"].append(f"ORDER BY {', '.join(last_list)}")
        return self

    def InnerJoin(self, table, asName, cols, on):
        self.data["joins"].append({
            "table": table,
            "shid": asName,
            "cols": cols,
            "on": on
        })
        return self

    def Build(self):
        parts = []
        outCols = []
        selectParts = []
        parts.append(f'{self.data["method"]}\n')

        # Select columns
        for col in self.data["cols"]:
            colName = f'{self.data["shid"]}.{col}'
            outCols.append(colName)
            selectParts.append(f'{colName}')

        # Select columns from joins
        for join in self.data["joins"]:
            for col in join["cols"]:
                colName = f'{join["shid"]}.{col}'
                outCols.append(colName)
                selectParts.append(f'{colName}')

        selectPartsStr = ",\n".join(selectParts)
        parts.append(f'{selectPartsStr}\n')
        # From
        parts.append(f'FROM {self.data["table"]} as {self.data["shid"]}\n')

        # Joins
        for join in self.data["joins"]:
            parts.append(
                f'INNER JOIN {join["table"]} as {join["shid"]} ON {join["on"]}\n'
            )

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

        # Accessories
        for ac in self.data["accessories"]:
            parts.append(f'{ac}\n')

        self.data["outCols"] = outCols
        return BuiltSelectBuilder(self.data, "".join(parts))

    def Execute(self):
        return self.Build().Execute()


# QueryBuilder() \
#     .Select("test_a", "ta", ["id", "a", "b_id"]) \
#     .InnerJoin("test_b", "tb", ["id", "b"], "ta.b_id = tb.id") \
#     .Build() \
#     .Explain() \
#     .Execute() \
