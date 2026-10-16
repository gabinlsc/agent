"""Faux client Anthropic pour tester la boucle sans appel réseau."""
from types import SimpleNamespace as NS


def text(t):
    return NS(type="text", text=t)


def tool_use(id, name, **inp):
    return NS(type="tool_use", id=id, name=name, input=inp)


class FakeStream:
    def __init__(self, msg):
        self.msg = msg

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False

    @property
    def text_stream(self):
        return (b.text for b in self.msg.content if b.type == "text")

    def get_final_message(self):
        return self.msg


class FakeClient:
    """Rejoue une liste de réponses ; enregistre les requêtes reçues dans `calls`."""

    def __init__(self, replies):
        self.replies = list(replies)
        self.calls = []
        self.messages = self

    def stream(self, **kw):
        self.calls.append(kw)
        content, stop = self.replies.pop(0)
        return FakeStream(NS(content=content, stop_reason=stop))
