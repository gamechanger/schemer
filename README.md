# Schemer

Schemer is lightweight library for declaratively creating schemas for Python dicts.

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

Schemer allows you to declaratively express the a desired structure and contraints of a Python dict in a reusable Schema which itself is declared as a Python dict.

Schemas can then be used to validate specific dict instances and apply default values to them where appropriate.

Schemas can be easily nested within one another providing powerful composability of document structures.

Though Schemer was originally designed to validate Mongo documents and was extracted from [Mongothon](http://github.com/gamechanger/mongothon), it is completely agnostic of use case.

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

Validate a dict
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

Each field in a schema must be given a type by adding a `"type"` key to the field spec dict. For example, this schema declares a single `"name"` field with a type of `basestring`:
```python
schema = Schema({"name": {"type": basestring}})
```
The `"type"` can be any Python `type` which responds to `instanceof()`, or another `Schema` for schema-nesting (see below).

#### The "Mixed" type
The `Mixed` type allows you to indicate that a field supports values of multiple types.

```python
schema = Schema({"external_id": {"type": Mixed(basestring, int)}})  # only basestring, int and ObjectId are supported
```

If you attempt to save a model containing a value of the wrong type for a given a field a `ValidationException` will be thrown.

### Mandatory fields
You can require a field to be present in a document by adding `"required": True` to the Schema:
```python
schema = Schema({"name": {"type": basestring, "required": True}})
```
By default all fields are _not_ required.


### Defaults
Schemas allow you to specify default values for fields which may be applied in the event a value is not provided in a given document.
A default can either be specified as literal:
```python
schema = Schema({"num_wheels": {"type": int, "default": 4}})
```
or as a reference to parameterless function which will be called at the point the document is saved:
```python
import datetime
schema = Schema({"created_date": {"type": datetime, "default": datetime.now}})
```
Defaults can be applied to a given document by using the `apply_defaults()` method:
```python
schema = Schema({"num_wheels": {"type": int, "default": 4}})
car = {}
schema.apply_defaults(car)
assert car == {"num_wheels": 4}
```


### Validation
Schemer allows you to specify validation for a field using the `"validates"` key in the field spec.
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
```python
# Validator                         # Validates that the field...
gte(value)                          # is greater than or equal to the given value
lte(value)                          # is less than or equal to the given value
gt(value)                           # is greater than the given value
lt(value)                           # is less than the given value
between(min_value, max_value)       # is between the given min and max values
length(min_length, [max_length])    # is at least the given min length and (optionally) at most the given max length
match(pattern)                      # matches the given regex pattern
one_of(values...)                   # is equal to one of the given values
is_url()                            # is a valid URL
is_email()                          # is a valid email address
```

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

### Nested schemas
Schemas may be nested within one another in order to describe the structure of documents containing deep graphs.

Nested can either be declared inline:
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


### Embedded collections
As well as nesting schemas directly under fields, Schemer supports embedded collections within documents. To declare an embedded collection, simply declare the type of the embedded items using Python list syntax:
```python
line_item_schema = Schema({
    "price":        {"type": int, "required": True}
    "item_name":    {"type": basestring, "required": True}
})

order_schema = Schema({
    "line_items":   [line_item_schema]
    "total_due":    {"type": int}
})
```
Simple primitive types can be embedded as well as full schemas:
```python
bookmark_schema = Schema({
    "url":      {"type": basestring},
    "tags":     [basestring]
})
```

# Developing and Contributing

To run Schemer's tests, simply run `python setup.py nosetests` at the command line.

All contributions submitted as GitHub pull requests are warmly received.
