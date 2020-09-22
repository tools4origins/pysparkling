from pysparkling.sql.expressions.expressions import Expression


class Literal(Expression):
    def __init__(self, value):
        super(Literal, self).__init__()
        self.value = value

    def eval(self, row, schema):
        return self.value

    def __str__(self):
        if self.value is True:
            return "true"
        if self.value is False:
            return "false"
        if self.value is None:
            return "NULL"
        return str(self.value)


__all__ = ["Literal"]
