import os
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

    APP_NAME: str = "Gold Daily Analysis"
    ENV: str = Field(default="development")
    TIMEZONE: str = Field(default="Asia/Kolkata")
    
    # Database
    DATABASE_URL: str = Field(default="sqlite:///./gold_analysis.db")
    
    # Provider Settings
    # Options: "goldapi", "yahoo"
    GOLD_PRICE_PROVIDER: str = Field(default="yahoo")
    GOLDAPI_KEY: str = Field(default="")
    
    # Caching & Fetching
    CACHE_TTL_MINUTES: int = Field(default=30)
    
    # Investment & Tax Defaults
    FIXED_DAILY_AMOUNT: float = Field(default=35.0)
    GST_RATE: float = Field(default=0.03)  # 3% GST on digital gold
    SELL_SPREAD_PCT: float = Field(default=0.03)  # 3% typical buy/sell spread

    # India landed-price adjustment. Raw feeds (Yahoo / GoldAPI) are international
    # prices converted to INR and exclude Indian import duty. Duty is 15% since
    # 13 May 2026 (10% BCD + 5% AIDC). Tune LOCAL_PREMIUM_PCT so the dashboard
    # matches the rate you actually see on PhonePe/Paytm.
    IMPORT_DUTY_PCT: float = Field(default=0.15)
    LOCAL_PREMIUM_PCT: float = Field(default=0.047)  # calibrated vs Paytm Bengaluru, 7 Oct 2026

    # Optional HTTP Basic auth. When BOTH are set, every /api route except
    # /api/health requires them. Set these before exposing the app publicly.
    APP_USERNAME: str = Field(default="")
    APP_PASSWORD: str = Field(default="")

    @property
    def price_multiplier(self) -> float:
        return (1.0 + self.IMPORT_DUTY_PCT) * (1.0 + self.LOCAL_PREMIUM_PCT)

settings = Settings()
