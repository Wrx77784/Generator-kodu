# Generator-kodu

Prosty projekt pokazujący, jak zbudować podstawowy mechanizm komunikacji sender/receiver przy użyciu Pythona.

## Co zawiera projekt

- `client.py` – wysyła wiadomość do serwera przez TCP
- `server.py` – odbiera wiadomości od klientów i wypisuje je na ekran
- `generator.py` – generuje prosty plik z szablonu Jinja2
- `template.py.jinja2` – szablon używany przez generator
- `interface.json` – konfiguracja hosta, portu i domyślnych nazw

## Uruchomienie

### 1. Uruchom serwer

```powershell
python server.py
```

### 2. Wyslij wiadomość od klienta

```powershell
python client.py "hello from client"
```

Możesz też podać własnego nadawcę i odbiorcę:

```powershell
python client.py "hello" --sender client1 --receiver receiver1
```

## Przykład działania

Serwer uruchomi się na domyślnym porcie `5001`.
Klient połączy się z `127.0.0.1:5001` i wyśle wiadomość.

## Uwagi

- Projekt jest prostym przykładem komunikacji sieciowej.
- Serwer obsługuje wiele połączeń jednocześnie.
- Plik `messages.jsonl` jest używany przez wcześniejszą wersję komunikacji plikowej, ale obecnie projekt działa przez TCP.
