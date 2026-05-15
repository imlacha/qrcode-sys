from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    # PostgreSQL Configuration
    db_user: str = "postgres"
    db_password: str = "postgres"
    db_host: str = "db"
    db_port: str = "5432"
    db_name: str = "shortener"
    
    # Redis Configuration
    redis_host: str = "redis"
    redis_port: int = 6379
    
    # App Configuration
    port: int = 8000
    base_url: str = "http://localhost:8000"  # fallback

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    @property
    def database_url(self) -> str:
        return f"postgresql+asyncpg://{self.db_user}:{self.db_password}@{self.db_host}:{self.db_port}/{self.db_name}"
    
    @property
    def redis_url(self) -> str:
        return f"redis://{self.redis_host}:{self.redis_port}/0"

    @property
    def resolved_base_url(self) -> str:
        #  如果 .env 有設定公開網址（非 localhost），直接使用
        if self.base_url and "localhost" not in self.base_url:
            return self.base_url

        try:
            import httpx
            # 💡 智慧判斷：連線 ngrok
            targets = ["http://ngrok:4040", "http://localhost:4040"]
            resp = None
            for target in targets:
                try:
                    resp = httpx.get(f"{target}/api/tunnels", headers={"Accept": "application/json"}, timeout=2)
                    if resp.status_code == 200:
                        break
                except Exception:
                    continue

            if resp and resp.status_code == 200:
                tunnels = resp.json().get("tunnels", [])
                if tunnels:
                    for tunnel in tunnels:
                        public_url = tunnel.get("public_url", "")
                        if public_url.startswith("https"):
                            return public_url
                    return tunnels[0].get("public_url", self.base_url)
        except Exception as e:
            print(f"抓取 Ngrok 網址失敗: {e}")
            pass
        return self.base_url

settings = Settings()
