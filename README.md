# Nocksup - Biblioteca WhatsApp pentru Python

Nocksup este o bibliotecă Python modernă pentru comunicarea cu WhatsApp, compatibilă cu protocoalele actuale WhatsApp. Această bibliotecă a fost dezvoltată pentru a rezolva problemele întâlnite cu alte biblioteci precum Yowsup, care nu mai sunt compatibile cu versiunile actuale ale WhatsApp.

## Caracteristici

- Compatibilitate cu protocoalele actuale WhatsApp
- Suport pentru autentificare multi-device
- Autentificare prin QR code sau pairing code
- Trimitere și primire de mesaje text și media
- Gestionare contacte și grupuri
- Arhitectură modulară, extensibilă

## Instalare

```bash
pip install cryptography requests websocket-client protobuf
git clone https://github.com/gyovannyvpn123/Nocksup.git
cd Nocksup
```

## Utilizare rapidă

```python
from nocksup import NocksupClient

# Creare client
client = NocksupClient()

# Setare număr de telefon
client.set_phone_number("401234567890")

# Conectare cu pairing code (recomandat pentru Termux și CLI)
print("Deschide WhatsApp pe telefon:")
print("Setări > Dispozitive conectate > Conectează un dispozitiv > Nu poți scana codul QR?")
pairing_code = input("Introdu codul de asociere din 8 cifre: ")
client.connect(restore_session=False, auth_method="pairing_code", pairing_code=pairing_code)

# Sau conectare cu QR code (recomandat pentru desktop)
# client.connect(restore_session=False, auth_method="qr")
# print("Scanează codul QR din aplicația WhatsApp")

# Trimitere mesaj text
client.send_text_message("401234567890", "Salut de la Nocksup!")

# Deconectare
client.disconnect()
```

## Exemplu complet

Vezi fișierul `examples/simple_client.py` pentru un exemplu complet.

## Compatibilitate

Biblioteca a fost testată cu versiunile curente ale WhatsApp (2023-2024) și include actualizări de protocol pentru a preveni erori precum "bad_baram".

## Utilizare pe Termux

Biblioteca funcționează perfect pe Termux (Android):

```bash
pkg update && pkg upgrade
pkg install python
pip install cryptography requests websocket-client protobuf
git clone https://github.com/gyovannyvpn123/Nocksup.git
cd Nocksup
python examples/simple_client.py
```

## Licență

MIT License