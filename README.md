# QR Code Distribution System (QR碼分發系統)

這是一個基於 FastAPI 開發的縮網址與 QR Code 生成系統。它能夠將長網址轉換為短網址，並自動生成對應的 QR Code，同時追蹤點擊次數。

## 🚀 核心特色

- **縮網址功能**：自動生成唯一的 6 位元短代碼。
- **動態 QR Code**：根據短網址生成 QR Code，支援自定義顏色。
- **點擊追蹤**：使用 Redis 快取與 PostgreSQL 持久化點擊次數。
- **自動 Ngrok 整合**：在開發環境下自動偵測並使用 Ngrok 公開網址。
- **容器化部署**：支援 Docker Compose 一鍵啟動。

## 🛠️ 技術棧

- **框架**: FastAPI
- **資料庫**: PostgreSQL (SQLAlchemy + asyncpg)
- **快取**: Redis
- **QR 生成**: Segno
- **部署**: Docker / Docker Compose

## 📦 快速開始

### 1. 環境設定

複製 `.env.example` 並重新命名為 `.env`，根據需求修改內容：

```bash
cp .env.example .env
```

重點參數說明：
- `NGROK_AUTHTOKEN`: 若需使用公開測試網址，請填入 Ngrok Token。
- `APP_PORT`: 應用程式對外連接埠（預設 8000）。

### 2. 使用 Docker Compose 啟動

**開發模式 (含 Ngrok):**
```bash
docker-compose --profile dev up --build
```

**正式模式:**
```bash
docker-compose up --build -d
```

### 3. 存取系統

- **API 服務**: `http://localhost:8000`
- **自動文件 (Swagger)**: `http://localhost:8000/docs`

---

## 📖 詳細文件

更多詳細資訊請參閱以下文件：

- [API 介面說明](./docs/api.md)
- [系統架構與設計](./docs/architecture.md)

## 🧪 測試

執行以下指令進行簡單測試：

```bash
python test.py
```
