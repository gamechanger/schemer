import re
from pprint import pformat

def e(string, *args):
    """Function which formats error messages."""
    return string.format(*[pformat(arg) for arg in args])

def one_of(*args):
    """
    Validates that a field value matches one of the values
    given to this validator.
    """
    if len(args) == 1 and isinstance(args[0], list):
        items = args[0]
    else:
        items = list(args)

    def validate(value):
        if not value in items:
            return e("{} is not in the list {}", value, items)
    return validate


def gte(min_value):
    """
    Validates that a field value is greater than or equal to the
    value given to this validator.
    """
    def validate(value):
        if value < min_value:
            return e("{} is not greater than or equal to {}", value, min_value)
    return validate


def lte(max_value):
    """
    Validates that a field value is less than or equal to the
    value given to this validator.
    """
    def validate(value):
        if value > max_value:
            return e("{} is not less than or equal to {}", value, max_value)
    return validate


def gt(gt_value):
    """
    Validates that a field value is greater than the
    value given to this validator.
    """
    def validate(value):
        if value <= gt_value:
            return e("{} is not greater than {}", value, gt_value)
    return validate


def lt(lt_value):
    """
    Validates that a field value is less than the
    value given to this validator.
    """
    def validate(value):
        if value >= lt_value:
            return e("{} is not less than {}", value, lt_value)
    return validate


def between(min_value, max_value):
    """
    Validates that a field value is between the two values
    given to this validator.
    """
    def validate(value):
        if value < min_value:
            return e("{} is not greater than or equal to {}",
                value, min_value)
        if value > max_value:
            return e("{} is not less than or equal to {}",
                value, max_value)
    return validate


def length(min=None, max=None):
    """
    Validates that a field value's length is between the bounds given to this
    validator.
    """

    def validate(value):
        if min and len(value) < min:
            return e("{} does not have a length of at least {}", value, min)
        if max and len(value) > max:
            return e("{} does not have a length of at most {}", value, max)
    return validate


def match(pattern):
    """
    Validates that a field value matches the regex given to this validator.
    """
    regex = re.compile(pattern)

    def validate(value):
        if not regex.match(value):
            return e("{} does not match the pattern {}", value, pattern)
    return validate

def is_email():
    """
    Validates that a fields value is a valid email address.
    """

    email = (
        ur'(?!^\.)'     # No dot at start
        ur'(?!.*\.@)'   # No dot before at sign
        ur'(?!.*@\.)'   # No dot after at sign
        ur'(?!.*\.$)'   # No dot at the end
        ur'(?!.*\.\.)'  # No double dots anywhere
        ur'^\S+'        # Starts with one or more non-whitespace characters
        ur'@'           # Contains an at sign
        ur'\S+$'        # Ends with one or more non-whitespace characters
    )

    regex = re.compile(email, re.IGNORECASE | re.UNICODE)

    def validate(value):
        if not regex.match(value):
            return e("{} is not a valid email address", value)
    return validate

def is_url():
    """
    Validates that a fields value is a valid URL.
    """
    # Stolen from Django
    regex = re.compile(
        r'^(?:http|ftp)s?://' # http:// or https://
        r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+(?:[A-Z]{2,6}\.?|[A-Z0-9-]{2,}\.?)|' #domain...
        r'localhost|' #localhost...
        r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})' # ...or ip
        r'(?::\d+)?' # optional port
        r'(?:/?|[/?]\S+)$', re.IGNORECASE)

    def validate(value):
        if not regex.match(value):
            return e("{} is not a valid URL", value)
    return validate


def each_item(*validators):
    """
    A wrapper which applies the given validators to each item in a field
    value of type `list`.

    Example usage in a Schema:

    "my_list_field": {"type": Array(int), "validates": each_item(lte(10))}
    """
    def validate(value):
        for item in value:
            for validator in validators:
                error = validator(item)
                if error:
                    return error
        return None
    return validate


def distinct():
    """
    Validates that all items in the given field list value are distinct,
    i.e. that the list contains no duplicates.
    """
    def validate(value):
        for i, item in enumerate(value):
            if item in value[i+1:]:
                return e("{} is not a distinct set of values", value)
    return validate

