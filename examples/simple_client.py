#!/usr/bin/env python3
"""
Simple client example for Nocksup.

This script connects to WhatsApp and echoes messages received.
"""
import os
import sys
import time
import logging
from getpass import getpass

# Asigură-te că nocksup poate fi importat
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from nocksup import NocksupClient
from nocksup.exceptions import ConnectionError, AuthenticationError

# Configurează logarea
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s [%(levelname)s] %(message)s')
logger = logging.getLogger(__name__)

def on_message(message):
    """Funcție apelată când se primește un mesaj."""
    print("\n" + "="*50)
    print(f"Mesaj primit: {message}")
    
    # Afișează componente specifice ale mesajului
    sender = message.get('from', 'Necunoscut')
    message_type = message.get('type', 'text')
    
    print(f"De la: {sender}")
    print(f"Tip: {message_type}")
    
    if message_type == 'text':
        text = message.get('text', '')
        print(f"Text: {text}")
        
        # Răspunde la mesaje text cu un ecou
        if text and client:
            client.send_text_message(sender, f"Echo: {text}")
            print(f"Am trimis ecou către {sender}")
            
    elif message_type == 'image':
        caption = message.get('caption', '(fără descriere)')
        print(f"Imagine primită cu descrierea: {caption}")
        
    elif message_type == 'document':
        filename = message.get('filename', 'document.bin')
        caption = message.get('caption', '(fără descriere)')
        print(f"Document primit: {filename}")
        print(f"Descriere: {caption}")
        
    print("="*50)

def on_qr_code(qr_data):
    """Funcție apelată când se generează un cod QR."""
    print("\nScanează acest cod QR cu telefonul tău:")
    print(qr_data)
    print("\nAșteptăm scanarea...")

def on_pairing_code(code):
    """Funcție apelată când se generează un cod de asociere."""
    print(f"\nCod de asociere: {code}")
    print("Introdu acest cod în aplicația WhatsApp de pe telefon:")
    print("1. Deschide WhatsApp pe telefon")
    print("2. Mergi la Setări > Dispozitive conectate > Conectează un dispozitiv")
    print("3. Când ți se cere, introdu codul de asociere")
    print("\nAșteptăm asocierea...")

def on_error(error):
    """Funcție apelată când apare o eroare."""
    print(f"\nEroare: {error}")

def main():
    """Funcția principală a scriptului."""
    global client
    
    # Solicită numărul de telefon
    phone_number = input("Introdu numărul de telefon (cu prefixul țării, ex: 40712345678): ")
    
    # Crează clientul
    client = NocksupClient(
        phone_number=phone_number,
        session_path='./session'
    )
    
    # Înregistrează callback-urile
    client.on_message(on_message)
    client.on_qr_code(on_qr_code)
    client.on_pairing_code(on_pairing_code)
    client.on_error(on_error)
    
    # Solicită metoda de autentificare
    print("\nAlege metoda de autentificare:")
    print("1. Cod QR (scanează cu telefonul)")
    print("2. Cod de asociere (introdu codul în aplicația WhatsApp)")
    print("3. Solicită un cod de verificare prin SMS sau apel vocal")
    
    auth_choice = input("Introdu opțiunea (1-3): ")
    
    try:
        if auth_choice == '1':
            # Conectare cu cod QR
            print("\nÎncercăm conectarea cu cod QR...")
            client.connect(auth_method='qr')
            
        elif auth_choice == '2':
            # Conectare cu cod de asociere
            print("\nGenerăm un cod de asociere...")
            client.connect(auth_method='pairing_code')
            
        elif auth_choice == '3':
            # Solicită un cod de verificare
            print("\nSolicităm un cod de verificare...")
            
            # Solicită metoda de verificare
            print("Alege metoda de verificare:")
            print("1. SMS")
            print("2. Apel vocal")
            
            verify_choice = input("Introdu opțiunea (1-2): ")
            
            if verify_choice == '1':
                verify_method = 'sms'
            else:
                verify_method = 'voice'
            
            # Solicită limba și codul țării (opțional)
            language = input("Introdu codul limbii (implicit en): ") or 'en'
            country_code = input("Introdu codul țării (opțional, ex: RO): ")
            
            # Solicită codul
            result = client.request_code(
                method=verify_method,
                language=language,
                country_code=country_code
            )
            
            print(f"Rezultat solicitare cod: {result}")
            print("Verifică telefonul pentru codul de verificare.")
            
            # Solicită codul de verificare
            verification_code = input("Introdu codul de verificare primit: ")
            
            # Verifică codul
            result = client.verify_code(verification_code)
            print(f"Rezultat verificare cod: {result}")
            
            # Acum că am verificat codul, conectează-te
            print("\nÎncercăm conectarea...")
            client.connect()
            
        else:
            print("Opțiune invalidă. Te rog să alegi 1, 2 sau 3.")
            return 1
        
        # Dacă am ajuns aici, suntem conectați
        print("\nConectat la WhatsApp!")
        print("Client simplu Nocksup rulează acum")
        print("Acesta va afișa mesajele primite și va răspunde cu un ecou")
        print("Apasă Ctrl+C pentru a ieși")
        
        # Menținem clientul în execuție
        try:
            while client.is_connected():
                time.sleep(1)
        except KeyboardInterrupt:
            pass
        
        # Deconectare
        client.disconnect()
        print("\nDeconectat de la WhatsApp")
        
        return 0
        
    except ConnectionError as e:
        print(f"Eroare de conexiune: {e}")
        return 1
    except AuthenticationError as e:
        print(f"Eroare de autentificare: {e}")
        return 1
    except Exception as e:
        print(f"Eroare neașteptată: {e}")
        return 1


if __name__ == '__main__':
    # Variabilă globală pentru client
    client = None
    
    # Rulează funcția principală
    sys.exit(main())