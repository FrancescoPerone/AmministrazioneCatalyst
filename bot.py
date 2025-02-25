import os
import cv2
import pytesseract
import logging
from googleapiclient.discovery import build
from google.oauth2 import service_account
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters
import asyncio

# Configura il logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

# Carica il file JSON delle credenziali di Google Sheets
GOOGLE_SHEETS_CREDENTIALS_FILE = "/etc/secrets/credentials.json"
SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]
SERVICE_ACCOUNT_FILE = GOOGLE_SHEETS_CREDENTIALS_FILE

creds = service_account.Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=SCOPES)
service = build("sheets", "v4", credentials=creds)

# ID del Google Sheet
SPREADSHEET_ID = "1w0WQu0HUvFNNYnsve1tD9fPMWYlOpo2kaw3YGHz2L-s"
SHEET_NAME = "Foglio1"

# Configura il bot Telegram
TELEGRAM_TOKEN = "7864421966:AAFv7OMH40FE2IDRKvegC_qRdOaD99aXrHg"

def ocr_image(image_path):
    """ Estrae testo da un'immagine usando Tesseract """
    img = cv2.imread(image_path)
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    text = pytesseract.image_to_string(gray)
    return text.strip()

def update_google_sheet(text):
    """ Scrive il testo estratto in una nuova riga del Google Sheet """
    sheet = service.spreadsheets()
    values = [[text]]  # Testo in una nuova riga
    body = {"values": values}
    sheet.values().append(
        spreadsheetId=SPREADSHEET_ID,
        range=f"{SHEET_NAME}!A:A",
        valueInputOption="RAW",
        body=body
    ).execute()

async def start(update: Update, context):
    """ Comando /start per il bot """
    await update.message.reply_text("Ciao! Inviami un'immagine e estrarrò il testo per te.")

async def handle_photo(update: Update, context):
    """ Gestisce le immagini ricevute """
    if update.message.photo:
        photo_file = await update.message.photo[-1].get_file()
        file_path = "image.jpg"
        await photo_file.download(file_path)
        await update.message.reply_text("Immagine ricevuta! Estraendo il testo...")
        
        text = ocr_image(file_path)
        if text:
            update_google_sheet(text)
            await update.message.reply_text(f"Testo estratto e salvato:\n{text}")
        else:
            await update.message.reply_text("Non sono riuscito a estrarre il testo. Assicurati che sia leggibile!")
        os.remove(file_path)
    else:
        await update.message.reply_text("Non ho ricevuto nessuna immagine. Per favore invia una foto.")

async def main():
    """ Avvia il bot """
    application = Application.builder().token(TELEGRAM_TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    
    print("Bot avviato...")
    await application.initialize()
    await application.start()
    try:
        await application.run_polling()
    except RuntimeError:
        pass

if __name__ == "__main__":
    import asyncio
    try:
        asyncio.run(main())
    except RuntimeError:
        loop = asyncio.get_event_loop()
        loop.run_until_complete(main())
