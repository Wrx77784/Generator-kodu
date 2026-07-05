# Generator-kodu

Prosty projekt pokazujący, jak zbudować podstawowy mechanizm komunikacji sender/receiver przy użyciu Pythona oraz wygenerowany protokół binarny i automatyczny dashboard dla World Cup 2026.

## Co zawiera projekt

- `client.py` – wysyła wiadomość do serwera przez TCP
- `server.py` – odbiera wiadomości od klientów i wypisuje je na ekran
- `generator.py` – generuje handler binarnej serializacji na podstawie `interface.json`
- `template.py.jinja2` – szablon używany przez generator
- `interface.json` – konfiguracja hosta, portu i schematu wiadomości
- `generated_message_handler.py` – wygenerowany handler do serializacji/deserializacji binarnej
- `data_source.py` – opcjonalny moduł pobierający dane wynikowe lub dający fallbackowe delty ratingowe
- `model.py` – modele szans turniejowych dla 2026 World Cup
- `gui.py` – automatyczny dashboard z wykresem top 5 zespołów i ukrytym auto-send
- `tests/test_serialization.py` – test sprawdzający poprawność serializacji/deserializacji

## Uruchomienie

### 1. Uruchom serwer

```powershell
python server.py
```

### 2. Wyslij wiadomość od klienta

```powershell
python client.py "hello from client"
```

### 3. Uruchom GUI World Cup 2026

```powershell
python gui.py
```

GUI automatycznie pobiera dane (jeśli jest dostępny internet) i wysyła estymację szans Argentyny na zwycięstwo w turnieju 2026 do serwera.

> Uwaga: aby GUI mogło pobrać dane z internetu, zainstaluj pakiet `requests`:
>
> ```powershell
> python -m pip install requests
> ```

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
