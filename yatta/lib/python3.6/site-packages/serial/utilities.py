import re


def camel2underscore(string):
    # type: (str) -> str
    """
    Converts a "camelCased" property name (javascript convention) into an underscore-separated property name.

    >>> print(camel2underscore('theBirdsAndTheBees'))
    the_birds_and_the_bees

    >>> print(camel2underscore('FYIThisIsAnAcronym'))
    fyi_this_is_an_acronym
    """
    return re.sub(
        r'([a-zA-Z])([0-9])',
        r'\1_\2',
        re.sub(
            r'([0-9])([a-zA-Z])',
            r'\1_\2',
            re.sub(
                r'([A-Z])([A-Z])([a-z])',
                r'\1_\2\3',
                re.sub(
                    r'([a-z])([A-Z])',
                    r'\1_\2',
                    string
                )
            )
        )
    ).casefold()
