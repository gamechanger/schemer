import types, copy
from inspect import getargspec
from exceptions import ValidationException, SchemaFormatException
from extension_types import Mixed


class Array(object):
    def __init__(self, contained_type):
        self.contained_type = contained_type


class Schema(object):
    """A Schema encapsulates the structure and constraints of a dict."""

    def __init__(self, doc_spec, strict=True, validates=[]):
        self._doc_spec = doc_spec
        self._virtuals = {}
        self._strict = strict
        self._verify()
        self._validates = validates

    @property
    def doc_spec(self):
        return self._doc_spec

    def apply_defaults(self, instance):
        """Applies the defaults described by the this schema to the given
        document instance as appropriate. Defaults are only applied to
        fields which are currently unset."""
        for field, spec in self.doc_spec.iteritems():
            field_type = spec['type']
            if field not in instance:
                if 'default' in spec:
                    default = spec['default']
                    if callable(default):
                        instance[field] = default()
                    else:
                        instance[field] = default
            # Determine if a value already exists for the field
            if field in instance:
                value = instance[field]

                # recurse into nested docs
                if isinstance(field_type, Schema) and isinstance(value, dict):
                    field_type.apply_defaults(value)

                elif isinstance(field_type, Array) and isinstance(field_type.contained_type, Schema) and isinstance(value, list):
                    for item in value:
                        field_type.contained_type.apply_defaults(item)

    def validate(self, instance):
        """Validates the given document against this schema. Raises a
        ValidationException if there are any failures."""
        errors = {}
        self._validate_instance(instance, errors)

        if len(errors) > 0:
            raise ValidationException(errors)

    def _append_path(self, prefix, field):
        """Appends the given field to the given path prefix."""
        if prefix:
            return "{}.{}".format(prefix, field)
        else:
            return field

    def _verify(self, path_prefix=None):
        """Verifies that this schema's doc spec is valid and makes sense."""
        for field, spec in self.doc_spec.iteritems():
            path = self._append_path(path_prefix, field)

            # Standard dict-based spec
            if isinstance(spec, dict):
                self._verify_field_spec(spec, path)
            else:
                raise SchemaFormatException("Invalid field definition for {}", path)


    def _verify_field_spec(self, spec, path):
        """Verifies a given field specification is valid, recursing into nested schemas if required."""

        # Required should be a boolean
        if 'required' in spec and not isinstance(spec['required'], bool):
            raise SchemaFormatException("{} required declaration should be True or False", path)

        # Required should be a boolean
        if 'nullable' in spec and not isinstance(spec['nullable'], bool):
            raise SchemaFormatException("{} nullable declaration should be True or False", path)

        # Must have a type specified
        if 'type' not in spec:
            raise SchemaFormatException("{} has no type declared.", path)

        self._verify_type(spec, path)

        # Validations should be either a single function or array of functions
        if 'validates' in spec:
            self._verify_validates(spec, path)

        # Defaults must be of the correct type or a function
        if 'default' in spec:
            self._verify_default(spec, path)

        # Only expected spec keys are supported
        if not set(spec.keys()).issubset(set(['type', 'required', 'validates', 'default', 'nullable'])):
            raise SchemaFormatException("Unsupported field spec item at {}. Items: "+repr(spec.keys()), path)

    def _verify_type(self, spec, path):
        """Verify that the 'type' in the spec is valid"""
        field_type = spec['type']

        if isinstance(field_type, Schema):
            # Nested documents cannot have validation
            if not set(spec.keys()).issubset(set(['type', 'required', 'nullable', 'default'])):
                raise SchemaFormatException("Unsupported field spec item at {}. Items: "+repr(spec.keys()), path)
            return

        elif isinstance(field_type, Array):
            if not isinstance(field_type.contained_type, (type, Schema, Array, types.FunctionType)):
                raise SchemaFormatException("Unsupported field type contained by Array at {}.", path)

        elif not isinstance(field_type, type) and not isinstance(field_type, types.FunctionType):
            raise SchemaFormatException("Unsupported field type at {}. Type must be a type, a function, an Array or another Schema", path)

    def _valid_schema_default(self, value):
        return isinstance(value, dict)

    def _verify_default(self, spec, path):
        """Verifies that the default specified in the given spec is valid."""
        field_type = spec['type']
        default = spec['default']

        # If it's a function there's nothing we can really do except assume its valid
        if callable(default):
            return

        if isinstance(field_type, Array):
            # Verify we'd got a list as our default
            if not isinstance(default, list):
                raise SchemaFormatException("Default value for Array at {} is not a list of values.", path)

            # Ensure the contents are of the correct type
            for i, item in enumerate(default):
                if isinstance(field_type.contained_type, Schema):
                    if not self._valid_schema_default(item):
                        raise SchemaFormatException("Default value for Schema is not valid.", path)
                elif not isinstance(item, field_type.contained_type):
                        raise SchemaFormatException("Not all items in the default list for the Array field at {} are of the correct type.", path)

        elif isinstance(field_type, Schema):
            if not self._valid_schema_default(default):
                raise SchemaFormatException("Default value for Schema is not valid.", path)

        else:
            if not isinstance(default, field_type):
                raise SchemaFormatException("Default value for {} is not of the nominated type.", path)


    def _verify_validates(self, spec, path):
        """Verify thats the 'validates' argument is valid."""
        validates = spec['validates']

        if isinstance(validates, list):
            for validator in validates:
                self._verify_validator(validator, path)
        else:
            self._verify_validator(validates, path)


    def _verify_validator(self, validator, path):
        """Verifies that a given validator associated with the field at the given path is legitimate."""

        # Validator should be a function
        if not callable(validator):
            raise SchemaFormatException("Invalid validations for {}", path)

        # Validator should accept a single argument
        (args, varargs, keywords, defaults) = getargspec(validator)
        if len(args) != 1:
            raise SchemaFormatException("Invalid validations for {}", path)


    def _validate_instance(self, instance, errors, path_prefix=''):
        """Validates that the given instance of a document conforms to the given schema's
        structure and validations. Any validation errors are added to the given errors
        collection. The caller should assume the instance is considered valid if the
        errors collection is empty when this method returns."""

        if not isinstance(instance, dict):
            errors[path_prefix] = "Expected instance of dict to validate against schema."
            return

        # validate against the schema level validators
        self._apply_validations(errors, path_prefix, self._validates, instance)

        # Loop over each field in the schema and check the instance value conforms
        # to its spec
        for field, spec in self.doc_spec.iteritems():
            path = self._append_path(path_prefix, field)

            # If the field is present, validate it's value.
            if field in instance:
                self._validate_value(instance[field], spec, path, errors)
            else:
                # If not, add an error if it was a required key.
                if spec.get('required', False):
                    errors[path] = "{} is required.".format(path)

        # Now loop over each field in the given instance and make sure we don't
        # have any fields not declared in the schema, unless strict mode has been
        # explicitly disabled.
        if self._strict:
            for field in instance:
                if field not in self.doc_spec:
                    errors[self._append_path(path_prefix, field)] = "Unexpected document field not present in schema"

    def _validate_value(self, value, field_spec, path, errors):
        """Validates that the given field value is valid given the associated
        field spec and path. Any validation failures are added to the given errors
        collection."""

        # Check if the value is None and add an error if the field is not nullable.
        # Note that for backward compatibility reasons, the default value of 'nullable'
        # is the inverse of 'required' (which use to mean both that the key be present
        # and not set to None).
        if value is None:
            if not field_spec.get('nullable', not field_spec.get('required', False)):
                errors[path] = "{} is not nullable.".format(path)
            return

        # All fields should have a type
        field_type = field_spec['type']
        if isinstance(field_type, types.FunctionType):
            try:
                field_type = field_type(value)
            except Exception as e:
                raise SchemaFormatException("Dynamic schema function raised exception: {}".format(str(e)), path)
            if not isinstance(field_type, (type, Schema, Array)):
                raise SchemaFormatException("Dynamic schema function did not return a type at path {}", path)


        # If our field is an embedded document, recurse into it
        if isinstance(field_type, Schema):
            if isinstance(value, dict):
                field_type._validate_instance(value, errors, path)
            else:
                errors[path] = "{} should be an embedded document".format(path)
            return

        elif isinstance(field_type, Array):
            if isinstance(value, list):
                is_dynamic = isinstance(field_type.contained_type, types.FunctionType)
                for i, item in enumerate(value):
                    contained_type = field_type.contained_type
                    if is_dynamic:
                        contained_type = contained_type(item)
                    instance_path = self._append_path(path, i)
                    if isinstance(contained_type, Schema):
                        contained_type._validate_instance(item, errors, instance_path)
                    elif not isinstance(item, contained_type):
                        errors[instance_path] = "Array item at {} is of incorrect type".format(instance_path)
                        continue
            else:
                errors[path] = "{} should be an embedded array".format(path)
                return

        elif not isinstance(value, field_type):
            errors[path] = "Field should be of type {}".format(field_type)
            return

        validations = field_spec.get('validates', None)
        if validations is None:
            return
        self._apply_validations(errors, path, validations, value)

    def _apply_validations(self, errors, path, validations, value):
        def apply(fn):
            error = fn(value)
            if error:
                errors[path] = error

        if isinstance(validations, list):
            for validation in validations:
                apply(validation)
        else:
            apply(validations)

