# Nocksup - Bibliotecă Python pentru WhatsApp

Nocksup este o bibliotecă Python modernă pentru comunicarea cu WhatsApp, dezvoltată ca înlocuitor pentru Yowsup.

## Caracteristici

- Compatibilă cu protocoalele WhatsApp actuale (actualizare 2025)
- Suport pentru autentificare prin cod QR sau cod de asociere
- Trimitere și primire de mesaje text
- Gestionare conexiuni WebSocket robustă
- Suport pentru dispozitive multiple și sesiuni persistente
- Compatibilă cu Termux pe dispozitive Android

## Instalare

```bash
pip install nocksup
```

Sau instalează din sursă:

```bash
git clone https://github.com/gyovannyvpn123/Nocksup.git
cd Nocksup
pip install -e .
```

## Utilizare de bază

### Conectare cu cod QR

```python
from nocksup.client.client import NocksupClient

# Creează un client cu numărul tău de telefon
client = NocksupClient(phone_number="4071234567")

# Callback pentru mesaje primite
def on_message(message):
    print(f"Mesaj primit de la {message.get('sender')}: {message.get('text')}")

# Callback pentru cod QR
def on_qr_code(qr_data):
    print("Scanează acest cod QR cu WhatsApp pe telefonul tău")
    # În aplicații reale, aici ai putea afișa codul QR

# Înregistrează callback-urile
client.on_message(on_message)
client.on_qr_code(on_qr_code)

# Conectare folosind QR code
client.connect(auth_method='qr')

if client.is_connected():
    # Trimite un mesaj
    client.send_text_message("4071234567", "Salut de la Nocksup!")
    
    # Menține aplicația rulând pentru a primi mesaje
    try:
        while client.is_connected():
            pass
    except KeyboardInterrupt:
        client.disconnect()
```

### Conectare cu cod de asociere

```python
from nocksup.client.client import NocksupClient

# Creează un client cu numărul tău de telefon
client = NocksupClient(phone_number="4071234567")

# Callback pentru cod de asociere
def on_pairing_code(code):
    print(f"Introdu acest cod în WhatsApp: {code}")

# Înregistrează callback-ul
client.on_pairing_code(on_pairing_code)

# Generează codul de asociere
pairing_code = client.generate_pairing_code()

# Conectare folosind codul de asociere
client.connect(auth_method='pairing_code')

if client.is_connected():
    print("Conectat cu succes!")
    # Cod pentru trimitere mesaje...
    
    client.disconnect()
```

## Rezolvarea problemelor

### Probleme comune

1. **Erori de conexiune**: Asigură-te că ai o conexiune stabilă la internet. Biblioteca va încerca automat reconectarea.

2. **Eroare de autentificare**: Scanează codul QR sau introdu codul de asociere în aplicația WhatsApp de pe telefonul tău.

3. **Eroare bad_baram**: Această eroare care apare în alte biblioteci a fost rezolvată în Nocksup prin actualizarea protocoalelor de comunicare.

4. **Erori cu caractere Unicode**: Nocksup folosește decodare UTF-8 robustă pentru a gestiona mesajele în orice limbă.

### Depanare

Pentru a activa logurile de depanare:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## Limitări actuale

- Suport încă în dezvoltare pentru apeluri audio/video
- Suportul pentru mesaje de grup este în versiune beta
- Trimiterea de mesaje media este încă în dezvoltare

## Note legale

Această bibliotecă nu este afiliată sau aprobată oficial de WhatsApp. Utilizarea acesteia trebuie să respecte termenii și condițiile WhatsApp.