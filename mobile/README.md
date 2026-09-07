# AI Tourism Ecosystem — Mobile Application

This repository contains the React Native mobile application built with Expo for the AI Tourism Ecosystem.

## Architectural Overview

- **Framework**: React Native with Expo SDK 57
- **Target Platforms**: iOS, Android, and Web
- **Backend Protocol**: REST API integration consuming http://localhost:8000/api/v1/destinations
- **Design System**: Strict corporate color scheme (Navy/Slate #0F172A, Corporate Azure #0284C7, Neutral Slate #F8FAFC, Crisp White #FFFFFF)
- **Compliance**: Zero emoji usage across UI, strings, and source documentation

## Features

1. **Destination Directory**: Real-time retrieval and FlatList presentation of destinations.
2. **Search & Category Filtering**: Client-side filtering across destination names, locations, descriptions, and categories (Cultural, Adventure, Nature, Urban).
3. **Resilient Network Architecture**: Automatic fallback to structured reference specifications when the backend service is offline, with integrated connection retry.
4. **Pull to Refresh**: Seamless synchronization with the upstream FastAPI catalog.

## Development Setup

```bash
# Navigate to mobile workspace
cd mobile

# Install dependencies
npm install

# Start development server
npm run start

# Launch on specific targets
npm run web
npm run android
npm run ios
```
