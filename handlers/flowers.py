"""Flower catalog and AI recommendation handlers."""
from __future__ import annotations

import os
from functools import wraps
from typing import Any, Dict

import httpx
import structlog
from telegram import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    ReplyKeyboardMarkup,
    Update,
    WebAppInfo,
)
from telegram.ext import (
    CallbackQueryHandler,
    CommandHandler
