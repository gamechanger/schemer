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

about_schema = Schema({
    "first_name": {"type": basestring, "required": True},
    "last_name": {"type": basestring, "required": True},
    "birth_year": {"type": int, "required": True},
    "birth_month": {"type": int, "required": True},
    "birth_day": {"type": int, "required": True}
})

def get_author_schema(document):
    if document.get("first_name"):
        return about_schema
    else:
        return name_schema

website_schema = Schema({
    "url": {"type": basestring, "required": True},
    "name": {"type": basestring, "required": True}
})

def get_website_schema(document):
    if isinstance(document, list):
        return Array(website_schema)
    elif isinstance(document, dict):
        return website_schema
    return basestring

blog_post_schema = Schema({
    "author":           {"type": get_author_schema, "required": True},
    "content":          {"type": Schema({
        "title":            {"type": basestring, "required": True},
        "text":             {"type": basestring, "required": True},
        "page_views":       {"type": int, "default": 1}
    }), "required": True},
    "meta":             {"type": Schema({
        "last_edited":      {"type": datetime}
    }), "required": True, "nullable": True},
    "category":         {"type": basestring, "validates": one_of("cooking", "politics")},
    "comments":         {"type": Array(comment_schema), "required": True},
    "likes":            {"type": int, "default": 0},
    "creation_date":    {"type": datetime, "default": stubnow},
    "tags":             {"type": Array(basestring), "default": ["blog"], "validates": length(1)},
    "misc":             {"type": Mixed(basestring, int)},
    "linked_id":        {"type": Mixed(int, basestring)},
    "external_code":    {"type": basestring, "nullable": False},
    "website":          {"type": get_website_schema},
    "editors":          {"type": Array(lambda document: name_schema if isinstance(document, dict) else basestring)}
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
        "meta": None,
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
        "external_code": "ABC123",
        "website": {
            "url": "johnhumphreys.tumblr.com",
            "name": "John's Cooking Blog"
        }
    }
    if overrides:
        doc.update(overrides)
    return doc

