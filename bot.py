"""
splash_dex_bot — بوت بناء ملف classes.dex للسبلاش سكرين
"""
import asyncio
import base64
import io
import logging
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

from aiogram import Bot, Dispatcher, F, types
from aiogram.client.default import DefaultBotProperties
from aiogram.filters import Command, BaseFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import (
    BufferedInputFile,
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
)
from PIL import Image

# ──────────────────────────────────────────
# CONFIG
# ──────────────────────────────────────────
BOT_TOKEN = os.environ["BOT_TOKEN"]
# IDs منفصلة بفاصلة: "123456,789012"
ADMIN_IDS: set[int] = {int(x.strip()) for x in os.environ.get("ADMIN_IDS", "0").split(",")}

BASE_DIR  = Path(__file__).parent
SMALI_DIR = BASE_DIR / "smali"          # ملفات smali الأصلية (القوالب)
TOOLS_DIR = BASE_DIR / "tools"
SMALI_JAR = TOOLS_DIR / "smali.jar"

CHUNK_SIZE   = 350    # أقصى طول لكل const-string في Smali
MAX_IMG_SIZE = 300    # أقصى أبعاد الصورة (بالبكسل)

# ──────────────────────────────────────────
# LOGGING
# ──────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)
LOG = logging.getLogger("splash_bot")

# ──────────────────────────────────────────
# FSM STATES
# ──────────────────────────────────────────
class Form(StatesGroup):
    channel_name     = State()   # اسم القناة
    channel_subtitle = State()   # الوصف / السلوجان
    channel_username = State()   # اليوزرنيم (بدون @)
    channel_image    = State()   # اللوغو
    admob_id         = State()   # AdMob Unit ID (اختياري)
    button_text      = State()   # نص زر الاشتراك (اختياري)
    confirm          = State()   # التأكيد


DEFAULT_BTN_TEXT = "اشترك في القناة الآن"

# ──────────────────────────────────────────
# ADMIN FILTER
# ──────────────────────────────────────────
class IsAdmin(BaseFilter):
    async def __call__(self, event: types.TelegramObject) -> bool:
        uid = getattr(getattr(event, "from_user", None), "id", None)
        return uid in ADMIN_IDS

# ──────────────────────────────────────────
# KEYBOARDS
# ──────────────────────────────────────────
def kb_skip(label: str = "تخطي ⏭") -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text=label, callback_data="skip")]]
    )

KB_CONFIRM = InlineKeyboardMarkup(inline_keyboard=[[
    InlineKeyboardButton(text="✅ بناء DEX",  callback_data="build"),
    InlineKeyboardButton(text="🔄 إعادة تشغيل", callback_data="restart"),
    InlineKeyboardButton(text="❌ إلغاء",     callback_data="cancel"),
]])

# ──────────────────────────────────────────
# SMALI BUILDER UTILITIES
# ──────────────────────────────────────────

def _extract_html(smali_text: str) -> str:
    """استخرج HTML الكاملة من قسم const-string chunks في الـ Smali."""
    START = "# ==== HTML CHUNKS ===="
    END   = "# ==== END HTML ===="
    s = smali_text.find(START)
    e = smali_text.find(END)
    if s == -1 or e == -1:
        raise ValueError("لم يُعثر على علامات HTML في SplashActivity.smali")
    section = smali_text[s:e]
    # كل قطعة: const-string v2, "..."
    chunks = re.findall(r'    const-string v2, "([^"]*)"', section)
    return "".join(chunks)


def _html_section(html: str) -> str:
    """أعد بناء قسم Smali من HTML كاملة (تقطيع + invoke-virtual)."""
    append_call = (
        "    invoke-virtual {v1, v2}, "
        "Ljava/lang/StringBuilder;->append(Ljava/lang/String;)Ljava/lang/StringBuilder;"
    )
    lines: list[str] = []
    for i in range(0, len(html), CHUNK_SIZE):
        part = html[i : i + CHUNK_SIZE]
        lines.append(f'    const-string v2, "{part}"')
        lines.append(append_call)
        lines.append("")           # سطر فارغ للمقروئية
    return "\n".join(lines)


def _patch_html(
    html: str,
    *,
    channel_name: str,
    channel_subtitle: str,
    channel_username: str,
    button_text: str,
    image_b64: str,
) -> str:
    """استبدل المتغيرات داخل HTML."""

    # ① الصورة — data:image/png;base64,XXXXX' alt='logo'
    TAG = "data:image/png;base64,"
    i = html.find(TAG)
    if i != -1:
        i += len(TAG)
        j = html.find("'", i)   # نهاية الـ base64
        html = html[:i] + image_b64 + html[j:]

    # ② اسم القناة — <div class='title'>...</div>
    OPEN, CLOSE = "<div class='title'>", "</div>"
    i = html.find(OPEN)
    if i != -1:
        i += len(OPEN)
        j = html.find(CLOSE, i)
        html = html[:i] + channel_name + html[j:]

    # ③ الوصف — <div class='subtitle'>...</div>
    OPEN = "<div class='subtitle'>"
    i = html.find(OPEN)
    if i != -1:
        i += len(OPEN)
        j = html.find(CLOSE, i)
        html = html[:i] + channel_subtitle + html[j:]

    # ④ رابط الزر — href='...'
    BTN = "class='btn'"
    bi  = html.find(BTN)
    if bi != -1:
        HREF = "href='"
        hi = html.find(HREF, bi) + len(HREF)
        hj = html.find("'", hi)
        html = html[:hi] + f"https://t.me/{channel_username}" + html[hj:]

    # ⑤ نص الزر — >...</a>
    bi = html.find(BTN)
    if bi != -1:
        ti = html.find(">", bi) + 1
        tj = html.find("</a>", ti)
        html = html[:ti] + button_text + html[tj:]

    return html


def build_modified_smali(
    *,
    channel_name:     str,
    channel_subtitle: str,
    channel_username: str,
    button_text:      str,
    image_b64:        str,
    admob_id:         str | None,
    out_dir:          Path,
) -> None:
    """اقرأ ملفات smali القالب، عدّلها، واكتبها في out_dir."""
    out_dir.mkdir(parents=True, exist_ok=True)

    # ── SplashActivity.smali ──────────────────────
    src = (SMALI_DIR / "SplashActivity.smali").read_text("utf-8")

    # AdMob Unit ID
    OLD_ADMOB = '"ca-app-pub-4754986736916928/4102584661"'
    if admob_id:
        src = src.replace(OLD_ADMOB, f'"{admob_id}"')
    # إذا لم يُقدَّم AdMob → احذف الـ AdView بتغيير ID لقيمة فارغة (يمنع ظهور الإعلانات)
    else:
        src = src.replace(OLD_ADMOB, '"ca-app-pub-0000000000000000/0000000000"')

    # HTML section
    START_MARK = "# ==== HTML CHUNKS ===="
    END_MARK   = "# ==== END HTML ===="

    full_html    = _extract_html(src)
    patched_html = _patch_html(
        full_html,
        channel_name=channel_name,
        channel_subtitle=channel_subtitle,
        channel_username=channel_username,
        button_text=button_text,
        image_b64=image_b64,
    )
    new_section = _html_section(patched_html)

    sm = src.find(START_MARK)
    em = src.find(END_MARK)
    src = (
        src[: sm + len(START_MARK)]
        + "\n\n"
        + new_section
        + "\n    "
        + src[em:]
    )

    (out_dir / "SplashActivity.smali").write_text(src, "utf-8")

    # ── SplashActivity$4.smali ────────────────────
    src4 = (SMALI_DIR / "SplashActivity$4.smali").read_text("utf-8")
    src4 = src4.replace(
        '"https://t.me/Bayan_x777"',
        f'"https://t.me/{channel_username}"',
    )
    (out_dir / "SplashActivity$4.smali").write_text(src4, "utf-8")

    # ── $5 & $6 — نسخ بدون تعديل ─────────────────
    for fname in ("SplashActivity$5.smali", "SplashActivity$6.smali"):
        shutil.copy(SMALI_DIR / fname, out_dir / fname)

    LOG.info("Smali files written to %s", out_dir)


def compile_dex(smali_dir: Path) -> bytes:
    """شغّل smali.jar لتجميع الملفات → DEX. يُرجع بايتات الـ DEX."""
    if not SMALI_JAR.exists():
        raise FileNotFoundError(
            f"❌ smali.jar غير موجود في:\n{SMALI_JAR}\n\n"
            "⬇️ نزّله من:\n"
            "https://github.com/JesusFreke/smali/releases\n"
            "وضعه في مجلد tools/"
        )
    with tempfile.TemporaryDirectory() as tmp:
        out_dex = Path(tmp) / "classes.dex"
        result = subprocess.run(
            ["java", "-jar", str(SMALI_JAR), "assemble",
             str(smali_dir), "-o", str(out_dex)],
            capture_output=True, text=True, timeout=90,
        )
        if result.returncode != 0:
            err = (result.stderr or result.stdout or "خطأ غير معروف").strip()
            raise RuntimeError(err)
        LOG.info("DEX built: %d bytes", out_dex.stat().st_size)
        return out_dex.read_bytes()


def image_to_b64(image_bytes: bytes) -> str:
    """حوّل الصورة → PNG مضغوط → base64 string."""
    img = Image.open(io.BytesIO(image_bytes)).convert("RGBA")
    img.thumbnail((MAX_IMG_SIZE, MAX_IMG_SIZE), Image.LANCZOS)
    buf = io.BytesIO()
    img.save(buf, format="PNG", optimize=True)
    return base64.b64encode(buf.getvalue()).decode()


# ──────────────────────────────────────────
# BOT & DISPATCHER
# ──────────────────────────────────────────
bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode="HTML"))
dp  = Dispatcher(storage=MemoryStorage())

# تطبيق فلتر الأدمن على كل المعالجات
dp.message.filter(IsAdmin())
dp.callback_query.filter(IsAdmin())


# ──────────────────────────────────────────
# /start
# ──────────────────────────────────────────
@dp.message(Command("start"))
async def cmd_start(msg: Message, state: FSMContext) -> None:
    await state.clear()
    await msg.answer(
        "🔨 <b>بوت بناء DEX — SplashActivity</b>\n\n"
        "سيتم تخصيص ملف <code>classes.dex</code> بمعلومات قناتك خطوة بخطوة.\n\n"
        "📌 <b>الخطوة ١/٦ — اسم القناة:</b>\n"
        "<i>مثال: قناة بيان</i>"
    )
    await state.set_state(Form.channel_name)


# ──────────────────────────────────────────
# STEP 1 — اسم القناة
# ──────────────────────────────────────────
@dp.message(Form.channel_name, F.text)
async def step_channel_name(msg: Message, state: FSMContext) -> None:
    name = msg.text.strip().replace('"', '')  # تجنّب كسر Smali strings
    await state.update_data(channel_name=name)
    await msg.answer(
        f"✅ <b>اسم القناة:</b> {name}\n\n"
        "📝 <b>الخطوة ٢/٦ — وصف القناة / السلوجان:</b>\n"
        "<i>مثال: شروحات تقنية مبسطة</i>"
    )
    await state.set_state(Form.channel_subtitle)


# ──────────────────────────────────────────
# STEP 2 — الوصف
# ──────────────────────────────────────────
@dp.message(Form.channel_subtitle, F.text)
async def step_subtitle(msg: Message, state: FSMContext) -> None:
    sub = msg.text.strip().replace('"', '')
    await state.update_data(channel_subtitle=sub)
    await msg.answer(
        f"✅ <b>الوصف:</b> {sub}\n\n"
        "🔗 <b>الخطوة ٣/٦ — يوزرنيم القناة (بدون @):</b>\n"
        "<i>مثال: Bayan_x777</i>"
    )
    await state.set_state(Form.channel_username)


# ──────────────────────────────────────────
# STEP 3 — اليوزرنيم
# ──────────────────────────────────────────
@dp.message(Form.channel_username, F.text)
async def step_username(msg: Message, state: FSMContext) -> None:
    username = msg.text.strip().lstrip("@")
    if not re.match(r'^[A-Za-z0-9_]{1,64}$', username):
        await msg.answer(
            "⚠️ يوزرنيم غير صحيح!\n"
            "استخدم فقط: <code>A-Z a-z 0-9 _</code>"
        )
        return
    await state.update_data(channel_username=username)
    await msg.answer(
        f"✅ <b>القناة:</b> @{username}\n\n"
        "🖼 <b>الخطوة ٤/٦ — لوغو/شعار القناة:</b>\n"
        "• أرسله كـ <b>ملف (Document)</b> للحفاظ على الجودة\n"
        "• أو كصورة عادية (سيتم ضغطها)\n"
        "<i>الصورة ستُحوَّل تلقائياً إلى PNG بحجم أقصى ٣٠٠×٣٠٠</i>"
    )
    await state.set_state(Form.channel_image)


# ──────────────────────────────────────────
# STEP 4 — الصورة
# ──────────────────────────────────────────
@dp.message(Form.channel_image, F.photo | F.document)
async def step_image(msg: Message, state: FSMContext) -> None:
    proc_msg = await msg.answer("⏳ جاري معالجة الصورة...")
    try:
        if msg.photo:
            file_id = msg.photo[-1].file_id
        else:
            mime = (msg.document.mime_type or "").lower()
            if not mime.startswith("image/"):
                await proc_msg.edit_text("⚠️ أرسل ملف صورة (PNG, JPG, WEBP…)")
                return
            file_id = msg.document.file_id

        file = await bot.get_file(file_id)
        buf  = io.BytesIO()
        await bot.download_file(file.file_path, buf)
        image_b64 = image_to_b64(buf.getvalue())

        await state.update_data(image_b64=image_b64)
        await proc_msg.edit_text(
            f"✅ <b>تم ترميز الصورة</b> ({len(image_b64):,} حرف base64)\n\n"
            "💰 <b>الخطوة ٥/٦ — AdMob Unit ID:</b>\n"
            "<i>مثال: ca-app-pub-1234567890/9876543210</i>",
            reply_markup=kb_skip("تخطي (بدون إعلانات) ⏭")
        )
        await state.set_state(Form.admob_id)

    except Exception as exc:
        LOG.exception("Image processing error")
        await proc_msg.edit_text(f"❌ خطأ في الصورة: <code>{exc}</code>")


@dp.message(Form.channel_image)
async def step_image_wrong(msg: Message) -> None:
    await msg.answer("⚠️ أرسل صورة أو ملف صورة من فضلك.")


# ──────────────────────────────────────────
# STEP 5 — AdMob ID  (اختياري)
# ──────────────────────────────────────────
BTN_TEXT_PROMPT = (
    "🔘 <b>الخطوة ٦/٦ — نص زر الاشتراك:</b>\n"
    f"<i>الافتراضي: {DEFAULT_BTN_TEXT}</i>"
)

@dp.callback_query(F.data == "skip", Form.admob_id)
async def skip_admob(cb: CallbackQuery, state: FSMContext) -> None:
    await state.update_data(admob_id=None)
    await cb.message.edit_text(
        "⏭ <b>تم تخطي AdMob</b> (سيُستخدم ID افتراضي معطَّل)\n\n" + BTN_TEXT_PROMPT,
        reply_markup=kb_skip(f'استخدام الافتراضي "{DEFAULT_BTN_TEXT}" ⏭')
    )
    await state.set_state(Form.button_text)
    await cb.answer()


@dp.message(Form.admob_id, F.text)
async def step_admob(msg: Message, state: FSMContext) -> None:
    admob = msg.text.strip()
    # تحقق بسيط من الشكل
    if not re.match(r'^ca-app-pub-\d+/\d+$', admob):
        await msg.answer(
            "⚠️ شكل AdMob ID غير صحيح!\n"
            "المطلوب: <code>ca-app-pub-XXXXXXXXXX/XXXXXXXXXX</code>"
        )
        return
    await state.update_data(admob_id=admob)
    await msg.answer(
        f"✅ <b>AdMob:</b> <code>{admob}</code>\n\n" + BTN_TEXT_PROMPT,
        reply_markup=kb_skip(f'استخدام الافتراضي ⏭')
    )
    await state.set_state(Form.button_text)


# ──────────────────────────────────────────
# STEP 6 — نص الزر  (اختياري)
# ──────────────────────────────────────────
@dp.callback_query(F.data == "skip", Form.button_text)
async def skip_btn_text(cb: CallbackQuery, state: FSMContext) -> None:
    await state.update_data(button_text=DEFAULT_BTN_TEXT)
    await _show_confirm(cb.message, state)
    await cb.answer()


@dp.message(Form.button_text, F.text)
async def step_button_text(msg: Message, state: FSMContext) -> None:
    btn = msg.text.strip().replace('"', '')
    await state.update_data(button_text=btn)
    await _show_confirm(msg, state)


# ──────────────────────────────────────────
# CONFIRM
# ──────────────────────────────────────────
async def _show_confirm(obj: Message | types.Message, state: FSMContext) -> None:
    data = await state.get_data()
    summary = (
        "📋 <b>ملخص — راجع البيانات قبل البناء:</b>\n\n"
        f"📌 <b>اسم القناة:</b> {data['channel_name']}\n"
        f"📝 <b>الوصف:</b> {data['channel_subtitle']}\n"
        f"🔗 <b>اليوزرنيم:</b> @{data['channel_username']}\n"
        f"🖼 <b>الصورة:</b> ✅ ({len(data['image_b64']):,} حرف)\n"
        f"💰 <b>AdMob:</b> {data.get('admob_id') or '⚠️ معطَّل'}\n"
        f"🔘 <b>نص الزر:</b> {data['button_text']}\n\n"
        "اضغط <b>بناء DEX</b> لإنشاء الملف."
    )
    if hasattr(obj, "edit_text"):
        await obj.edit_text(summary, reply_markup=KB_CONFIRM)
    else:
        await obj.answer(summary, reply_markup=KB_CONFIRM)
    await state.set_state(Form.confirm)


@dp.callback_query(F.data == "cancel", Form.confirm)
async def cancel_build(cb: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    await cb.message.edit_text("❌ تم الإلغاء. أرسل /start للبدء من جديد.")
    await cb.answer()


@dp.callback_query(F.data == "restart", Form.confirm)
async def restart_build(cb: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    await cb.message.edit_text("🔄 إعادة تشغيل... أرسل /start")
    await cb.answer()


@dp.callback_query(F.data == "build", Form.confirm)
async def do_build(cb: CallbackQuery, state: FSMContext) -> None:
    data = await state.get_data()
    await cb.answer("⚙️ جاري البناء...")
    status = await cb.message.edit_text("⚙️ <b>الخطوة ١/٢:</b> تعديل ملفات Smali...")

    try:
        with tempfile.TemporaryDirectory() as tmp:
            work = Path(tmp) / "smali"

            build_modified_smali(
                channel_name=data["channel_name"],
                channel_subtitle=data["channel_subtitle"],
                channel_username=data["channel_username"],
                button_text=data["button_text"],
                image_b64=data["image_b64"],
                admob_id=data.get("admob_id"),
                out_dir=work,
            )

            await status.edit_text("⚙️ <b>الخطوة ٢/٢:</b> تجميع Smali ← DEX...")
            dex_bytes = compile_dex(work)

        fname = (
            f"splash_{data['channel_username']}.dex"
            .replace(" ", "_")[:50]
        )
        caption = (
            f"✅ <b>classes.dex جاهز!</b>\n\n"
            f"📦 الحجم: {len(dex_bytes):,} بايت\n"
            f"📌 القناة: @{data['channel_username']}\n\n"
            "ضع هذا الملف في مشروعك (<code>app/src/main/assets/</code>"
            " أو مكانه الأصلي)."
        )

        await state.clear()
        await status.edit_text(
            "✅ <b>تم البناء بنجاح!</b> جاري الإرسال..."
        )
        await bot.send_document(
            cb.from_user.id,
            document=BufferedInputFile(dex_bytes, filename=fname),
            caption=caption,
        )

    except FileNotFoundError as exc:
        await status.edit_text(str(exc))

    except RuntimeError as exc:
        err = str(exc)[:800]
        await status.edit_text(
            f"❌ <b>خطأ في smali.jar:</b>\n<pre>{err}</pre>"
        )

    except Exception as exc:
        LOG.exception("Unexpected build error")
        await status.edit_text(
            f"❌ <b>خطأ غير متوقع:</b>\n<code>{exc}</code>"
        )


# ──────────────────────────────────────────
# /cancel في أي وقت
# ──────────────────────────────────────────
@dp.message(Command("cancel"))
async def cmd_cancel(msg: Message, state: FSMContext) -> None:
    await state.clear()
    await msg.answer("❌ تم الإلغاء. أرسل /start للبدء من جديد.")


# ──────────────────────────────────────────
# /status — للتحقق من إعداد الأدوات
# ──────────────────────────────────────────
@dp.message(Command("status"))
async def cmd_status(msg: Message) -> None:
    java_ok  = shutil.which("java") is not None
    smali_ok = SMALI_JAR.exists()
    smali_files = list(SMALI_DIR.glob("*.smali"))

    lines = [
        "🔧 <b>حالة الأدوات:</b>\n",
        f"☕️ Java: {'✅' if java_ok else '❌ غير مثبّت'}",
        f"📦 smali.jar: {'✅' if smali_ok else '❌ غير موجود'}",
        f"📁 ملفات Smali: {len(smali_files)} ملف",
    ]
    if not smali_ok:
        lines.append(
            "\n⬇️ <b>تحميل smali.jar:</b>\n"
            "https://github.com/JesusFreke/smali/releases\n"
            "ضعه في: <code>tools/smali.jar</code>"
        )
    await msg.answer("\n".join(lines))


# ──────────────────────────────────────────
# MAIN
# ──────────────────────────────────────────
async def main() -> None:
    LOG.info("Bot starting... Admin IDs: %s", ADMIN_IDS)

    # تحقق من Java عند التشغيل
    if not shutil.which("java"):
        LOG.warning("⚠️  Java غير موجود — compile_dex سيفشل!")
    if not SMALI_JAR.exists():
        LOG.warning("⚠️  smali.jar غير موجود في %s", SMALI_JAR)

    await dp.start_polling(bot, allowed_updates=["message", "callback_query"])


if __name__ == "__main__":
    asyncio.run(main())
