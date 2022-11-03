from abc import ABC, abstractmethod

class Agent(ABC):

    @abstractmethod
    def launch():
        """
        Perform a loop for the specific task the agent is supposed to do.
        """
        pass