# Schemer

Powerful schema-based validation of Python dicts.

[![build status](https://travis-ci.org/gamechanger/schemer.png?branch=master "Build status")](https://travis-ci.org/gamechanger/schemer)

# Installation

Install via easy_install:
```
easy_install schemer
```
Or, via pip:
```
pip install schemer
```

# Getting Started

Schemer allows you to declaratively express the desired structure and contraints of a Python dict in a reusable Schema which itself is declared as a Python dict.

Schemas can then be used to validate specific `dict` instances and apply default values to them where appropriate.

Schemas can be easily nested within one another providing powerful composability of document structures.

Though Schemer was originally designed to validate Mongo documents and was extracted from [Mongothon](http://github.com/gamechanger/mongothon), it is now completely agnostic of use case.

## Example

This is how simple it is to declare a Schema:
```python
car_schema = Schema({
    "make":         {"type": basestring, "required": True},
    "model":        {"type": basestring, "required": True},
    "num_wheels":   {"type": int,        "default": 4, "validates": gte(0)}
    "color":        {"type": basestring, "validates": one_of("red", "green", "blue")}
})
```

Once you have your schema you can use it to validate a dict:
```python
car = {
    "make":         "Ford",
    "model":        "F-150",
    "num_wheels":   -1
    "color":        "red"
}

try:
    car_schema.validate(car)
except ValidationException:
    # num_wheels should be >= 0

```

# API Reference

## Schemas

### Types

Each field in a schema must be given a type by adding a `"type"` key to the field spec `dict`. For example, this schema declares a single `"name"` field with a type of `basestring`:
```python
schema = Schema({"name": {"type": basestring}})
```
The `"type"` can be any Python `type` which responds to `isinstance()`, another `Schema` for schema-nesting (see below), or a `function` which will create dynamic schema (see below).

#### The "Mixed" type
The `Mixed` type allows you to indicate that a field supports values of multiple types.

```python
schema = Schema({"external_id": {"type": Mixed(basestring, int)}})  # only basestring, int and ObjectId are supported
```

When you validate a `dict` containing a value of the wrong type for a given a field a `ValidationException` will be thrown describing the error.

### Mandatory fields
You can require a field to be present in a `dict` by adding `"required": True` to the Schema:
```python
schema = Schema({"name": {"type": basestring, "required": True}})
```
By default all fields are _not_ required.


### Nested schemas
Schemas may be nested within one another in order to describe the structure of `dict`s containing deep graphs.

Nested schemas can either be declared inline:
```python
blog_post_schema = Schema({
    "author":   {"type": Schema({
        "first_name": {"type": basestring},
        "last_name": {"type": basestring}})},
    "title":    {"type": basestring},
    "content":  {"type": basestring}
})

```
or declared in isolation and then referenced (and potentially reused between multiple parent schemas):
```python
name_schema = Schema({
    "first_name":   {"type": basestring},
    "last_name":    {"type": basestring}
})

blog_post_schema = Schema({
    "author":   {"type": name_schema},
    "title":    {"type": basestring},
    "content":  {"type": basestring}
})

comment_schema = Schema({
    "author":   {"type": name_schema, "required":True},
    "comment":  {"type": base_string}
})

```
In each case the nested schema is provided as the `type` parameter in the parent field's spec and can be declared as `"required"=True` if so desired. Any validation present within the nested schema is applied wherever the schema
is used.


### Embedded arrays
As well as nesting schemas directly under fields, Schemer supports embedding `list`s within `dict`s. To declare an embedded array, simply set the `type` of the field to `Array` providing the type of entries
in the array as an init arg:
```python
line_item_schema = Schema({
    "price":        {"type": int, "required": True}
    "item_name":    {"type": basestring, "required": True}
})

order_schema = Schema({
    "line_items":   {"type": Array(line_item_schema)}
    "total_due":    {"type": int}
})
```
Simple primitive types can be embedded as well as full schemas:
```python
bookmark_schema = Schema({
    "url":      {"type": basestring},
    "tags":     {"type": Array(basestring)}
})
```
Just like other fields, embedded arrays can have defaults (see below):
```python
bookmark_schema = Schema({
    "url":      {"type": basestring},
    "tags":     {"type": Array(basestring), "default": []}
})
```
...and validation (see below):
```python
bookmark_schema = Schema({
    "url":      {"type": basestring},
    "tags":     {"type": Array(basestring), "validates":[each_item(length(min=1)),
                                                         distinct()]}
})
```

### Dynamic Types
Sometimes it becomes necessary to set the expected type for a given field dynamically at validation-time, based on the content of a given document.

For this purpose, Schemer allows you to specify a function for a given field's `'type'` specification. The given function will be called at validation time with a single argument - the sub-document, of the document being validated, keyed off of the field. The dynamic type function should return the `type` against which the given field value should be validated. This can be a simple Python type, or a `Schema` or `Array`.

Consider the following example:

```python
uk_address_schema = Schema({
    'recipient': {'type': basestring, 'required': True},
    'floor_apartment': {'type': basestring, 'required': False},
    'building': {'type': basestring, 'required': False},
    'house_number': {'type': int,  'required': False},
    'dependent_locality': {'type': basestring, 'required': False},
    'localitly': {'type': basestring, 'required': True},
    'postal_code': {'type': basestring, 'required': True},
    'country': {'type': basestring, 'required': True}
})

usa_address_schema = Schema({
    'recipient': {'type': basestring, 'required': True},
    'house_number_street_name': {'type': int,  'required': True},
    'floor_apartment': {'type': basestring, 'required': False},
    'localitly_province_postalcode': {'type': basestring, 'required': True},
    'country': {'type': basestring, 'required': True}
})

canada_address_schema = Schema({
    'recipient': {'type': basestring, 'required': True},
    'house_number_street_name': {'type': basestring, 'required': True},
    'street_direction': {'type': basestring, 'required': False},
    'locality_province_postalcode': {'type': basestring, 'required': True},
    'country': {'type': basestring, 'required': True}
})

def get_address_schema(document):
    country = document.get('country')
    if country == 'uk':
        return uk_address_schema
    elif country == 'usa':
        return usa_address_schema
    else:
        return canada_address_schema

user_account_schema = Schema({
    'first_name': {'type': basestring, 'required': True},
    'last_name': {'type': basestring, 'required': True},
    'age': {'type': int, 'required': True},
    'address': {'type': get_address_schema, 'required': True}
})

```
In this instance, dynamic types allow us to specify a single `'address'` field on the `user_account_schema`, but validate against one of multiple potential address schemas depending on the country we've set in any given document's address.

Important Note:
Bear in mind that using dynamic type functions in this way effectively defers the verification that the Schema's structure is itself valid until document validation time. So you're giving up a certain amount of control for the sake of flexibility.

### Defaults
Schemas allow you to specify default values for fields which may be applied to a given document.
A default can either be specified as literal:
```python
schema = Schema({"num_wheels": {"type": int, "default": 4}})
```
or as a reference to parameterless function which will be called at the point the default is applied:
```python
import datetime
schema = Schema({"created_date": {"type": datetime, "default": datetime.utcnow}})
```
Defaults can be applied to a given document by using the `apply_defaults()` method:
```python
schema = Schema({"num_wheels": {"type": int, "default": 4}})
car = {}
schema.apply_defaults(car)
assert car == {"num_wheels": 4}
```


### Validation
Schemer allows you to specify further validation for a field using the `"validates"` key in the field spec.
You can specify a single validator:
```python
schema = Schema({"color": {"type": basestring, "validates": one_of("red", "green", "blue")}})
```
or multiple validators:
```python
schema = Schema({"num_wheels": {"type": int, "validates": [gte(0), lte(6)]}})
```


#### Provided validators
Schemer provides the following validators out-of-the-box:

| Validator                           | Works with type(s)              | Validates the field... |
| ----------------------------------- | ------------------------------- |----------------------- |
| `gte(value)`                        | Any                             | is greater than or equal to the given value |
| `lte(value)`                        | Any                             | is less than or equal to the given value |
| `gt(value)`                         | Any                             | is greater than the given value |
| `lt(value)`                         | Any                             | is less than the given value |
| `between(min_value, max_value)`     | Any                             | is between the given min and max values |
| `length(min_length, [max_length])`  | Sequence types (`str`, `list`, etc) | is at least the given min length and (optionally) at most the given max length |
| `match(pattern)`                    | `basestring`, `str`, `unicode`        | is matches the given regex pattern |
| `one_of(*values)`                   | `basestring`, `str`, `unicode`        | is equal to one of the given values |
| `is_url()`                          | `basestring`, `str`, `unicode`        | is a valid URL |
| `is_email()`                        | `basestring`, `str`, `unicode`        | is a valid email address |
| `distinct()`                        | `list`                            | contains distinct values |
| `each_item(*validators)`            | `list`                           | by validating each contained item with the given validators. |


#### Creating custom validators
In addition to the provided validators it's easy to create your own custom validators.
To create a custom validator:
 - declare a function which accepts any arguments you want to provide to the validation algorithm
 - the function should itself return a function which will ultimately be called by Schemer when validating a field value. The function should:
    - accept a single argument - the field value being validated
    - return nothing if the given value is valid
    - return a string describing the validation error if the value is invalid

Here's the declaration of an example custom validator:
```python
def startswith(prefix):
    def validate(value):
        if not value.startswith(prefix):
            return "String must start with %s" % prefix

# Usage:
schema = Schema({"full_name": {"type": basestring, "validates": startswith("Mr")}})
```

## Validating `dict`s

To validate a given dict, using all the constraints of the schema as described above, simply call `validate()` on the `Schema` passing the `dict` to test:

```python
schema.validate(mydict)
```

If the `dict` is found to be valid then this call will return without issue. If the dict is found to be invalid then a `ValidationException` will be thrown. This exception can be inspected for details of the failures:

```python
try:
    schema.validate(my_dict)
except ValidationException, e:
    for path, error in e.errors.iteritems():
        print "Error found for {}: {}".format(path, error)
```

# Developing and Contributing

To run Schemer's tests, simply run `python setup.py nosetests` at the command line.

All contributions submitted as GitHub pull requests are warmly received.
