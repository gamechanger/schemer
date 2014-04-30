"""Provides a valid sample set of schemas and documents adhereing to those
schemas for use in testing."""

from schemer import Schema, Mixed, Array
from schemer.validators import one_of, length
from datetime import datetime


def stubnow():
    return datetime(2012, 4, 5)

name_schema = Schema({
    "first":    {"type": basestring, "required": True},
    "last":     {"type": basestring, "required": True}
})

# TEST SCHEMAS
comment_schema = Schema({
    "commenter":    {"type": name_schema, "required": True},
    "email":        {"type": basestring, "required": False},
    "comment":      {"type": basestring, "required": True},
    "votes":        {"type": int, "default": 0}
})

blog_post_schema = Schema({
    "author":           {"type": name_schema, "required": True},
    "content":          {"type": Schema({
        "title":            {"type": basestring, "required": True},
        "text":             {"type": basestring, "required": True},
        "page_views":       {"type": int, "default": 1}
    }), "required": True},
    "category":         {"type": basestring, "validates": one_of("cooking", "politics")},
    "comments":         {"type": Array(comment_schema), "required": True},
    "likes":            {"type": int, "default": 0},
    "creation_date":    {"type": datetime, "default": stubnow},
    "tags":             {"type": Array(basestring), "default": ["blog"], "validates": length(1)},
    "misc":             {"type": Mixed(basestring, int)},
    "linked_id":        {"type": Mixed(int, basestring)},
    "external_code":    {"type": basestring, "nullable": False}
})


def valid_doc(overrides=None):
    doc = {
        "author": {
            "first":    "John",
            "last":     "Humphreys"
        },
        "content": {
            "title": "How to make cookies",
            "text": "First start by pre-heating the oven..."
        },
        "category": "cooking",
        "comments": [
            {
                "commenter": {
                    "first": "Julio",
                    "last": "Cesar"
                },
                "email": "jcesar@test.com",
                "comment": "Great post dude!"
            },
            {
                "commenter": {
                    "first": "Michael",
                    "last": "Andrews"
                },
                "comment": "My wife loves these."
            }
        ],
        "tags": ["cookies", "recipe", "yum"],
        "external_code": "ABC123"
    }
    if overrides:
        doc.update(overrides)
    return doc

