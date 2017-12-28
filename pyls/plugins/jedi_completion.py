# Copyright 2017 Palantir Technologies, Inc.
import uuid
from pyls.lsp import CompletionItemKind
from pyls import hookimpl, _utils

_JEDI_CACHE = {}


@hookimpl
def pyls_jedi_completions(document, position):
    _JEDI_CACHE.clear()
    definitions = document.jedi_script(position).completions()
    return [_parse_completion(d) for d in definitions]


@hookimpl
def pyls_jedi_resolve_completion(completion_item):
    _id = completion_item.get('data')
    definition = _JEDI_CACHE.get(_id) if _id is not None else None
    if definition is not None:
        completion_item['documentation'] = _utils.format_docstring(definition.docstring())
    return completion_item


def _parse_completion(definition):
    _id = str(uuid.uuid4())
    _JEDI_CACHE[_id] = definition
    d_type = definition.type
    return {
        'label': _label(definition, d_type),
        'kind': _kind(d_type),
        'detail': _detail(definition),
        'documentation': _utils.format_docstring(definition.docstring()),
        'sortText': _sort_text(definition),
        'insertText': definition.name,
        'data': _id
    }


def _label(definition, d_type):
    if d_type in ('function', 'method'):
        params = ", ".join(param.name for param in definition.params)
        return "{}({})".format(definition.name, params)

    return definition.name


def _detail(definition):
    return "builtin" if definition.in_builtin_module() else definition.parent().full_name or ""


def _sort_text(definition):
    """ Ensure builtins appear at the bottom.
    Description is of format <type>: <module>.<item>
    """
    if definition.in_builtin_module():
        # It's a builtin, put it last
        return 'z' + definition.name

    if definition.name.startswith("_"):
        # It's a 'hidden' func, put it next last
        return 'y' + definition.name

    # Else put it at the front
    return 'a' + definition.name


def _kind(d_type):
    """ Return the VSCode type """
    MAP = {
        'none': CompletionItemKind.Value,
        'type': CompletionItemKind.Class,
        'tuple': CompletionItemKind.Class,
        'dict': CompletionItemKind.Class,
        'dictionary': CompletionItemKind.Class,
        'function': CompletionItemKind.Function,
        'lambda': CompletionItemKind.Function,
        'generator': CompletionItemKind.Function,
        'class': CompletionItemKind.Class,
        'instance': CompletionItemKind.Reference,
        'method': CompletionItemKind.Method,
        'builtin': CompletionItemKind.Class,
        'builtinfunction': CompletionItemKind.Function,
        'module': CompletionItemKind.Module,
        'file': CompletionItemKind.File,
        'xrange': CompletionItemKind.Class,
        'slice': CompletionItemKind.Class,
        'traceback': CompletionItemKind.Class,
        'frame': CompletionItemKind.Class,
        'buffer': CompletionItemKind.Class,
        'dictproxy': CompletionItemKind.Class,
        'funcdef': CompletionItemKind.Function,
        'property': CompletionItemKind.Property,
        'import': CompletionItemKind.Module,
        'keyword': CompletionItemKind.Keyword,
        'constant': CompletionItemKind.Variable,
        'variable': CompletionItemKind.Variable,
        'value': CompletionItemKind.Value,
        'param': CompletionItemKind.Variable,
        'statement': CompletionItemKind.Keyword,
    }

    return MAP.get(d_type)
