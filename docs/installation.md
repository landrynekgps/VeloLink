# 📖 Instrukcja instalacji Velolink

## Wymagania

- Home Assistant 2024.1.0 lub nowszy
- Połączenie:
  - **Serial:** Raspberry Pi + Velolink HAT lub USB-RS485 adapter
  - **TCP:** VeloGateway (ESP32/STM32)

---

## Instalacja przez HACS (zalecana)

### 1. Zainstaluj HACS

Jeśli nie masz HACS, zainstaluj go według instrukcji: https://hacs.xyz/docs/setup/download

### 2. Dodaj repozytorium custom

1. Otwórz **HACS** → **Integrations**
2. Kliknij **⋮** (menu) → **Custom repositories**
3. Dodaj URL:https://github.com/landrynekgps/velolink-ha
4. 4. Kategoria: **Integration**
5. Kliknij **Add**

### 3. Zainstaluj integrację

1. W **HACS** → **Integrations** wyszukaj: `Velolink`
2. Kliknij **Download**
3. **Restart Home Assistant**

---

## Instalacja ręczna

### 1. Pobierz pliki

Pobierz najnowszą wersję z: https://github.com/yourname/velolink-ha/releases

### 2. Skopiuj pliki

Rozpakuj i skopiuj folder `custom_components/velolink` do:

### 3. Restart

Restart Home Assistant

---

## Konfiguracja

### Połączenie szeregowe (RPi HAT / USB)

1. **Settings** → **Devices & Services** → **Add Integration**
2. Szukaj: `Velolink`
3. Wybierz: **Serial (RPi HAT / USB)**
4. Konfiguruj:
   - **Port #1:** `/dev/ttyAMA0` (RPi HAT) lub `/dev/ttyUSB0` (USB)
   - **Port #2:** opcjonalnie
   - **Baudrate:** `115200`
   - **RTS toggle:** OFF (włącz tylko jeśli transceiver wymaga)
   - **Scan on startup:** ON
5. Kliknij **Submit**

### Połączenie TCP (VeloGateway)

1. **Settings** → **Devices & Services** → **Add Integration**
2. Szukaj: `Velolink`
3. Wybierz: **TCP (VeloGateway)**
4. Konfiguruj:
   - **Host:** IP VeloGateway (np. `192.168.1.50`)
   - **Port:** `5485`
   - **Scan on startup:** ON
5. Kliknij **Submit**

---

## Discovery

Po konfiguracji uruchom discovery:

1. **Settings** → **Devices & Services** → **Velolink**
2. Kliknij przycisk: **Skanuj wszystkie magistrale**
3. Poczekaj 5-10 sekund
4. Urządzenia pojawią się w zakładce **Devices**

---

## Rozwiązywanie problemów

### Brak portu /dev/ttyAMA0

Na Raspberry Pi włącz UART:

```bash
sudo raspi-config
# Interface Options → Serial Port
# Login shell: NO
# Serial hardware: YES
# Reboot


---

### `docs/configuration.md`

```markdown
# ⚙️ Konfiguracja Velolink

## Device Class i polaryzacja

### Przez UI (zalecane)

1. **Settings** → **Devices & Services** → **Velolink** → **Configure**
2. Wybierz: **Edit channel**
3. Wybierz kanał z listy
4. Ustaw:
   - **Device class:** door, window, motion, itp.
   - **Polarity:** NO (normalnie otwarty) lub NC (normalnie zamknięty)
5. Kliknij **Submit**

### Przez serwis

```yaml
service: velolink.set_channel_config
data:
  bus_id: "bus1"
  address: 5
  channel: 0
  device_class: "door"
  polarity: "NC"
