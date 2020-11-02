import collections.abc
import yaml
from contextlib import contextmanager
from yaml.error import MarkedYAMLError
from yaml.loader import SafeLoader
from yaml.nodes import MappingNode, SequenceNode
from yaml.constructor import ConstructorError

__all__ = ['load_file', 'make_parse_error', 'to_parse_error', 'MarkedDict',
           'MarkedList', 'SafeLineLoader', 'YamlParseError']


class YamlParseError(Exception):
    def __init__(self, message, mark, snippet):
        self.message = message
        self.mark = mark
        self.snippet = snippet

    def __str__(self):
        return (self.message + '\n' +
                str(self.mark) + '\n' +
                '  ' + self.snippet + '\n' +
                ' ' * (self.mark.column + 2) + '^')


def make_parse_error(e, stream):
    stream.seek(e.problem_mark.index - e.problem_mark.column, 0)
    snippet = stream.readline().rstrip()
    return YamlParseError(e.problem, e.problem_mark, snippet)


@contextmanager
def to_parse_error(filename):
    try:
        yield
    except MarkedYAMLError as e:
        with open(filename, newline='') as f:
            raise make_parse_error(e, f)


@contextmanager
def load_file(filename, Loader=SafeLoader):
    with open(filename, newline='') as f:
        try:
            yield yaml.load(f, Loader=Loader)
        except MarkedYAMLError as e:
            raise make_parse_error(e, f)


def dump(data):
    # `sort_keys` only works on newer versions of PyYAML, so don't worry too
    # much if we can't use it.
    try:
        return yaml.dump(data, sort_keys=False)
    except TypeError:
        return yaml.dump(data)


class MarkedCollection:
    pass


class MarkedList(list, MarkedCollection):
    def __init__(self, mark=None):
        super().__init__(self)
        self.mark = mark
        self.marks = []

    def _fill_marks(self):
        # Ensure we have the same number of marks as we do elements.
        # Note: this doesn't account for deletions or anything fancy like that,
        # but those shouldn't happen anyway.
        for i in range(len(self.marks), len(self)):
            self.marks.append(None)

    def append(self, value, mark):
        self._fill_marks()
        super().append(value)
        self.marks.append(mark)

    def extend(self, rhs):
        self._fill_marks()
        super().extend(rhs)
        if isinstance(rhs, MarkedCollection):
            if self.mark is None:
                self.mark = rhs.mark
            self.marks.extend(rhs.marks)
        else:
            self.marks.extend([None] * len(rhs))

    def copy(self):
        result = MarkedList()
        result.extend(self)
        return result


class MarkedDict(dict, MarkedCollection):
    def __init__(self, mark=None):
        super().__init__(self)
        self.mark = mark
        self.marks = {}

    def add(self, key, value, mark):
        self[key] = value
        self.marks[key] = mark

    def pop(self, key, *args):
        result = super().pop(key, *args)
        self.marks.pop(key, None)
        return result

    def update(self, *args, **kwargs):
        super().update(*args, **kwargs)
        if len(args) and isinstance(args[0], MarkedCollection):
            if self.mark is None:
                self.mark = args[0].mark
                self.marks.update(args[0].marks)

    def copy(self):
        result = MarkedDict()
        result.update(self)
        return result


class SafeLineLoader(SafeLoader):
    def construct_yaml_seq(self, node):
        data = MarkedList()
        yield data
        data.extend(self.construct_sequence(node))

    def construct_yaml_map(self, node):
        data = MarkedDict()
        yield data
        data.update(self.construct_mapping(node))

    def construct_sequence(self, node, deep=False):
        if not isinstance(node, SequenceNode):  # pragma: no cover
            raise ConstructorError(
                None, None, 'expected a sequence node, but found %s' % node.id,
                node.start_mark
            )
        sequence = MarkedList(node.start_mark)
        for child_node in node.value:
            sequence.append(self.construct_object(child_node, deep=deep),
                            child_node.start_mark)
        return sequence

    def construct_mapping(self, node, deep=False):
        if not isinstance(node, MappingNode):  # pragma: no cover
            raise ConstructorError(
                None, None, 'expected a mapping node, but found %s' % node.id,
                node.start_mark
            )
        mapping = MarkedDict(node.start_mark)
        for key_node, value_node in node.value:
            key = self.construct_object(key_node, deep=deep)
            if not isinstance(
                key, collections.abc.Hashable
            ):  # pragma: no cover
                raise ConstructorError(
                    'while constructing a mapping', node.start_mark,
                    'found unhashable key', key_node.start_mark
                )
            value = self.construct_object(value_node, deep=deep)
            mapping.add(key, value, key_node.start_mark)
        return mapping


SafeLineLoader.add_constructor('tag:yaml.org,2002:seq',
                               SafeLineLoader.construct_yaml_seq)
SafeLineLoader.add_constructor('tag:yaml.org,2002:map',
                               SafeLineLoader.construct_yaml_map)
