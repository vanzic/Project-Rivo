from abc import ABC, abstractmethod

class TrendSource(ABC):
    """
    Interface for a source that provides trends.
    """
    
    @abstractmethod
    def fetch_trends(self) -> list[str]:
        """
        Fetches a list of current trends from the source.
        Returns:
            list[str]: A list of trend strings.
        """
        pass
