import logging
from abc import ABC, abstractmethod

logger = logging.getLogger('TorgovoN.BotHandlers.Base')


class BaseBot(ABC):
    """Abstract base for bot handlers"""

    @abstractmethod
    def startBot(self):
        pass

    @abstractmethod
    def stop_bot(self):
        pass