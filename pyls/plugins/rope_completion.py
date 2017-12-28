# Copyright 2017 Palantir Technologies, Inc.
import logging
from rope.contrib.codeassist import code_assist, sorted_proposals

from pyls import hookimpl, lsp


log = logging.getLogger(__name__)


@hookimpl
def pyls_rope_completions(document, position):
    log.debug('Launching Rope')

    # Rope is a bit rubbish at completing module imports, so we'll return None
    word = document.word_at_position({
        # The -1 should really be trying to look at the previous word, but that might be quite expensive
        # So we only skip import completions when the cursor is one space after `import`
        'line': position['line'], 'character': max(position['character'] - 1, 0),
    })
    if word == 'import':
        return None

    offset = document.offset_at_position(position)
    definitions = code_assist(
        document._rope_project, document.source,
        offset, document._rope, maxfixes=3)

    definitions = sorted_proposals(definitions)
    new_definitions = []
    for d in definitions:
        try:
            doc = d.get_doc()
        except AttributeError:
            doc = None
        new_definitions.append({
            'label': d.name,
            'kind': _kind(d),
            'detail': '{0} {1}'.format(d.scope or "", d.name),
            'documentation': doc or "",
            'sortText': _sort_text(d)})
    definitions = new_definitions
    log.debug('Rope finished')
    return definitions or None


@hookimpl
def pyls_rope_resolve_completion(completion_item):
    return completion_item


def _sort_text(definition):
    """ Ensure builtins appear at the bottom.
    Description is of format <type>: <module>.<item>
    """
    if definition.scope == 'builtin':
        return 'z' + definition.name

    if definition.name.startswith("_"):
        # It's a 'hidden' func, put it next last
        return 'y' + definition.name

    # Else put it at the front
    return 'a' + definition.name


def _kind(d):
    """ Return the VSCode type """
    MAP = {
        'none': lsp.CompletionItemKind.Value,
        'type': lsp.CompletionItemKind.Class,
        'tuple': lsp.CompletionItemKind.Class,
        'dict': lsp.CompletionItemKind.Class,
        'dictionary': lsp.CompletionItemKind.Class,
        'function': lsp.CompletionItemKind.Function,
        'lambda': lsp.CompletionItemKind.Function,
        'generator': lsp.CompletionItemKind.Function,
        'class': lsp.CompletionItemKind.Class,
        'instance': lsp.CompletionItemKind.Reference,
        'method': lsp.CompletionItemKind.Method,
        'builtin': lsp.CompletionItemKind.Class,
        'builtinfunction': lsp.CompletionItemKind.Function,
        'module': lsp.CompletionItemKind.Module,
        'file': lsp.CompletionItemKind.File,
        'xrange': lsp.CompletionItemKind.Class,
        'slice': lsp.CompletionItemKind.Class,
        'traceback': lsp.CompletionItemKind.Class,
        'frame': lsp.CompletionItemKind.Class,
        'buffer': lsp.CompletionItemKind.Class,
        'dictproxy': lsp.CompletionItemKind.Class,
        'funcdef': lsp.CompletionItemKind.Function,
        'property': lsp.CompletionItemKind.Property,
        'import': lsp.CompletionItemKind.Module,
        'keyword': lsp.CompletionItemKind.Keyword,
        'constant': lsp.CompletionItemKind.Variable,
        'variable': lsp.CompletionItemKind.Variable,
        'value': lsp.CompletionItemKind.Value,
        'param': lsp.CompletionItemKind.Variable,
        'statement': lsp.CompletionItemKind.Keyword,
    }

    return MAP.get(d.type)
