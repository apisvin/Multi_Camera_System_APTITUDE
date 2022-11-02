#TO DO 
# Faire une classe abstraite pour creer les differents types d agents sur une meme base 

from abc import ABC, abstractmethod

class Agent(ABC):

    @abstractmethod
    def launch():
        pass