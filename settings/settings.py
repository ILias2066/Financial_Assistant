from dataclasses import dataclass
from environs import Env

@dataclass
class Bots:
    token: str


@dataclass
class Settings:
    bots: Bots


def get_settings(path: str):
    env = Env()
    env.read_env(path)
    return Settings(
        bots = Bots(
            token = env.str("TOKEN")
        )
    )

settings = get_settings('.env')
print(get_settings)