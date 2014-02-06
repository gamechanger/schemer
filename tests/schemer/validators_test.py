from schemer.validators import (one_of, gte, lte, gt, lt, between,
    length, match, is_email, is_url, each_item, distinct)
import unittest


class TestOneOf(unittest.TestCase):
    def test_valid(self):
        self.validator = one_of('peas', 'carrots')
        self.assertIsNone(self.validator('peas'))
        self.assertIsNone(self.validator('carrots'))

    def test_invalid(self):
        self.validator = one_of('peas', 'carrots')
        self.assertEqual(
            "'sweetcorn' is not in the list ['peas', 'carrots']",
            self.validator('sweetcorn'))

    def test_valid_array(self):
        self.validator = one_of(['peas', 'carrots'])
        self.assertIsNone(self.validator('peas'))
        self.assertIsNone(self.validator('carrots'))

    def test_invalid_array(self):
        self.validator = one_of(['peas', 'carrots'])
        self.assertEqual(
            "'sweetcorn' is not in the list ['peas', 'carrots']",
            self.validator('sweetcorn'))


class TestGte(unittest.TestCase):
    def setUp(self):
        self.validator = gte(3)

    def test_valid(self):
        self.assertIsNone(self.validator(3))
        self.assertIsNone(self.validator(4))

    def test_invalid(self):
        self.assertEqual(
            "2 is not greater than or equal to 3",
            self.validator(2))


class TestLte(unittest.TestCase):
    def setUp(self):
        self.validator = lte(3)

    def test_valid(self):
        self.assertIsNone(self.validator(3))
        self.assertIsNone(self.validator(2))

    def test_invalid(self):
        self.assertEqual(
            "4 is not less than or equal to 3",
            self.validator(4))


class TestBetween(unittest.TestCase):
    def setUp(self):
        self.validator = between(3, 5)

    def test_valid(self):
        self.assertIsNone(self.validator(3))
        self.assertIsNone(self.validator(4))
        self.assertIsNone(self.validator(5))

    def test_invalid(self):
        self.assertEqual(
            "6 is not less than or equal to 5",
            self.validator(6))

        self.assertEqual(
            "2 is not greater than or equal to 3",
            self.validator(2))


class TestGt(unittest.TestCase):
    def setUp(self):
        self.validator = gt(3)

    def test_valid(self):
        self.assertIsNone(self.validator(4))

    def test_invalid(self):
        self.assertEqual(
            "3 is not greater than 3",
            self.validator(3))


class TestLt(unittest.TestCase):
    def setUp(self):
        self.validator = lt(3)

    def test_valid(self):
        self.assertIsNone(self.validator(2))

    def test_invalid(self):
        self.assertEqual(
            "3 is not less than 3",
            self.validator(3))


class TestLen(unittest.TestCase):
    def setUp(self):
        self.validator = length(3, 5)

    def test_valid(self):
        self.assertIsNone(self.validator('abc'))
        self.assertIsNone(self.validator('abcd'))
        self.assertIsNone(self.validator('abcde'))

    def test_invalid(self):
        self.assertEqual("'ab' does not have a length of at least 3", self.validator('ab'))
        self.assertEqual("'abcdef' does not have a length of at most 5", self.validator('abcdef'))

    def test_max_length_with_keyword(self):
        validator = length(max=5)
        self.assertIsNone(validator('abcde'))
        self.assertEqual("'abcdef' does not have a length of at most 5", self.validator('abcdef'))


class TestMatch(unittest.TestCase):
    def setUp(self):
        self.validator = match("^[a-z]+$")

    def test_valid(self):
        self.assertIsNone(self.validator('abcde'))

    def test_invalid(self):
        self.assertEqual("'ABCde' does not match the pattern '^[a-z]+$'", self.validator('ABCde'))


class TestIsEmail(unittest.TestCase):
    def setUp(self):
        self.validator = is_email()

    def test_valid(self):
        self.assertIsNone(self.validator('s.balmer@hotmail.com'))

    def test_invalid(self):
        self.assertEqual(
            "'notanemail' is not a valid email address",
            self.validator("notanemail"))


class TestIsUrl(unittest.TestCase):
    def setUp(self):
        self.validator = is_url()

    def test_valid(self):
        self.assertIsNone(self.validator('http://www.github.com'))

    def test_invalid(self):
        self.assertEqual(
            "'notaurl' is not a valid URL",
            self.validator("notaurl"))


class TestEachItem(unittest.TestCase):
    def setUp(self):
        self.validator = each_item(gt(2), lt(6))

    def test_valid(self):
        self.assertIsNone(self.validator([3, 4]))

    def test_invalid(self):
        self.assertEqual(
            "6 is not less than 6",
            self.validator([3, 6]))


class TestDistinct(unittest.TestCase):
    def setUp(self):
        self.validator = distinct()

    def test_valid(self):
        self.assertIsNone(self.validator([1, 2, 3]))

    def test_invalid(self):
        self.assertEqual(
            "[2, 2, 3] is not a distinct set of values",
            self.validator([2, 2, 3]))
