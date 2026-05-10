# GMP Inspector Mobile App — Setup Guide
## Meta Ray-Ban Wayfarer Gen 2 + Claude API (Flutter)

### Prerequisites

1. **Meta Developer Account**: Register at https://wearables.developer.meta.com/
2. **Flutter SDK**: Install via `winget install Flutter.Flutter` or download from https://flutter.dev
3. **Android Studio** (for Android): Install via `winget install Google.AndroidStudio`
4. **OR Xcode** (for iPhone, Mac only)
5. **Claude API Key**: From https://console.anthropic.com/settings/keys

### How It Works

```
Meta Ray-Ban Glasses
    ↓ (Bluetooth - live 720p @ 30fps JPEG frames)
Your Phone (Flutter App)
    ↓ (captures frame on button tap or auto-interval)  
Claude API (Vision)
    ↓ (analyzes against 8 GMP inspection domains)
Inspection Report
    ↓ (displayed on phone + saved + text-to-speech)
```

### Cost Per Inspection
- Claude API: ~$0.01-0.02 per image analysis
- 100 inspections = ~$1-2
- Your $28 credits = ~1,400-2,800 inspections

### Building the App

```bash
cd "C:\Users\gaura\OneDrive\Desktop\Claude Cowork\Smart Glasses GMP Inspection\gmp_inspector_app"
flutter create gmp_inspector
cd gmp_inspector
flutter pub add meta_wearables
flutter pub add http
flutter pub add flutter_tts
flutter run
```
