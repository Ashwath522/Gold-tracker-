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

settings = Settings()
