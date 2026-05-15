# API 介面文件

本系統提供縮網址生成、QR Code 讀取以及自動跳轉功能。

## 1. 生成縮網址

將原始長網址轉換為短網址。

- **URL**: `/shorten`
- **Method**: `POST`
- **Query Parameters**:
  - `original_url` (string, required): 原始網址。
  - `color` (string, optional): 指定 QR Code 的顏色（預設為 `black`）。支援顏色包含 `red`, `blue`, `green`, `purple` 等。
- **Response**:
  ```json
  {
    "short_code": "Ab12Cd",
    "short_url": "http://localhost:8000/Ab12Cd",
    "qr_code_api": "http://localhost:8000/qr/Ab12Cd?color=black"
  }
  ```

## 2. 獲取 QR Code

根據短網址代碼獲取對應的 QR Code 圖片。

- **URL**: `/qr/{short_code}`
- **Method**: `GET`
- **Query Parameters**:
  - `color` (string, optional): QR Code 的顏色。
- **Response**: `image/png` (QR Code 圖片串流)

## 3. 短網址跳轉

存取短網址時，系統會記錄點擊次數並自動跳轉至原始網址。

- **URL**: `/{short_code}`
- **Method**: `GET`
- **Response**: `HTML` (內含 JavaScript 跳轉邏輯)

## 錯誤代碼說明

| 狀態碼 | 描述 |
| :--- | :--- |
| 400 | 無效的網址格式或不支援的顏色名稱 |
| 404 | 找不到該短網址代碼 |
| 500 | 伺服器內部錯誤 |
