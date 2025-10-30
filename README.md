# 🔌 Velolink RS485 – Profesjonalna automatyka domowa

[![HACS](https://img.shields.io/badge/HACS-Custom-orange.svg?style=for-the-badge)](https://github.com/hacs/integration)
[![GitHub release](https://img.shields.io/github/release/landrynekgps/VeloLink.svg?style=for-the-badge)](https://github.com/landrynekgps/VeloLink/releases)
[![GitHub stars](https://img.shields.io/github/stars/landrynekgps/VeloLink.svg?style=for-the-badge)](https://github.com/landrynekgps/VeloLink/stargazers)
[![Maintenance](https://img.shields.io/badge/Maintained%3F-yes-green.svg?style=for-the-badge)](https://github.com/landrynekgps/VeloLink/graphs/commit-activity)

![Velolink Logo](https://raw.githubusercontent.com/landrynekgps/VeloLink/main/icon.png)

**Velolink** to system automatyki domowej wykorzystujący **magistralę RS485** do szybkiej i niezawodnej komunikacji z modułami wejść/wyjść, przełącznikami ściennymi, ściemniaczami i czujnikami.

---

## ✨ Dlaczego Velolink?

| Funkcja | Korzyść |
|---------|---------|
| ⚡ **Ultra-niskie opóźnienie** | Reakcja <20ms – idealne dla przycisków i czujników |
| 🔌 **Przewodowa komunikacja** | Niezawodność RS485, brak zaników WiFi |
| 🏢 **Duże instalacje** | Do 254 urządzeń na magistralę |
| 🏠 **100% lokalnie** | Bez chmury, bez subskrypcji, pełna prywatność |
| 🎛️ **Auto-discovery** | Urządzenia pojawiają się automatycznie |
| 🌐 **Gateway WiFi/Ethernet** | Opcjonalny VeloGateway zamiast kabla do RPi |

---

## 📸 Screenshoty

<details>
<summary>👉 Kliknij aby zobaczyć zrzuty ekranu</summary>

### Główny panel
![Dashboard](https://raw.githubusercontent.com/landrynekgps/VeloLink/main/docs/images/dashboard.png)

### Konfiguracja przez UI
![Config Flow](https://raw.githubusercontent.com/landrynekgps/VeloLink/main/docs/images/config-flow.png)

### Wykryte urządzenia
![Devices](https://raw.githubusercontent.com/landrynekgps/VeloLink/main/docs/images/devices.png)

### Edycja Device Class
![Device Class](https://raw.githubusercontent.com/landrynekgps/VeloLink/main/docs/images/device-class-config.png)

</details>

---

## 🎛️ Wspierane urządzenia

### 🔧 Moduły w rozdzielnicy (magistrala RS485)

| Moduł | Typ | Kanały | Zastosowanie |
|-------|-----|--------|--------------|
| **IO-16IN** | Wejścia binarne | 16 | Przyciski, czujniki drzwi/okien, PIR |
| **IO-12OUT** | Przekaźniki | 12 | Światła, rolety, bramy, ogrzewanie |
| **IO-4OUT** | Przekaźniki | 4 | Duże moce 16A oraz pomiar prądu |
| **IO-PWM** | PWM 0–255 | 4–8 | Ściemnianie LED, regulatory |
| **IO-ANALOG** | Wejścia 0–10V | 4–8 | Czujniki temp/wilg, natężenie światła |

### 🏠 Urządzenia ścienne (montaż podtynkowy)

| Urządzenie | Opis | Platforma HA |
|------------|------|--------------|
| **VeloSwitch** | Przycisk ścienny (1–4 przyciski) | `binary_sensor` |
| **VeloDimmer** | Ściemniacz z enkoderem i przyciskiem | `light` |
| **VeloMotion** | Czujnik ruchu/obecności | `binary_sensor` |
| **VeloSensor** | Multi-czujnik (temp/wilgotność/lux) | `sensor` |

### 📡 Czujniki bezprzewodowe (ESP-NOW, wymaga VeloGateway)

- Czujnik drzwi/okien
- Czujnik temperatury
- Przycisk bezprzewodowy
- Przekaźnik WiFi

---

## 🚀 Szybki start

### Wymagania

- **Home Assistant** 2024.1.0 lub nowszy
- **HACS** zainstalowany
- Połączenie:
  - **Opcja A:** Raspberry Pi + Velolink HAT (2× RS485)
  - **Opcja B:** VeloGateway (ESP32/STM32 + Ethernet/WiFi)

### Instalacja

1. **Dodaj repozytorium do HACS:**
   - HACS → Integrations → ⋮ → Custom repositories
   - URL: `https://github.com/landrynekgps/VeloLink`
   - Category: **Integration**

2. **Zainstaluj:**
   - Szukaj "Velolink" → Download

3. **Restart Home Assistant**

4. **Dodaj integrację:**
   - Settings → Devices & Services → Add Integration
   - Szukaj "Velolink"
   - Wybierz typ połączenia (Serial / TCP)
   - Podaj parametry (port, baudrate, itp.)

5. **Discovery:**
   - Kliknij przycisk "Skanuj wszystkie magistrale"
   - Urządzenia pojawią się automatycznie! 🎉

---

## 📚 Dokumentacja

- 📖 [Instrukcja instalacji](docs/installation.md)
- ⚙️ [Konfiguracja](docs/configuration.md)
- 🔧 [Rozwiązywanie problemów](docs/troubleshooting.md)
- 📡 [Specyfikacja protokołu](docs/protocol.md)
- 🎓 [Przykłady automatyzacji](examples/automations.yaml)

---

## 🎯 Przykładowa automatyzacja

```yaml
automation:
  - alias: "Dzwonek włącza światło w przedpokoju"
    trigger:
      platform: state
      entity_id: binary_sensor.velolink_in_5_0
      to: "on"
    action:
      - service: light.turn_on
        target:
          entity_id: light.przedpokoj
      - delay:
          seconds: 10
      - service: light.turn_off
        target:
          entity_id: light.przedpokoj
