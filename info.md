# 🔌 Velolink – Profesjonalna automatyka domowa przez RS485

Velolink to system automatyki domowej wykorzystujący magistralę RS485 do komunikacji z modułami wejść/wyjść, przełącznikami ściennymi, ściemniaczami i czujnikami.

## ✨ Funkcje

- ⚡ **Niskie opóźnienie** – reakcja <20ms (idealne dla przycisków)
- 🔌 **Przewodowa komunikacja** – niezawodność RS485, bez WiFi
- 🏠 **Auto-discovery** – automatyczne wykrywanie urządzeń
- 🎛️ **Pełna integracja HA** – przyciski, światła, czujniki, sensory
- 🌐 **Gateway TCP/IP** – możliwość łączenia przez Ethernet/WiFi
- 📡 **ESP-NOW** – bezprzewodowe czujniki (opcjonalnie)

## 🛠️ Wspierane urządzenia

### Moduły I/O (RS485)
- **IO-8IN** – 8 wejść binarnych
- **IO-8OUT** – 8 przekaźników
- **IO-PWM** – Sterownik PWM
- **IO-ANALOG** – Wejścia analogowe

### Urządzenia ścienne (RS485)
- **VeloSwitch** – Przełącznik ścienny (1-4 przyciski)
- **VeloDimmer** – Ściemniacz z enkoderem
- **VeloMotion** – Czujnik ruchu/obecności
- **VeloSensor** – Czujnik temp/wilgotność/lux

### Czujniki ESP-NOW (wymaga VeloGateway)
- Czujnik drzwi/okien
- Czujnik temperatury
- Przycisk bezprzewodowy
- Przekaźnik WiFi

## 📡 Typy połączeń

### Serial (RPi HAT / USB-RS485)
- Raspberry Pi + Velolink HAT
- USB-RS485 adapter
- Bezpośrednie podłączenie do magistrali

### TCP/IP (VeloGateway)
- ESP32/STM32 + RS485 + Ethernet/WiFi
- Możliwość wielu klientów TCP
- Bridge dla ESP-NOW

## 🚀 Szybki start

1. **Instaluj przez HACS:**
   - HACS → Integrations → ⋮ → Custom repositories
   - Dodaj URL repozytorium
   - Kategoria: Integration
   - Download

2. **Restart Home Assistant**

3. **Dodaj integrację:**
   - Settings → Devices & Services → Add Integration
   - Szukaj: "Velolink"
   - Wybierz typ połączenia (Serial lub TCP)

4. **Discovery:**
   - Kliknij przycisk "Skanuj magistralę"
   - Urządzenia pojawią się automatycznie

## 📚 Dokumentacja

- [Instrukcja instalacji](https://github.com/yourname/velolink-ha/blob/main/docs/installation.md)
- [Konfiguracja](https://github.com/yourname/velolink-ha/blob/main/docs/configuration.md)
- [Rozwiązywanie problemów](https://github.com/yourname/velolink-ha/blob/main/docs/troubleshooting.md)
- [Protokół komunikacji](https://github.com/yourname/velolink-ha/blob/main/docs/protocol.md)

## 💬 Pomoc

- **GitHub Issues:** https://github.com/yourname/velolink-ha/issues
- **Discord:** https://discord.gg/velolink
- **Forum:** https://forum.velolink.pl

---

**Velolink** – Twoja automatyka, Twoja kontrola! 🏠✨
