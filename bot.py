import requests
import time
import json
import os
import uuid
from flask import Flask, request, jsonify

# =========================================
# SETTINGS
# =========================================

TOKEN = os.environ.get("RUBIKA_TOKEN", "").strip()

MY_CHAT_ID = "b0HitaY0yT308095415a5973d55ef43d"

BASE = f"https://botapi.rubika.ir/v3/{TOKEN}"

OFFSET_FILE = "bot_offset.json"
MESSAGES_FILE = "bot_messages.json"
INIT_FILE = "bot_initialized.json"
REPLY_MAP_FILE = "bot_reply_map.json"
BANNED_FILE = "bot_banned.json"

TEMP_DIR = "/tmp/temp_images"

os.makedirs(TEMP_DIR, exist_ok=True)


# =========================================
# JSON
# =========================================

def load_json(filename, default):

    if not os.path.exists(filename):
        return default

    try:

        with open(
            filename,
            "r",
            encoding="utf-8"
        ) as file:

            return json.load(file)

    except Exception as e:

        print("LOAD ERROR:", filename, e)

        return default


def save_json(filename, data):

    try:

        with open(
            filename,
            "w",
            encoding="utf-8"
        ) as file:

            json.dump(
                data,
                file,
                ensure_ascii=False,
                indent=2
            )

        return True

    except Exception as e:

        print("SAVE ERROR:", e)

        return False


# =========================================
# LOAD DATA
# =========================================

offset_id = load_json(
    OFFSET_FILE,
    None
)

messages = load_json(
    MESSAGES_FILE,
    {}
)

initialized = load_json(
    INIT_FILE,
    False
)

reply_map = load_json(
    REPLY_MAP_FILE,
    {}
)

banned_users = load_json(
    BANNED_FILE,
    []
)


if not isinstance(messages, dict):
    messages = {}

if not isinstance(reply_map, dict):
    reply_map = {}

if not isinstance(banned_users, list):
    banned_users = []

banned_users = [
    str(x)
    for x in banned_users
]


# =========================================
# MESSAGE NUMBER
# =========================================

if messages:

    try:

        message_number = max(
            int(x)
            for x in messages.keys()
        )

    except:

        message_number = 0

else:

    message_number = 0


# =========================================
# SEND MESSAGE
# =========================================

def send_message(chat_id, text):

    if not chat_id:

        print("SEND ERROR: empty chat_id")

        return None

    while True:

        try:

            response = requests.post(
                f"{BASE}/sendMessage",
                json={
                    "chat_id": str(chat_id),
                    "text": str(text)
                },
                timeout=20
            )

            result = response.json()

            print("SEND:", result)

            if result.get("status") == "OK":

                time.sleep(1.5)

                return result.get(
                    "data",
                    {}
                ).get(
                    "message_id"
                )

            if result.get("status") == "TOO_REQUESTS":

                print(
                    "⏳ TOO_REQUESTS - waiting 6 seconds..."
                )

                time.sleep(6)

                continue

            print(
                "SEND FAILED:",
                result
            )

            return None

        except Exception as e:

            print(
                "SEND EXCEPTION:",
                e
            )

            time.sleep(5)


# =========================================
# SEND FILE
# فقط برای عکس
# =========================================

def send_file(chat_id, file_id, text=""):

    try:

        data = {
            "chat_id": str(chat_id),
            "file_id": str(file_id)
        }

        if text:

            data["text"] = str(text)

        response = requests.post(
            f"{BASE}/sendFile",
            json=data,
            timeout=60
        )

        result = response.json()

        print(
            "SEND FILE:",
            result
        )

        if result.get("status") != "OK":

            return None

        time.sleep(1.5)

        return result.get(
            "data",
            {}
        ).get(
            "message_id"
        )

    except Exception as e:

        print(
            "SEND FILE ERROR:",
            e
        )

        return None


# =========================================
# GET FILE
# =========================================

def get_file(file_id):

    try:

        response = requests.post(
            f"{BASE}/getFile",
            json={
                "file_id": str(file_id)
            },
            timeout=30
        )

        result = response.json()

        print(
            "GET FILE:",
            result
        )

        if result.get("status") != "OK":

            return None

        return result.get(
            "data",
            {}
        )

    except Exception as e:

        print(
            "GET FILE ERROR:",
            e
        )

        return None


# =========================================
# IMAGE CHECK
# =========================================

def is_image(file_info):

    if not file_info:

        return False

    filename = str(
        file_info.get(
            "file_name",
            ""
        )
    ).lower()

    return filename.endswith(
        (
            ".jpg",
            ".jpeg",
            ".png",
            ".webp",
            ".gif"
        )
    )


# =========================================
# TRANSFER IMAGE
# =========================================

def transfer_image(
    source_file_id,
    source_file_name,
    target_chat_id,
    caption=""
):

    temp_path = None

    try:

        file_data = get_file(
            source_file_id
        )

        if not file_data:

            return None

        download_url = file_data.get(
            "download_url"
        )

        if not download_url:

            print(
                "❌ download_url not found"
            )

            return None

        safe_name = os.path.basename(
            source_file_name or "image.jpg"
        )

        temp_path = os.path.join(
            TEMP_DIR,
            str(uuid.uuid4())
            + "_"
            + safe_name
        )

        response = requests.get(
            download_url,
            timeout=120
        )

        response.raise_for_status()

        with open(
            temp_path,
            "wb"
        ) as file:

            file.write(
                response.content
            )

        response = requests.post(
            f"{BASE}/requestSendFile",
            json={
                "type": "Image"
            },
            timeout=30
        )

        result = response.json()

        print(
            "REQUEST IMAGE:",
            result
        )

        if result.get("status") != "OK":

            return None

        upload_url = result.get(
            "data",
            {}
        ).get(
            "upload_url"
        )

        if not upload_url:

            print(
                "❌ upload_url not found"
            )

            return None

        with open(
            temp_path,
            "rb"
        ) as file:

            upload_response = requests.post(
                upload_url,
                files={
                    "file": file
                },
                timeout=180
            )

        upload_result = upload_response.json()

        print(
            "UPLOAD IMAGE:",
            upload_result
        )

        if upload_result.get("status") != "OK":

            return None

        new_file_id = upload_result.get(
            "data",
            {}
        ).get(
            "file_id"
        )

        if not new_file_id:

            return None

        return send_file(
            target_chat_id,
            new_file_id,
            caption
        )

    except Exception as e:

        print(
            "TRANSFER IMAGE ERROR:",
            e
        )

        return None

    finally:

        if temp_path:

            try:

                if os.path.exists(
                    temp_path
                ):

                    os.remove(
                        temp_path
                    )

            except:

                pass


# =========================================
# FORWARD NOTICE
# =========================================

def get_forward_notice(new_message):

    forwarded = new_message.get(
        "forwarded_from"
    )

    if not forwarded:

        return ""

    text = (
        "\n\n"
        "📤 این پیام فوروارد شده است."
    )

    type_from = forwarded.get(
        "type_from"
    )

    if type_from:

        text += (
            f"\nمبدأ: {type_from}"
        )

    from_chat_id = forwarded.get(
        "from_chat_id"
    )

    if from_chat_id:

        text += (
            f"\nشناسه مبدأ: {from_chat_id}"
        )

    source_message_id = forwarded.get(
        "message_id"
    )

    if source_message_id:

        text += (
            f"\nشناسه پیام مبدأ: {source_message_id}"
        )

    return text


# =========================================
# REPLY MESSAGE ID
# =========================================

def get_reply_message_id(new_message):

    reply_id = new_message.get(
        "reply_to_message_id"
    )

    if reply_id:

        return str(reply_id)

    reply_id = new_message.get(
        "reply_to"
    )

    if isinstance(
        reply_id,
        str
    ) and reply_id:

        return reply_id

    if isinstance(
        reply_id,
        dict
    ):

        value = reply_id.get(
            "message_id"
        )

        if value:

            return str(value)

    reply_message = new_message.get(
        "reply_to_message"
    )

    if isinstance(
        reply_message,
        dict
    ):

        value = reply_message.get(
            "message_id"
        )

        if value:

            return str(value)

    return None


# =========================================
# WEBHOOK / RENDER
# =========================================

app = Flask(__name__)


def update_bot_endpoint(endpoint_url):

    if not endpoint_url:

        print("⚠️ WEBHOOK URL not available.")
        return False

    if not TOKEN:

        print("❌ RUBIKA_TOKEN is not set.")
        return False

    try:

        response = requests.post(
            f"{BASE}/updateBotEndpoints",
            json={
                "url": endpoint_url,
                "type": "ReceiveUpdate"
            },
            timeout=30
        )

        result = response.json()

        print("UPDATE ENDPOINT:", result)

        return result.get("status") == "OK"

    except Exception as e:

        print("UPDATE ENDPOINT ERROR:", e)
        return False


def extract_updates(payload):
    """Accept common Rubika webhook shapes and return a list of updates."""

    if not isinstance(payload, dict):
        return []

    data = payload.get("data")

    if isinstance(data, dict):
        updates = data.get("updates")
        if isinstance(updates, list):
            return updates

    updates = payload.get("updates")
    if isinstance(updates, list):
        return updates

    update = payload.get("update")
    if isinstance(update, dict):
        return [update]

    if payload.get("type"):
        return [payload]

    return []


def process_update(update):
    """Process one Rubika NewMessage update using the existing bot logic."""

    global message_number

    if not isinstance(update, dict):
        return

    if update.get("type") != "NewMessage":
        return

    chat_id = str(
        update.get(
            "chat_id"
        )
    )

    new_message = update.get(
        "new_message",
        {}
    )

    text = str(
        new_message.get(
            "text",
            ""
        )
    ).strip()

    file_info = new_message.get(
        "file"
    )

    # =================================
    # ADMIN
    # =================================

    if chat_id == MY_CHAT_ID:

        reply_message_id = get_reply_message_id(
            new_message
        )

        if reply_message_id:

            target_chat_id = reply_map.get(
                str(reply_message_id)
            )

            if not target_chat_id:

                send_message(
                    MY_CHAT_ID,
                    "❌ این پیام قابل پاسخ دادن نیست."
                )

                return

            target_chat_id = str(
                target_chat_id
            )

            # -----------------------------
            # BAN
            # -----------------------------

            if text == "بن":

                if target_chat_id not in banned_users:

                    banned_users.append(
                        target_chat_id
                    )

                    save_json(
                        BANNED_FILE,
                        banned_users
                    )

                send_message(
                    MY_CHAT_ID,
                    "🚫 کاربر با موفقیت بن شد."
                )

                return

            # -----------------------------
            # UNBAN
            # -----------------------------

            if text in (
                "انبن",
                "آنبن"
            ):

                if target_chat_id in banned_users:

                    banned_users.remove(
                        target_chat_id
                    )

                    save_json(
                        BANNED_FILE,
                        banned_users
                    )

                send_message(
                    MY_CHAT_ID,
                    "✅ کاربر با موفقیت آزاد شد."
                )

                return

            # -----------------------------
            # TEXT REPLY
            # -----------------------------

            if text:

                answer_id = send_message(
                    target_chat_id,
                    text
                )

                if answer_id:

                    send_message(
                        MY_CHAT_ID,
                        "✅ جواب با موفقیت ارسال شد."
                    )

                else:

                    send_message(
                        MY_CHAT_ID,
                        "❌ ارسال جواب ناموفق بود."
                    )

                return

            # -----------------------------
            # IMAGE REPLY
            # -----------------------------

            if file_info and is_image(
                file_info
            ):

                source_file_id = file_info.get(
                    "file_id"
                )

                source_file_name = file_info.get(
                    "file_name",
                    "image.jpg"
                )

                if source_file_id:

                    answer_id = transfer_image(
                        source_file_id,
                        source_file_name,
                        target_chat_id
                    )

                    if answer_id:

                        send_message(
                            MY_CHAT_ID,
                            "✅ عکس ارسال شد."
                        )

                    else:

                        send_message(
                            MY_CHAT_ID,
                            "❌ ارسال عکس ناموفق بود."
                        )

                return

        return

    # =================================
    # BANNED USER
    # =================================

    if chat_id in banned_users:

        print(
            "🚫 BANNED USER:",
            chat_id
        )

        return

    # =================================
    # START
    # =================================

    if text == "/start":

        send_message(
            chat_id,
            "👋 سلام!\n\n"
            "به چت ناشناس خوش اومدی 🌚\n\n"
            "پیامت رو بفرست؛ "
            "من اون رو به صورت ناشناس برای مدیر میفرستم."
        )

        return

    # =================================
    # HELP
    # =================================

    if text == "/help":

        send_message(
            chat_id,
            "📖 راهنمای بات\n\n"
            "پیامت رو بفرست تا به صورت ناشناس "
            "برای مدیر ارسال بشه."
        )

        return

    # =================================
    # OTHER COMMANDS
    # =================================

    if text.startswith("/"):

        return

    # =================================
    # USER IMAGE
    # =================================

    if file_info:

        if not is_image(
            file_info
        ):

            print(
                "⚠️ NON-IMAGE FILE IGNORED:",
                file_info
            )

            return

        source_file_id = file_info.get(
            "file_id"
        )

        source_file_name = file_info.get(
            "file_name",
            "image.jpg"
        )

        if not source_file_id:

            return

        message_number += 1

        messages[
            str(message_number)
        ] = chat_id

        save_json(
            MESSAGES_FILE,
            messages
        )

        admin_caption = (
            f"🖼️ عکس ناشناس #{message_number}\n\n"
            f"نام فایل: {source_file_name}\n"
            f"حجم: {file_info.get('size', 'نامشخص')} بایت"
        )

        admin_caption += get_forward_notice(
            new_message
        )

        admin_message_id = transfer_image(
            source_file_id,
            source_file_name,
            MY_CHAT_ID,
            admin_caption
        )

        if admin_message_id:

            reply_map[
                str(admin_message_id)
            ] = chat_id

            save_json(
                REPLY_MAP_FILE,
                reply_map
            )

            send_message(
                chat_id,
                "✅ عکس با موفقیت ارسال شد."
            )

        else:

            send_message(
                chat_id,
                "❌ ارسال عکس ناموفق بود."
            )

        return

    # =================================
    # USER TEXT
    # =================================

    if text:

        message_number += 1

        messages[
            str(message_number)
        ] = chat_id

        save_json(
            MESSAGES_FILE,
            messages
        )

        admin_message = (
            f"📩 پیام ناشناس #{message_number}\n\n"
            f"{text}\n\n"
            f"↩️ برای جواب دادن، همین پیام را Reply کنید."
        )

        admin_message += get_forward_notice(
            new_message
        )

        admin_message_id = send_message(
            MY_CHAT_ID,
            admin_message
        )

        if admin_message_id:

            reply_map[
                str(admin_message_id)
            ] = chat_id

            save_json(
                REPLY_MAP_FILE,
                reply_map
            )

            send_message(
                chat_id,
                "✅ پیام با موفقیت ارسال شد."
            )

        else:

            send_message(
                chat_id,
                "❌ ارسال پیام ناموفق بود."
            )


@app.get("/")
def health():
    return "OK", 200


@app.post("/webhook")
def webhook():
    try:
        payload = request.get_json(silent=True)

        if payload is None:
            return jsonify({"status": "BAD_REQUEST"}), 400

        updates = extract_updates(payload)

        print(f"WEBHOOK: received {len(updates)} update(s)")

        for update in updates:
            try:
                process_update(update)
            except Exception as e:
                print("UPDATE PROCESS ERROR:", e)

        return jsonify({"status": "OK"}), 200

    except Exception as e:
        print("WEBHOOK ERROR:", e)
        return jsonify({"status": "ERROR"}), 500


def configure_webhook():
    render_url = os.environ.get("RENDER_EXTERNAL_URL", "").strip().rstrip("/")

    if not render_url:
        print("⚠️ RENDER_EXTERNAL_URL is not set; webhook was not registered automatically.")
        return

    endpoint_url = f"{render_url}/webhook"

    print("🔗 Registering webhook:", endpoint_url)
    update_bot_endpoint(endpoint_url)


print()
print("================================")
print("🤖 RUBIKA WEBHOOK BOT")
print("================================")

if not TOKEN:
    print("❌ RUBIKA_TOKEN environment variable is missing.")
else:
    configure_webhook()


if __name__ == "__main__":
    port = int(os.environ.get("PORT", "10000"))
    app.run(host="0.0.0.0", port=port)
