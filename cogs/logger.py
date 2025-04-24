import os
import sys
import logging
import datetime
import importlib
from logging.handlers import RotatingFileHandler
from discord.ext import commands
import colorama
from colorama import Fore, Style
import config

# Get configuration from config.py
LOG_LEVEL = config.LOG_LEVEL.upper()
LOG_MAX_SIZE = config.LOG_MAX_SIZE  # 5 MB default size
LOG_BACKUP_COUNT = config.LOG_BACKUP_COUNT  # Number of backup files

# Mapování textových úrovní logování na konstanty z modulu logging
LOG_LEVELS = {
    'DEBUG': logging.DEBUG,
    'INFO': logging.INFO,
    'WARNING': logging.WARNING,
    'ERROR': logging.ERROR,
    'CRITICAL': logging.CRITICAL
}

class ColoredFormatter(logging.Formatter):
    """Vlastní formátovač pro barevné výstupy v konzoli"""

    COLORS = {
        'DEBUG': Fore.BLUE,
        'INFO': Fore.GREEN,
        'WARNING': Fore.YELLOW,
        'ERROR': Fore.RED,
        'CRITICAL': Fore.RED + Style.BRIGHT
    }

    def format(self, record):
        # Přidáme barvu k úrovni logu v konzoli
        levelname = record.levelname
        if levelname in self.COLORS:
            record.levelname = f"{self.COLORS[levelname]}{levelname}{Style.RESET_ALL}"
        return super().format(record)

class DailyRotatingFileHandler(RotatingFileHandler):
    """Handler pro rotaci logů podle data"""

    def __init__(self, filename, mode='a', maxBytes=0, backupCount=0, encoding=None, delay=False):
        self.date = datetime.datetime.now().date()
        self.base_filename = filename
        filename = self._get_log_filename()
        super().__init__(filename, mode, maxBytes, backupCount, encoding, delay)

    def _get_log_filename(self):
        """Vytvoří název souboru s aktuálním datem"""
        return f"{self.base_filename}-{self.date.strftime('%Y-%m-%d')}.log"

    def emit(self, record):
        """Kontroluje, zda se změnilo datum a případně vytvoří nový soubor"""
        current_date = datetime.datetime.now().date()
        if current_date != self.date:
            self.date = current_date
            self.baseFilename = self._get_log_filename()
            # Pokud existuje starý handler, zavřeme ho
            if self.stream:
                self.stream.close()
                self.stream = None
        super().emit(record)

class LoggerCog(commands.Cog):
    """Cog pro správu logování v Discord botu"""

    def __init__(self, bot):
        self.bot = bot
        self.logger = self._setup_logger()

        # Zachytíme standardní výstupy
        self._redirect_stdout_stderr()

        self.logger.info(f"Logger inicializován s úrovní {LOG_LEVEL}")

    def _setup_logger(self):
        """Nastavení loggeru s konzolí a souborem"""
        logger = logging.getLogger('discord_bot')
        logger.setLevel(LOG_LEVELS.get(LOG_LEVEL, logging.INFO))

        # Odstranění existujících handlerů (pro případ reloadu)
        for handler in logger.handlers[:]:
            logger.removeHandler(handler)

        # Formát logu
        log_format = '%(asctime)s [%(levelname)s] %(message)s'
        date_format = '%Y-%m-%d %H:%M:%S'

        # Konzolový handler s barevným formátováním
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(ColoredFormatter(log_format, date_format))
        logger.addHandler(console_handler)

        # Soubor handler s rotací podle data a velikosti
        os.makedirs('log', exist_ok=True)
        file_handler = DailyRotatingFileHandler(
            filename='log/bot',
            maxBytes=LOG_MAX_SIZE,
            backupCount=LOG_BACKUP_COUNT
        )
        file_handler.setFormatter(logging.Formatter(log_format, date_format))
        logger.addHandler(file_handler)

        return logger

    def _redirect_stdout_stderr(self):
        """Přesměrování stdout a stderr do loggeru"""
        class LoggerWriter:
            def __init__(self, logger, level):
                self.logger = logger
                self.level = level
                self.buffer = ''

            def write(self, message):
                # Pokud je zpráva prázdná nebo jen nový řádek, ignorujeme
                if message and message.strip():
                    self.buffer += message
                    if self.buffer.endswith('\n'):
                        self.logger.log(self.level, self.buffer.rstrip())
                        self.buffer = ''

            def flush(self):
                if self.buffer:
                    self.logger.log(self.level, self.buffer)
                    self.buffer = ''

        # Uložíme původní stdout a stderr
        self.original_stdout = sys.stdout
        self.original_stderr = sys.stderr

        # Přesměrujeme stdout a stderr do loggeru
        sys.stdout = LoggerWriter(self.logger, logging.INFO)
        sys.stderr = LoggerWriter(self.logger, logging.ERROR)

    def cog_unload(self):
        """Obnovení původních stdout a stderr při odinstalaci cogu"""
        sys.stdout = self.original_stdout
        sys.stderr = self.original_stderr
        self.logger.info("Logger byl odinstalován")

    @commands.Cog.listener()
    async def on_ready(self):
        """Zalogování informací o připojení bota"""
        self.logger.info(f"Bot {self.bot.user.name} je připraven a připojen k Discordu")
        self.logger.info(f"Bot je připojen k {len(self.bot.guilds)} serverům")

    @commands.Cog.listener()
    async def on_command(self, ctx):
        """Zalogování použitých příkazů"""
        self.logger.info(
            f"Příkaz: {ctx.command} | "
            f"Uživatel: {ctx.author} (ID: {ctx.author.id}) | "
            f"Server: {ctx.guild.name if ctx.guild else 'DM'} | "
            f"Kanál: {ctx.channel.name if hasattr(ctx.channel, 'name') else 'DM'}"
        )

    @commands.Cog.listener()
    async def on_command_error(self, ctx, error):
        """Zalogování chyb příkazů"""
        self.logger.error(
            f"Chyba příkazu: {ctx.command} | "
            f"Uživatel: {ctx.author} (ID: {ctx.author.id}) | "
            f"Chyba: {error}"
        )

    @commands.Cog.listener()
    async def on_guild_join(self, guild):
        """Zalogování připojení k novému serveru"""
        self.logger.info(f"Bot se připojil k serveru: {guild.name} (ID: {guild.id})")

    @commands.Cog.listener()
    async def on_guild_remove(self, guild):
        """Zalogování odpojení od serveru"""
        self.logger.info(f"Bot byl odpojen od serveru: {guild.name} (ID: {guild.id})")

    @commands.command(name="loglevel")
    @commands.has_permissions(administrator=True)
    async def set_log_level(self, ctx, level: str):
        """Nastaví úroveň logování (admin only)

        Úrovně: DEBUG, INFO, WARNING, ERROR, CRITICAL
        """
        level = level.upper()
        if level not in LOG_LEVELS:
            await ctx.send(f"Neplatná úroveň logování. Povolené hodnoty: {', '.join(LOG_LEVELS.keys())}")
            return

        # Nastavení nové úrovně
        self.logger.setLevel(LOG_LEVELS[level])

        # Aktualizace konfiguračního souboru
        self._update_config_value('LOG_LEVEL', level)

        # Aktualizace globální proměnné
        global LOG_LEVEL
        LOG_LEVEL = level

        self.logger.info(f"Úroveň logování změněna na {level}")
        await ctx.send(f"Úroveň logování nastavena na {level}")

    def _update_config_value(self, key, value):
        """Aktualizuje hodnotu v config.py a znovu načte modul"""
        try:
            # Otevřeme config.py soubor
            with open('config.py', 'r', encoding='utf-8') as file:
                lines = file.readlines()

            # Najdeme řádek s danou proměnnou
            for i, line in enumerate(lines):
                if line.startswith(f"{key} = "):
                    # Aktualizujeme hodnotu podle typu
                    if isinstance(value, str):
                        lines[i] = f'{key} = "{value}"\n'
                    else:
                        lines[i] = f'{key} = {value}\n'
                    break

            # Zapíšeme změny zpět do souboru
            with open('config.py', 'w', encoding='utf-8') as file:
                file.writelines(lines)

            self.logger.info(f"Hodnota {key} byla aktualizována v config.py")

            # Znovu načteme modul config
            importlib.reload(config)

        except Exception as e:
            self.logger.error(f"Chyba při aktualizaci config.py: {e}")

async def setup(bot):
    await bot.add_cog(LoggerCog(bot))
