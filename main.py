from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
import requests
import base64
from Crypto.Cipher import AES
from Crypto.Util.Padding import unpad

# AES decryption setup
key = "638udh3829162018".encode("utf-8")  # Your key
iv = "fedcba9876543210".encode("utf-8")   # Your IV

# AES decryption function
def decrypt_aes(encrypted_text, key, iv):
    try:
        encrypted_data = base64.b64decode(encrypted_text.split(':')[0])
        cipher = AES.new(key, AES.MODE_CBC, iv)
        decrypted_data = unpad(cipher.decrypt(encrypted_data), AES.block_size)
        return decrypted_data.decode("utf-8")
    except Exception as e:
        print(f"Error during decryption: {e}")
        return None

# API credentials and headers
headers = {
    "Client-Service": "Appx",
    "Auth-Key": "appxapi",
    "source": "windows",
    "User-ID": "86683",
    "Authorization": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJpZCI6Ijg2NjgzIiwiZW1haWwiOiJzZW5wcmFubm95QGdtYWlsLmNvbSIsInRpbWVzdGFtcCI6MTcyOTY2NjI0NH0.wJVUyMfA1dMPyZolsPNyWBje8fgZ1HeNkgKDSGSC4j8"
}

# Function to fetch video data using item_id
def fetch_video_data(item_id):
    url_video_data = f"https://voraclassesapi.classx.co.in/get/get_mpd_drm_links?videoid={item_id}&folder_wise_course=1"
    try:
        response_video = requests.get(url_video_data, headers=headers)
        if response_video.status_code == 200:
            return response_video.json()
        else:
            return None
    except Exception as e:
        print(f"Error fetching video data for ID {item_id}: {e}")
        return None

# Process video contents and return links
def process_video_folder_contents(course_id, parent_id):
    params_video = {"course_id": course_id, "parent_id": parent_id, "windowsapp": "true"}
    url_folder_contents = "https://voraclassesapi.classx.co.in/get/folder_contentsv2"
    response = requests.get(url_folder_contents, headers=headers, params=params_video)
    if response.status_code == 200:
        data = response.json().get("data", [])
        result = []
        for item in data:
            item_id = item.get("id", "No ID")
            title = item.get("Title", "No Title")
            video_data = fetch_video_data(item_id)
            if video_data and isinstance(video_data, dict) and "data" in video_data:
                for video_item in video_data["data"]:
                    if "path" in video_item and "480p" in video_item.get("quality", "").lower():
                        encrypted_path = video_item["path"]
                        decrypted_path = decrypt_aes(encrypted_path, key, iv)
                        if decrypted_path:
                            result.append(f"{title}:{decrypted_path}")
                        else:
                            result.append(f"Failed to decrypt path for video ID {item_id}")
        return "\n".join(result) if result else "No video links found."
    else:
        return f"Failed to retrieve folder contents. Status code: {response.status_code}"

# Process PDF contents and return links
def process_pdf_folder_contents(course_id, parent_id):
    params_pdf = {"course_id": course_id, "parent_id": parent_id, "windowsapp": "true"}
    url_folder_contents = "https://voraclassesapi.classx.co.in/get/folder_contentsv2"
    response = requests.get(url_folder_contents, headers=headers, params=params_pdf)
    if response.status_code == 200:
        data = response.json().get("data", [])
        result = []
        for item in data:
            title = item.get("Title", "No Title")
            download_link = item.get("download_link", "")
            decrypted_link = decrypt_aes(download_link, key, iv)
            if decrypted_link:
                result.append(f"{title}:{decrypted_link}")
            else:
                result.append(f"Failed to decrypt download link for PDF {title}")
        return "\n".join(result) if result else "No PDF links found."
    else:
        return f"Failed to retrieve folder contents. Status code: {response.status_code}"

# /video command handler
async def video_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        course_id, parent_id = context.args[0].split(":")
        result = process_video_folder_contents(course_id, parent_id)
        await update.message.reply_text(result)
    except Exception as e:
        await update.message.reply_text(f"Error: {e}")

# /pdf command handler
async def pdf_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        course_id, parent_id = context.args[0].split(":")
        result = process_pdf_folder_contents(course_id, parent_id)
        await update.message.reply_text(result)
    except Exception as e:
        await update.message.reply_text(f"Error: {e}")

# Main function to start the bot
if __name__ == "__main__":
    application = Application.builder().token("7505197787:AAES1wqwfXym-vmKuc9n3c56SOUNQF2Nixk").build()

    # Command handlers
    application.add_handler(CommandHandler("video", video_handler))
    application.add_handler(CommandHandler("pdf", pdf_handler))

    # Start the bot and run until shutdown
    application.run_polling()  # Start polling for updates
