"""A project, a home with an endpoint file, the helper loaded to be called in this process, and a fake Ollama server.

The fake listens on the loopback address inside the test process, records each request (the request line, the headers in the
order they came and the body), and answers as the test says: a status and a body, a delay, a body one byte at a time, or no
answer at all. No test starts a real Ollama or reaches another host.

The certificates under ``certs/`` are throwaway keys made once with ``openssl`` for the HTTPS tests (a certificate for
127.0.0.1 and localhost, one for another name only, and one that expired in 2000). They guard nothing."""

import http.server
import io
import json
import os
import socket
import ssl
import struct
import tempfile
import threading
import time
import unittest
import unittest.mock

from tests import support_helpers

CERTS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "certs")
STANDARD_CHAT = ("llama3:8b", "other:1b", "gpt-oss:20b", "gpt-5")
STANDARD_EMBED = ("nomic-embed-text", "mxbai-embed-large")


def chat(content="the reply", **fields):
    """The body of a finished, plain reply of the server."""
    body = {"model": "llama3:8b", "message": {"role": "assistant", "content": content}, "done": True,
            "done_reason": "stop", "prompt_eval_count": 12, "eval_count": 5}
    body.update(fields)
    return body


class Server6(http.server.ThreadingHTTPServer):
    address_family = socket.AF_INET6


class Stall:
    """A listener on 127.0.0.1 that accepts connections and then says nothing, so that a TLS handshake never finishes."""

    def __init__(self):
        self.listener = socket.socket()
        self.listener.bind(("127.0.0.1", 0))
        self.listener.listen(5)
        self.listener.settimeout(0.05)
        self.port = self.listener.getsockname()[1]
        self.held = []
        self.running = True
        self.thread = threading.Thread(target=self.accept, daemon=True)
        self.thread.start()

    def accept(self):
        while self.running:
            try:
                self.held.append(self.listener.accept()[0])
            except OSError:
                pass

    def close(self):
        self.running = False
        self.thread.join(5)
        for connection in self.held:
            connection.close()
        self.listener.close()


class Fake:
    """A server on 127.0.0.1 (or ::1 with `ipv6`). `context` makes it speak TLS."""

    def __init__(self, context=None, ipv6=False):
        self.requests = []
        self.spec = {"body": json.dumps(chat()).encode()}
        self.release = threading.Event()
        fake = self

        class Handler(http.server.BaseHTTPRequestHandler):
            protocol_version = "HTTP/1.1"

            def log_message(self, *args):
                pass

            def do_POST(self):
                length = int(self.headers.get("Content-Length", "0"))
                body = self.rfile.read(length)
                fake.requests.append({"method": self.command, "path": self.path,
                                      "headers": [(k, v) for k, v in self.headers.items()], "body": body})
                fake.answer(self)

            def do_GET(self):
                length = int(self.headers.get("Content-Length", "0"))
                body = self.rfile.read(length) if length else b""
                fake.requests.append({"method": self.command, "path": self.path,
                                      "headers": [(k, v) for k, v in self.headers.items()], "body": body})
                fake.answer(self)

        self.server = (Server6 if ipv6 else http.server.ThreadingHTTPServer)(("::1" if ipv6 else "127.0.0.1", 0), Handler)
        self.server.daemon_threads = True
        self.server.handle_error = lambda request, client_address: None
        if context is not None:
            self.server.socket = context.wrap_socket(self.server.socket, server_side=True)
        self.port = self.server.server_address[1]
        self.thread = threading.Thread(target=self.server.serve_forever, kwargs={"poll_interval": 0.05}, daemon=True)
        self.thread.start()

    def reply(self, body=None, **spec):
        """Answer the next requests with `body` (a dict is written as JSON, bytes as they are) and the fields of `spec`:
        ``status``, ``headers``, ``delay`` (seconds before answering), ``drip`` (seconds between bytes), ``drop``
        (close the connection with no answer), ``declare_length`` (a Content-Length other than the body's) and ``abort``
        (send half the body and then reset the connection)."""
        if isinstance(body, (dict, list)):
            body = json.dumps(body).encode()
        spec["body"] = body if body is not None else b""
        self.spec = spec

    def answer(self, handler):
        spec = self.spec
        handler.close_connection = True
        if spec.get("drop"):
            return
        if spec.get("delay"):
            self.release.wait(spec["delay"])
        body = spec["body"]
        handler.send_response(spec.get("status", 200))
        for name, value in spec.get("headers", {}).items():
            handler.send_header(name, value)
        handler.send_header("Content-Type", "application/json")
        handler.send_header("Content-Length", str(spec.get("declare_length", len(body))))
        handler.send_header("Connection", "close")
        handler.end_headers()
        try:
            if spec.get("abort"):
                handler.wfile.write(body[:len(body) // 2])
                handler.wfile.flush()
                handler.connection.setsockopt(socket.SOL_SOCKET, socket.SO_LINGER, struct.pack("ii", 1, 0))
                handler.connection.close()
                return
            if spec.get("drip"):
                for index in range(len(body)):
                    handler.wfile.write(body[index:index + 1])
                    handler.wfile.flush()
                    time.sleep(spec["drip"])
            else:
                handler.wfile.write(body)
        except OSError:
            pass

    def close(self):
        self.release.set()
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(5)


def server_context(name):
    """A server-side TLS context with the certificate and key `name` under ``certs/``."""
    context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    context.load_cert_chain(os.path.join(CERTS, name + ".pem"), os.path.join(CERTS, name + ".key"))
    return context


def trusting(name):
    """A client-side context, as the helper's own is built, that trusts only the certificate `name` under ``certs/``."""
    context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
    context.minimum_version = ssl.TLSVersion.TLSv1_2
    context.load_verify_locations(cafile=os.path.join(CERTS, name + ".pem"))
    return context


class Bridge(unittest.TestCase):
    """The helper, a project at `self.root`, a home with a guarded store at `self.store` and a fake server at `self.fake`."""

    @classmethod
    def setUpClass(cls):
        cls.helper = support_helpers.load("ask-ollama")

    def setUp(self):
        holder = tempfile.TemporaryDirectory()
        self.addCleanup(holder.cleanup)
        self.base = os.path.realpath(holder.name)
        self.root = os.path.join(self.base, "project")
        self.home = os.path.join(self.base, "home")
        self.store = os.path.join(self.home, ".config", "project-workbench")
        for folder in (os.path.join(self.root, ".git"), os.path.join(self.root, ".workbench"),
                       os.path.join(self.root, "docs"), self.store):
            os.makedirs(folder)
        os.chmod(self.store, 0o700)
        with open(os.path.join(self.root, ".workbench", "manifest.json"), "w") as handle:
            handle.write("{}\n")
        with open(os.path.join(self.root, "docs", "plan.md"), "w") as handle:
            handle.write("# Plan\n")
        patch = unittest.mock.patch.dict(os.environ, {"HOME": self.home})
        patch.start()
        self.addCleanup(patch.stop)
        self.fake = Fake()
        self.addCleanup(self.fake.close)
        self.endpoints()

    def record(self, models=None, chat=(), embed=(), context=8192, default_context=None, bytes_per_token=None, **fields):
        """A record of format 2. Without `models`, it configures the standard models (STANDARD_CHAT and STANDARD_EMBED), the
        names in `chat` and `embed`, and the record's own `default_model` and `embedding_model`, each with the window `context`
        (and `default_context` and `bytes_per_token` when they are given)."""
        record = {"scheme": "http", "host": "127.0.0.1", "port": self.fake.port, "location": "this-machine",
                  "authenticated": False, "default_model": "llama3:8b"}
        record.update(fields)
        if models is None:
            kinds = {name: "chat" for name in STANDARD_CHAT + tuple(chat)}
            kinds.update({name: "embedding" for name in STANDARD_EMBED + tuple(embed)})
            for key, kind in (("default_model", "chat"), ("embedding_model", "embedding")):
                name = record.get(key)
                if isinstance(name, str) and name not in kinds:
                    kinds[name] = kind
            models = {}
            for name, kind in kinds.items():
                section = {"kind": kind, "context": context}
                if default_context is not None:
                    section["default_context"] = default_context
                if bytes_per_token is not None:
                    section["bytes_per_token"] = bytes_per_token
                models[name] = section
        record["models"] = models
        return {key: value for key, value in record.items() if value is not None}

    def endpoints(self, default="ned", **records):
        """Write the endpoint file: a record `ned` (as ``record()`` makes it) unless `records` gives others."""
        document = {"format": 2, "endpoints": records or {"ned": self.record()}}
        if default is not None:
            document["default"] = default
        self.write_endpoint_file(json.dumps(document).encode())

    def write_endpoint_file(self, data):
        with open(os.path.join(self.store, "endpoints.json"), "wb") as handle:
            handle.write(data)

    def ask(self, *args, prompt=b"Review docs/plan.md\n", cwd=None, command="ask"):
        """``(code, standard output, standard error)`` of ``ask-ollama <command> <args>`` with `prompt` on standard input."""
        out, err = io.StringIO(), io.StringIO()
        code = self.helper.main([command, *args], io.BytesIO(prompt), out, err, cwd or self.root)
        return code, out.getvalue(), err.getvalue()

    def document(self, *args, **kwargs):
        """The one object a call printed, after the checks every call must pass."""
        code, out, err = self.ask(*args, **kwargs)
        self.assertEqual("", err)
        self.assertTrue(out.endswith("\n") and "\n" not in out[:-1], "not one line")
        self.assertLessEqual(len(out.encode()), self.helper.MAX_OBJECT)
        document = json.loads(out)
        self.assertEqual(code, 0 if document["ok"] else 1)
        self.assertEqual(2, document["contract"])
        self.assertEqual("ollama", document["vendor"])
        self.assertNotIn("127.0.0.1", out)
        self.assertNotIn(str(self.fake.port), out)
        return document

    def failed(self, *args, error, detail=None, retryable=False, **kwargs):
        document = self.document(*args, **kwargs)
        self.assertEqual((False, error, detail, retryable),
                         (document["ok"], document["error"], document["detail"], document["retryable"]), document)
        self.assertEqual(set(document), {"contract", "ok", "vendor", "error", "detail", "retryable", "message"})
        self.assertLessEqual(len(document["message"]), 500)
        return document

    def refused(self, *args, contains="", **kwargs):
        """A refusal: one ``refused:`` line, nothing on standard output, nothing sent, no address in it."""
        before = len(self.fake.requests)
        code, out, err = self.ask(*args, **kwargs)
        self.assertEqual((1, ""), (code, out), err)
        self.assertTrue(err.startswith("refused: ") and err.count("\n") == 1, err)
        self.assertIn(contains, err)
        self.assertEqual(before, len(self.fake.requests), "a request was sent")
        self.assertNotIn("127.0.0.1", err)
        self.assertNotIn(str(self.fake.port), err)
        return err

    def tree(self, top):
        found = {}
        for base, dirs, files in os.walk(top):
            for name in dirs + files:
                full = os.path.join(base, name)
                if os.path.islink(full):
                    found[os.path.relpath(full, top)] = os.readlink(full)
                elif os.path.isdir(full):
                    found[os.path.relpath(full, top)] = None
                else:
                    with open(full, "rb") as handle:
                        found[os.path.relpath(full, top)] = handle.read()
        return found
