#!/usr/bin/env python3
"""
run.py — تشغيل البوت مع تحميل .env تلقائياً
"""
from dotenv import load_dotenv
load_dotenv()          # يحمّل .env قبل أي شيء

import bot             # noqa: E402 — يشتغل بعد تحميل المتغيرات
import asyncio

asyncio.run(bot.main())
