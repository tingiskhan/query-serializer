import unittest
from query_serializer import QueryBuilder
from test.model import Task
from datetime import date


class QueryTest(unittest.TestCase):
    def test_QueryToString(self):
        qb = QueryBuilder(Task)

        expr = Task.name == "Test"

        expected = "(name eq \"Test\")"
        as_string = qb.to_string(expr)

        self.assertEqual(expected, as_string)

    def test_QueryToStringMultipleFiltration(self):
        qb = QueryBuilder(Task)

        date_ = date.today()
        expr = (Task.name == "Test") & (Task.finished_by < date_)

        expected = f"((name eq \"Test\") and (finished_by lt {date_:%Y-%m-%d}))"
        as_string = qb.to_string(expr)

        self.assertEqual(expected, as_string)

    def test_QueryFromString(self):
        qb = QueryBuilder(Task)
        expr = (Task.name == "Test")

        as_string = qb.to_string(expr)
        from_string = qb.string_to_filters(as_string)

        expected = [{"field": "name", "op": "eq", "value": "Test"}]

        self.assertEqual(expected, from_string)

    def test_QueryFromStringMultiple(self):
        qb = QueryBuilder(Task)

        date_ = date.today()
        expr = (Task.name == "Test") & (Task.finished_by < date_)

        as_string = qb.to_string(expr)
        from_string = qb.string_to_filters(as_string)

        expected = [
            {
                "and": [
                    {"field": "name", "op": "eq", "value": "Test"},
                    {"field": "finished_by", "op": "lt", "value": date_}
                ]
            }
        ]

        self.assertEqual(expected, from_string)

    def test_QueryEvenMoreStuff(self):
        qb = QueryBuilder(Task)

        date_ = date.today()
        expr = (Task.name == "Test") & (Task.finished_by < date_) | (Task.name == "Test2")

        as_string = qb.to_string(expr)
        from_string = qb.string_to_filters(as_string)

        expected = [
            {
                "or": [
                    {
                        "and": [
                            {"field": "name", "op": "eq", "value": "Test"},
                            {"field": "finished_by", "op": "lt", "value": date_}
                        ]},
                    {"field": "name", "op": "eq", "value": "Test2"}
                ],
            }
        ]

        self.assertEqual(expected, from_string)


if __name__ == '__main__':
    unittest.main()
