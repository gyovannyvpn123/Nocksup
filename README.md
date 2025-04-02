# Nocksup - Python Library for WhatsApp

Nocksup este o bibliotecă modernă Python pentru comunicarea WhatsApp, dezvoltată ca înlocuitor pentru Yowsup, menținând compatibilitatea cu protocoalele actuale WhatsApp.

## Caracteristici

- Compatibilă cu protocoalele WhatsApp actuale (actualizare 2025)
- Suport pentru mai multe metode de autentificare:
  - Cod QR (scanare cu telefonul)
  - Cod de asociere (introdus manual în aplicația WhatsApp)
  - Înregistrare prin SMS/apel vocal
- Trimitere și primire de mesaje text
- Gestionare robustă a conexiunilor WebSocket
- Suport pentru dispozitive multiple și sesiuni persistente
- Compatibilitate cu Termux pe dispozitive Android
- Funcționalități avansate pentru gestionarea grupurilor
- Trimitere și primire de media (imagini, documente, locație)
- CLI similar cu yowsup-cli pentru acces rapid la funcționalități

## Instalare

```bash
pip install nocksup
```

Sau instalare din sursă:

```bash
git clone https://github.com/gyovannyvpn123/Nocksup.git
cd Nocksup
pip install -e .
```

## Utilizare de bază

### Utilizare prin CLI (nocksup-cli)

Nocksup include o interfață în linia de comandă (CLI) similară cu yowsup-cli pentru acces rapid la funcționalitățile bibliotecii.

#### Autentificare și trimitere de mesaje

```bash
# Rulează clientul WhatsApp cu autentificare prin cod QR
nocksup-cli run -p 40712345678 -a qr

# Rulează clientul WhatsApp cu autentificare prin cod de asociere
nocksup-cli run -p 40712345678 -a pairing_code

# Rulează client de ecou (răspunde automat la mesaje)
nocksup-cli demos echo -p 40712345678
```

#### Înregistrare cu număr de telefon (SMS/apel vocal)

```bash
# Solicită un cod de verificare prin SMS
nocksup-cli registration request -p 40712345678 -m sms

# Solicită un cod de verificare prin apel vocal
nocksup-cli registration request -p 40712345678 -m voice

# Verifică codul primit
nocksup-cli registration verify -p 40712345678 -c 123456
```

### Utilizare din Python

#### Conectare cu cod QR

```python
from nocksup import NocksupClient

# Crează un client cu numărul tău de telefon
client = NocksupClient(phone_number="40712345678")

# Callback pentru mesajele primite
def on_message(message):
    print(f"Mesaj primit de la {message.get('from')}: {message.get('text')}")

# Callback pentru codul QR
def on_qr_code(qr_data):
    print("Scanează acest cod QR cu WhatsApp de pe telefonul tău")
    print(qr_data)

# Înregistrează callback-urile
client.on_message(on_message)
client.on_qr_code(on_qr_code)

# Conectează-te folosind codul QR
client.connect(auth_method='qr')

if client.is_connected():
    # Trimite un mesaj
    client.send_text_message("40723456789", "Salut de la Nocksup!")
    
    # Menține aplicația în execuție pentru a primi mesaje
    try:
        import time
        while client.is_connected():
            time.sleep(1)
    except KeyboardInterrupt:
        client.disconnect()
```

#### Conectare cu cod de asociere

```python
from nocksup import NocksupClient

# Crează un client cu numărul tău de telefon
client = NocksupClient(phone_number="40712345678")

# Callback pentru codul de asociere
def on_pairing_code(code):
    print(f"Introdu acest cod în WhatsApp: {code}")
    print("1. Deschide WhatsApp pe telefon")
    print("2. Mergi la Setări > Dispozitive conectate > Conectează un dispozitiv")
    print("3. Când ți se cere, introdu codul de asociere")

# Înregistrează callback-ul
client.on_pairing_code(on_pairing_code)

# Conectează-te folosind codul de asociere
client.connect(auth_method='pairing_code')

if client.is_connected():
    print("Conectat cu succes!")
    # Cod pentru trimiterea de mesaje...
    
    client.disconnect()
```

#### Înregistrare și verificare de cod

```python
from nocksup import NocksupClient

# Crează un client cu numărul tău de telefon
client = NocksupClient(phone_number="40712345678")

# Solicită un cod de verificare prin SMS
result = client.request_code(method='sms', language='ro')
print(f"Rezultat solicitare cod: {result}")
print("Verifică telefonul pentru codul de verificare.")

# Verifică codul primit (introdus de utilizator)
verification_code = input("Introdu codul de verificare primit: ")
result = client.verify_code(verification_code)
print(f"Rezultat verificare cod: {result}")

# Acum te poți conecta la WhatsApp
client.connect()
```

## Funcționalități avansate

### Trimitere de media

```python
# Trimite o imagine
client.send_image("40712345678", "path/to/image.jpg", "Descriere opțională")

# Trimite un document
client.send_document("40712345678", "path/to/document.pdf", "Descriere opțională")

# Trimite locație
client.send_location("40712345678", 44.4268, 26.1025, "București", "Piața Unirii")

# Trimite audio
client.send_audio("40712345678", "path/to/audio.mp3")

# Trimite video
client.send_video("40712345678", "path/to/video.mp4", "Descriere opțională")
```

### Gestionare grupuri

```python
# Crează un grup nou
group_id = client.create_group("Numele grupului", ["40712345678", "40723456789"])

# Adaugă participanți la grup
client.add_participants(group_id, ["40734567890"])

# Elimină participanți din grup
client.remove_participants(group_id, ["40723456789"])

# Actualizează subiectul grupului
client.update_group_subject(group_id, "Noul nume al grupului")
```

### Gestionare contacte

```python
# Verifică dacă un număr există pe WhatsApp
if client.check_phone_exists("40712345678"):
    print("Numărul există pe WhatsApp")

# Obține informații despre un contact
contact_info = client.get_contact("40712345678")
print(f"Informații contact: {contact_info}")

# Obține toate contactele
all_contacts = client.get_contacts()
```

## Depanare

### Probleme comune

1. **Erori de conexiune**: Asigură-te că ai o conexiune stabilă la internet. Biblioteca va încerca automat să se reconecteze.

2. **Eroare de autentificare**: Scanează codul QR sau introdu codul de asociere în aplicația WhatsApp de pe telefonul tău.

3. **Eroarea bad_baram**: Această eroare care apare în alte biblioteci a fost rezolvată în Nocksup prin actualizarea protocoalelor de comunicare.

4. **Erori de caractere Unicode**: Nocksup folosește decodarea robustă UTF-8 pentru a gestiona mesaje în orice limbă.

### Depanare

Pentru a activa logurile de depanare:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## Limitări actuale

- Suportul pentru apeluri audio/video este încă în dezvoltare
- Suportul pentru mesaje de grup este în beta
- Trimiterea de media este încă în optimizare pentru toate tipurile de fișiere

## CLI (nocksup-cli)

Scriptul `nocksup-cli` oferă o interfață completă în linia de comandă:

```
nocksup-cli registration request -p <phone> -m <sms|voice>  # Solicită cod prin SMS/voce
nocksup-cli registration verify -p <phone> -c <code>        # Verifică codul primit
nocksup-cli run -p <phone> -a <qr|pairing_code>            # Rulează clientul interactiv
nocksup-cli demos echo -p <phone>                          # Rulează un client de ecou
```

## Instalare în Termux

Nocksup funcționează excelent pe dispozitive Android prin Termux:

```bash
pkg update && pkg upgrade
pkg install python
pip install nocksup

# Sau instalare din sursă
git clone https://github.com/gyovannyvpn123/Nocksup.git
cd Nocksup
pip install -e .
```

## Note legale

Această bibliotecă nu este afiliată sau aprobată oficial de WhatsApp. Utilizarea sa trebuie să respecte termenii și condițiile WhatsApp.