"""Interface web : un chat dans le navigateur (FastAPI + streaming SSE)."""
import json
import queue
import threading
import uuid

import openai
from fastapi import FastAPI
from fastapi.responses import HTMLResponse, StreamingResponse
from pydantic import BaseModel

from .config import make_client
from .loop import SYSTEM, fmt_args, run
from .memory import REMEMBER_TOOL, remember, system_with_memory
from .subagent import DELEGATE_TOOL, make_delegate
from .tools import TOOLS, default_handlers

PAGE = """<!doctype html><html lang="fr"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Agent</title>
<style>
 body{font:16px system-ui;max-width:760px;margin:0 auto;padding:16px;background:#fafafa;color:#222}
 #log{display:flex;flex-direction:column;gap:10px;margin-bottom:80px}
 .m{padding:10px 14px;border-radius:12px;white-space:pre-wrap;max-width:90%}
 .user{background:#2563eb;color:#fff;align-self:flex-end}.agent{background:#fff;border:1px solid #ddd}
 .tool{font:13px ui-monospace,monospace;color:#666;align-self:flex-start}
 form{position:fixed;bottom:0;left:0;right:0;display:flex;gap:8px;padding:12px;background:#fafafa;max-width:760px;margin:auto}
 input{flex:1;padding:10px;border:1px solid #ccc;border-radius:8px;font:inherit}button{padding:10px 16px;font:inherit}
 @media(prefers-color-scheme:dark){body,form{background:#16181d;color:#eee}.agent{background:#22252c;border-color:#333}input{background:#22252c;color:#eee;border-color:#444}}
</style>
<div id="log"></div>
<form id="f"><input id="q" autocomplete="off" placeholder="Écris à l'agent…" autofocus><button>Envoyer</button></form>
<script>
const sid=crypto.randomUUID(),log=document.getElementById('log');
const add=(c,t)=>{const d=document.createElement('div');d.className='m '+c;d.textContent=t;log.append(d);scrollTo(0,document.body.scrollHeight);return d};
f.onsubmit=async e=>{e.preventDefault();const text=q.value.trim();if(!text)return;q.value='';add('user',text);
 let cur=null;const r=await fetch('/chat',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({session_id:sid,message:text})});
 const rd=r.body.getReader(),dec=new TextDecoder();let buf='';
 for(;;){const{done,value}=await rd.read();if(done)break;buf+=dec.decode(value,{stream:true});
  const parts=buf.split('\\n\\n');buf=parts.pop();
  for(const p of parts){const ev=JSON.parse(p.slice(6));
   if(ev.type==='text'){cur=cur||add('agent','');cur.textContent+=ev.text}
   else if(ev.type==='tool'){cur=null;add('tool','🔧 '+ev.name+'('+ev.args+')')}
   else if(ev.type==='error'){add('tool','⚠️ '+ev.message)}}}};
</script></html>"""


class ChatIn(BaseModel):
    session_id: str
    message: str


def create_app(client=None) -> FastAPI:
    app = FastAPI(title="Agent")
    sessions: dict[str, list] = {}
    state = {"client": client}

    def get_client():
        state["client"] = state["client"] or make_client()
        return state["client"]

    @app.get("/", response_class=HTMLResponse)
    def index() -> str:
        return PAGE

    @app.post("/chat")
    def chat(body: ChatIn):
        messages = sessions.setdefault(body.session_id or str(uuid.uuid4()), [])
        start = len(messages)
        messages.append({"role": "user", "content": body.message})
        events: queue.Queue = queue.Queue()
        c = get_client()

        def on_tool(name: str, args: dict) -> None:
            events.put({"type": "tool", "name": name, "args": fmt_args(args)})

        # Pas d'approbation possible dans le navigateur : run_bash est refusé.
        handlers = {
            **default_handlers(lambda cmd: False),
            "remember": remember,
            "delegate": make_delegate(c, on_tool),
        }

        def worker() -> None:
            try:
                run(
                    c, messages, [*TOOLS, REMEMBER_TOOL, DELEGATE_TOOL], handlers,
                    system=system_with_memory(SYSTEM),
                    on_text=lambda t: events.put({"type": "text", "text": t}),
                    on_tool=on_tool,
                )
            except openai.OpenAIError as e:
                del messages[start:]
                events.put({"type": "error", "message": str(e)})
            finally:
                events.put(None)

        threading.Thread(target=worker, daemon=True).start()

        def stream():
            while (ev := events.get()) is not None:
                yield f"data: {json.dumps(ev, ensure_ascii=False)}\n\n"

        return StreamingResponse(stream(), media_type="text/event-stream")

    return app


app = create_app()

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=8000)
