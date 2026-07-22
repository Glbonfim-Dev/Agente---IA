"""Inicia o chatbot sem ambiente virtual ou pacotes externos."""

from __future__ import annotations

import threading
import webbrowser

from app import serve


if __name__ == "__main__":
    threading.Timer(0.8, lambda: webbrowser.open("http://localhost:8501")).start()
    serve()
