from authx import AuthX, AuthXConfig

config = AuthXConfig()
config.JWT_ALGORITHM = "HS256"
config.JWT_SECRET_KEY = "SECRET_KEY"

auth: AuthX = AuthX(config=config)
