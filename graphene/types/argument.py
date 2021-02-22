from itertools import chain

from .dynamic import Dynamic
from .mountedtype import MountedType
from .structures import NonNull
from .utils import get_type


class Argument(MountedType):
    """
    Makes an Argument available on a Field in the GraphQL schema.

    Arguments will be parsed and provided to resolver methods for fields as keyword arguments.

    All ``arg`` and ``**extra_args`` for a ``graphene.Field`` are implicitly mounted as Argument
    using the below parameters.

    .. code:: python

        from graphene import String, Boolean, Argument

        age = String(
            # Boolean implicitly mounted as Argument
            dog_years=Boolean(description="convert to dog years"),
            # Boolean explicitly mounted as Argument
            decades=Argument(Boolean, default_value=False),
        )

    args:
        type (class for a graphene.UnmountedType): must be a class (not an instance) of an
            unmounted graphene type (ex. scalar or object) which is used for the type of this
            argument in the GraphQL schema.
        required (bool): indicates this argument as not null in the graphql schema. Same behavior
            as graphene.NonNull. Default False.
        name (str): the name of the GraphQL argument. Defaults to parameter name.
        description (str): the description of the GraphQL argument in the schema.
        default_value (Any): The value to be provided if the user does not set this argument in
            the operation.
    """

    def __init__(
        self,
        type_,
        default_value=None,
        description=None,
        name=None,
        required=False,
        _creation_counter=None,
    ):
        super(Argument, self).__init__(_creation_counter=_creation_counter)

        if required:
            type_ = NonNull(type_)

        self.name = name
        self._type = type_
        self.default_value = default_value
        self.description = description

    @property
    def type(self):
        return get_type(self._type)

    def __eq__(self, other):
        return isinstance(other, Argument) and (
            self.name == other.name
            and self.type == other.type
            and self.default_value == other.default_value
            and self.description == other.description
        )


def to_arguments(args, extra_args=None):
    from .unmountedtype import UnmountedType
    from .field import Field
    from .inputfield import InputField

    if type(args) == dict and len(args) == 1 and '__annotations__' in args:
        raise ValueError(f"Arguments class doesn't have any field but has type annotations. "
                         f"You probably used ':' instead of '=' in class definition")

    if extra_args:
        extra_args = sorted(extra_args.items(), key=lambda f: f[1])
    else:
        extra_args = []
    iter_arguments = chain(args.items(), extra_args)
    arguments = {}
    for default_name, arg in iter_arguments:
        if isinstance(arg, Dynamic):
            arg = arg.get_type()
            if arg is None:
                # If the Dynamic type returned None
                # then we skip the Argument
                continue

        if isinstance(arg, UnmountedType):
            arg = Argument.mounted(arg)

        if isinstance(arg, (InputField, Field)):
            raise ValueError(
                f"Expected {default_name} to be Argument, "
                f"but received {type(arg).__name__}. Try using Argument({arg.type})."
            )

        if not isinstance(arg, Argument):
            raise ValueError(f'Unknown argument "{default_name}".')

        arg_name = default_name or arg.name
        assert (
            arg_name not in arguments
        ), f'More than one Argument have same name "{arg_name}".'
        arguments[arg_name] = arg

    return arguments
