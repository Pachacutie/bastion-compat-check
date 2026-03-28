"""WSGI entry point for production deployment."""

from bastion_compat.web import create_app

app = create_app()
