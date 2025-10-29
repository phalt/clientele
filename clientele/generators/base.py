from abc import ABC, abstractmethod


class Generator(ABC):
    """
    Abstract base class for all clientele generators.

    All generators must implement the generate() method to produce
    their respective client code outputs.
    """

    @abstractmethod
    def generate(self) -> None:
        """
        Generate the client code.

        This method should be implemented by all concrete generator classes
        to produce their specific client code outputs.
        """
        raise NotImplementedError
