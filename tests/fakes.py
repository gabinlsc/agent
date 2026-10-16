"""Faux client OpenAI pour tester la boucle sans appel réseau."""
import json
from types import SimpleNamespace as NS


def reply(text=None, *calls):
    """Une réponse du modèle : du texte et/ou des appels d'outils."""
    return (text, list(calls))


def call(id, name, **args):
    return (id, name, json.dumps(args))


def _chunk(content=None, tool_calls=None):
    return NS(choices=[NS(delta=NS(content=content, tool_calls=tool_calls))])


def _stream(text, calls):
    if text:
        mid = len(text) // 2
        yield _chunk(content=text[:mid])
        yield _chunk(content=text[mid:])
    for i, (id, name, args) in enumerate(calls):
        mid = len(args) // 2  # les arguments arrivent en deux morceaux, comme sur un vrai flux
        yield _chunk(tool_calls=[NS(index=i, id=id, function=NS(name=name, arguments=args[:mid]))])
        yield _chunk(tool_calls=[NS(index=i, id=None, function=NS(name=None, arguments=args[mid:]))])


class FakeClient:
    """Rejoue une liste de réponses ; enregistre les requêtes reçues dans `calls`."""

    def __init__(self, replies):
        self.replies = list(replies)
        self.calls = []
        self.chat = NS(completions=self)

    def create(self, **kw):
        kw["messages"] = list(kw["messages"])  # instantané : la boucle modifie la liste ensuite
        self.calls.append(kw)
        return _stream(*self.replies.pop(0))
