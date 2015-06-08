from schemer import Schema, Array
from schemer.exceptions import ValidationException, SchemaFormatException
from schemer.validators import one_of, lte, gte, length
import unittest
from mock import patch
from datetime import datetime
from sample import blog_post_schema, stubnow, valid_doc


class TestSchemaVerification(unittest.TestCase):

    def assert_spec_invalid(self, spec, path):
        for strict in [True, False]:
            with self.assertRaises(SchemaFormatException) as cm:
                Schema(spec, strict)
            self.assertEqual(path, cm.exception.path)

    def test_requires_field_spec_dict(self):
        self.assert_spec_invalid({"author": 45}, 'author')

    def test_missing_type(self):
        self.assert_spec_invalid({"author": {}}, 'author')

    def test_type_can_be_a_type(self):
        Schema({"author": {'type': str}})

    def test_type_can_be_another_schema(self):
        Schema({"author": {'type': Schema({
                    'first': {'type': str},
                    'last': {'type': str}
                })}})

    def test_type_cannot_be_an_instance(self):
        self.assert_spec_invalid({"author": {'type': "wrong"}}, 'author')

    def test_required_should_be_a_boolean(self):
        self.assert_spec_invalid(
            {
                "author": {'type': int, 'required': 23}
            },
            'author')

    def test_nullable_should_be_a_boolean(self):
        self.assert_spec_invalid(
            {
                "author": {'type': int, 'nullable': 23}
            },
            'author')


    def test_single_validation_function(self):
        Schema({'some_field': {'type':int, "validates":one_of(['a', 'b'])}})

    def test_multiple_validation_functions(self):
        Schema({'some_field': {'type':int, "validates":[gte(1), lte(10)]}})

    def test_invalid_validation(self):
        self.assert_spec_invalid(
            {'some_field': {'type':int, "validates":'wrong'}},
            'some_field')

    def test_invalid_validation_in_validation_list(self):
        self.assert_spec_invalid(
            {'some_field': {'type':int, "validates":[gte(1), 'wrong']}},
            'some_field')

    def test_incorrect_validator_arg_spec(self):
        def bad_validator():
            pass

        self.assert_spec_invalid(
            {'some_field': {'type':int, "validates":bad_validator}},
            'some_field')

        self.assert_spec_invalid(
            {'some_field': {'type':int, "validates":[bad_validator, gte(1)]}},
            'some_field')

    def test_unsupported_keys(self):
        self.assert_spec_invalid(
            {
                "somefield": {"type":int, "something":"wrong"},
                "otherfield": {"type":int}
            },
            'somefield')

    def test_default_value_of_correct_type(self):
        Schema({'num_wheels':{'type':int, 'default':4}})

    def test_default_value_of_incorrect_type(self):
        self.assert_spec_invalid(
            {'num_wheels':{'type':int, 'default':'wrong'}},
            'num_wheels')

    def test_default_schema_value_of_incorrect_type_1(self):
        self.assert_spec_invalid(
            {'wheel':{'type':Schema({'size': {'type': int, 'default': 32},
                                     'brand': {'type': basestring, 'default': 'firestone'}}),
                      'default':'wrong'}},
            'wheel')

    def test_default_schema_value_correct_1(self):
        Schema({'wheel':{'type':Schema({'size': {'type': int, 'default': 32},
                                        'brand': {'type': basestring, 'default': 'firestone'}}),
                'default':{'wrong': True}}})

    def test_default_schema_value_correct_2(self):
        Schema({'wheel':{'type':Schema({'size': {'type': int, 'default': 32},
                                        'brand': {'type': basestring, 'default': 'firestone'}}),
                      'default':{}}})

    def test_default_array_schema_value_of_incorrect_type_1(self):
        self.assert_spec_invalid(
            {'wheel':{'type':Array(Schema({'size': {'type': int, 'default': 32},
                                           'brand': {'type': basestring, 'default': 'firestone'}})),
                      'default':'wrong'}},
            'wheel')

    def test_default_array_schema_value_of_incorrect_type_2(self):
        self.assert_spec_invalid(
            {'wheel':{'type':Array(Schema({'size': {'type': int, 'default': 32},
                                           'brand': {'type': basestring, 'default': 'firestone'}})),
                      'default':{}}},
            'wheel')

    def test_default_array_schema_value_correct_1(self):
        Schema({'wheel':{'type':Array(Schema({'size': {'type': int, 'default': 32},
                                              'brand': {'type': basestring, 'default': 'firestone'}})),
                'default':[{'wrong': True}]}})

    def test_default_array_schema_value_correct_2(self):
        Schema({'wheel':{'type':Array(Schema({'size': {'type': int, 'default': 32},
                                              'brand': {'type': basestring, 'default': 'firestone'}})),
                      'default':[{}]}})

    def test_default_value_accepts_function(self):
        def default_fn():
            return 4

        Schema({'num_wheels':{'type':int, 'default':default_fn}})

    def test_spec_wrong_type(self):
        self.assert_spec_invalid(
            {
                "items": []
            },
            'items')
        self.assert_spec_invalid(
            {
                "items": "wrong"
            },
            'items')

    def test_nested_schema_cannot_have_validation(self):
        def some_func():
            pass
        self.assert_spec_invalid(
            {
                "content": {'type': Schema({
                    "somefield": {"type": int}
                }), "validates": some_func}
            },
            'content')

    def test_array_of_ints(self):
        Schema({
            "numbers": {"type": Array(int)}
        })

    def test_array_of_strings_with_default(self):
        Schema({
            "fruit": {'type': Array(basestring), "default": ['apple', 'orange']}
        })

    def test_array_of_strings_with_invalid_default(self):
        self.assert_spec_invalid({
            "fruit": {'type': Array(basestring), "default": 'not a list'}
        }, 'fruit')

    def test_array_of_strings_with_invalid_default_content(self):
        self.assert_spec_invalid({
            "nums": {'type': Array(int), "default": ['not an int']}
        }, 'nums')

    def test_invalid_array_with_value_not_type(self):
        self.assert_spec_invalid({
                "items": {"type": Array(1)}
            },
            'items')

    def test_array_validation(self):
        Schema({
            "fruit": {'type': Array(basestring), "validates": length(1, 2)}
        })

class TestBlogValidation(unittest.TestCase):
    def setUp(self):
        self.document_1 = valid_doc()
        self.document_2 = valid_doc(overrides={"author": {"first_name": "John",
                                                               "last_name": "Humphreys",
                                                               "birth_year": 1978,
                                                               "birth_month": 8,
                                                               "birth_day": 15}})

    def assert_document_paths_invalid(self, document, paths):
        with self.assertRaises(ValidationException) as cm:
            blog_post_schema.validate(document)
        self.assertListEqual(paths, cm.exception.errors.keys())

    def test_valid_document_1(self):
        blog_post_schema.validate(self.document_1)

    def test_valid_document_2(self):
        blog_post_schema.validate(self.document_2)

    def test_missing_required_field_1(self):
        del self.document_1["author"]
        self.assert_document_paths_invalid(self.document_1, ["author"])

    def test_missing_subfield_of_dynamic_schema_1(self):
        del self.document_1["author"]["last"]
        self.assert_document_paths_invalid(self.document_1, ["author.last"])

    def test_missing_subfield_of_dynamic_schema_2(self):
        del self.document_2["author"]["last_name"]
        self.assert_document_paths_invalid(self.document_2, ["author.last_name"])

    def test_required_field_with_null_value(self):
        # By default, required fields are not nullable
        self.document_1['author'] = None
        self.assert_document_paths_invalid(self.document_1, ['author'])

    def test_non_required_field_set_to_none(self):
        self.document_1['likes'] = None
        blog_post_schema.validate(self.document_1)

    def test_missing_required_array_field(self):
        del self.document_1['comments']
        self.assert_document_paths_invalid(self.document_1, ['comments'])

    def test_set_non_nullable_field_to_none(self):
        self.document_1['external_code'] = None
        self.assert_document_paths_invalid(self.document_1, ['external_code'])

    def test_dynamic_function_exception(self):
        self.document_1['author'] = 33
        with self.assertRaises(SchemaFormatException) as cm:
            blog_post_schema.validate(self.document_1)
        self.assertEqual('author', cm.exception.path)

    def test_mixed_type(self):
        self.document_1['misc'] = "a string"
        blog_post_schema.validate(self.document_1)
        self.document_1['misc'] = 32
        blog_post_schema.validate(self.document_1)

    def test_mixed_type_instance_incorrect_type(self):
        self.document_1['linked_id'] = 123.45
        self.assert_document_paths_invalid(self.document_1, ['linked_id'])

    def test_missing_embedded_document(self):
        del self.document_1['content']
        self.assert_document_paths_invalid(self.document_1, ['content'])

    def test_missing_required_field_in_embedded_document(self):
        del self.document_1['content']['title']
        self.assert_document_paths_invalid(self.document_1, ['content.title'])

    def test_missing_required_field_in_embedded_collection(self):
        del self.document_1['comments'][0]['commenter']
        self.assert_document_paths_invalid(self.document_1, ['comments.0.commenter'])

    def test_multiple_missing_fields(self):
        del self.document_1['content']['title']
        del self.document_1['comments'][1]['commenter']
        del self.document_1['author']
        self.assert_document_paths_invalid(
            self.document_1,
            ['content.title', 'comments.1.commenter', 'author'])

    def test_embedded_collection_item_of_incorrect_type(self):
        self.document_1['tags'].append(55)
        self.assert_document_paths_invalid(self.document_1, ['tags.3'])

    def test_validation_failure(self):
        self.document_1['category'] = 'gardening'  # invalid category
        self.assert_document_paths_invalid(self.document_1, ['category'])

    def test_disallows_fields_not_in_schema(self):
        self.document_1['something'] = "extra"
        self.assert_document_paths_invalid(self.document_1, ['something'])

    def test_validation_of_array(self):
        self.document_1['tags'] = []
        self.assert_document_paths_invalid(self.document_1, ['tags'])

    def test_dynamic_function_valid_array(self):
        self.document_1['website'] = [self.document_1['website'] for i in range(2)]
        blog_post_schema.validate(self.document_1)

    def test_dynamic_function_invalid_array(self):
        self.document_1['website'] = ["string" for i in range(2)]
        self.assert_document_paths_invalid(self.document_1, ['website.0', 'website.1'])

    def test_dynamic_function_correct_type(self):
        self.document_1['website'] = "WEB"
        blog_post_schema.validate(self.document_1)

    def test_dynamic_function_wrong_type(self):
        self.document_1['website'] = 56
        self.assert_document_paths_invalid(self.document_1, ['website'])

    def test_array_with_dynamic_function_correct_types(self):
        self.document_1['editors'] = [{'first': 'Jordan', 'last': 'Gansey'}]
        blog_post_schema.validate(self.document_1)
        self.document_1['editors'] = ['Jordan Gansey']
        blog_post_schema.validate(self.document_1)

    def test_array_with_dynamic_function_wrong_types(self):
        self.document_1['editors'] = [{'first': 'Jordan'}]
        self.assert_document_paths_invalid(self.document_1, ['editors.0.last'])
        self.document_1['editors'] = [555]
        self.assert_document_paths_invalid(self.document_1, ['editors.0'])

    def test_array_with_dynamic_function_heterogenous_list_correct_type(self):
        self.document_1['editors'] = [{'first': 'Jordan', 'last': 'Gansey'}, 'Jordan Gansey']
        blog_post_schema.validate(self.document_1)

    def test_array_with_dynamic_function_heterogenous_list_wrong_type(self):
        self.document_1['editors'] = ['Jordan Gansey', {'last': 'Gansey'}]
        self.assert_document_paths_invalid(self.document_1, ['editors.1.first'])

    def test_schema_level_validator_list_item_failure_to_small(self):
        self.document_1.update(
            {'creation_date': datetime(2014, 1, 1),
             'modification_date': datetime(2013, 1, 1),
             'final_date': datetime(2015, 1, 1)})
        self.assert_document_paths_invalid(self.document_1, [''])

    def test_schema_level_validator_list_item_failure_to_large(self):
        self.document_1.update(
            {'creation_date': datetime(2014, 1, 1),
             'modification_date': datetime(2016, 1, 1),
             'final_date': datetime(2015, 1, 1)})
        self.assert_document_paths_invalid(self.document_1, [''])

    def test_schema_level_validator_list_item_just_right(self):
        self.document_1.update(
            {'creation_date': datetime(2014, 1, 1),
             'modification_date': datetime(2015, 1, 1),
             'final_date': datetime(2016, 1, 1)})

        blog_post_schema.validate(self.document_1)


class TestDefaultApplication(unittest.TestCase):
    def setUp(self):
        self.document_1 = {
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
                    "commenter": "Julio Cesar",
                    "email": "jcesar@test.com",
                    "comment": "Great post dude!"
                },
                {
                    "commenter": "Michael Andrews",
                    "comment": "My wife loves these."
                }
            ]
        }

    def test_apply_default_function(self):
        blog_post_schema.apply_defaults(self.document_1)
        self.assertEqual(stubnow(), self.document_1['creation_date'])

    def test_apply_default_value(self):
        blog_post_schema.apply_defaults(self.document_1)
        self.assertEqual(0, self.document_1['likes'])

    def test_apply_default_value_in_nested_document(self):
        blog_post_schema.apply_defaults(self.document_1)
        self.assertEqual(1, self.document_1['content']['page_views'])

    def test_apply_default_value_in_array(self):
        blog_post_schema.apply_defaults(self.document_1)
        self.assertEqual(0, self.document_1['comments'][0]['votes'])
        self.assertEqual(0, self.document_1['comments'][1]['votes'])

    def test_apply_default_value_for_array(self):
        blog_post_schema.apply_defaults(self.document_1)
        self.assertEqual(['blog'], self.document_1['tags'])

    def test_default_value_does_not_overwrite_existing(self):
        self.document_1['likes'] = 35
        self.document_1['creation_date'] = datetime(1980, 5, 3)
        blog_post_schema.apply_defaults(self.document_1)
        self.assertEqual(35, self.document_1['likes'])
        self.assertEqual(datetime(1980, 5, 3), self.document_1['creation_date'])

    def test_default_schema_value(self):
        blog_post_schema.apply_defaults(self.document_1)
        self.assertEqual(0, self.document_1['latest_comment']['votes'])

    def test_default_array_schema_value(self):
        blog_post_schema.apply_defaults(self.document_1)
        for i in range(3):
            self.assertEqual(0, self.document_1['most_popular_comments'][i]['votes'])

