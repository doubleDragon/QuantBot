import abc


class Observer(object, metaclass=abc.ABCMeta):
    def __init__(self):
        self.is_terminated = False

    def terminate(self):
        self.is_terminated = True
    
    def tick(self, depths):
        pass
        
    def begin_opportunity_finder(self, depths):
        pass

    def end_opportunity_finder(self):
        pass

    ## abstract
    # @abc.abstractmethod
    def opportunity(self, profit, volume, bprice, kask, sprice, kbid, perc, 
                        w_bprice, w_sprice, 
                        base_currency="CNY", market_currency="BTC"):
        pass
