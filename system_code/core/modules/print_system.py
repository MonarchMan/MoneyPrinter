from datetime import datetime

from system_code.core.clickhouse import CKClient, logger
from system_code.core.modules.open_module import OpenPositionModule, BBRsiMaOpenPositionModule, BBRsiMaOpenClusterPositionModule
from system_code.core.modules.close_module import ClosePositionModule, FixClosePositionModule
from system_code.core.modules.backtest import Backtest


class PrintSystem:
    def __init__(self, bar: str, inst_id: str, begin: datetime, end: datetime):
        self.begin = begin
        self.end = end
        self.inst_id = inst_id

        self.open_module = BBRsiMaOpenClusterPositionModule()
        self.close_module = ClosePositionModule()
        self.backtest = Backtest(bar)

        self.ck_client = CKClient(database=f'mc_{bar.upper()}')

    def __str__(self):
        info = f"""\n
        =================================================================
        PrintSystem -> [OpenModule] {self.open_module.name} 
                    -> [CloseModule] {self.close_module.name}
        =================================================================            
        """

        return info

    def fetch_data(self):
        data = self.ck_client.fetch_data(self.inst_id, self.begin, self.end)
        indicators = self.ck_client.fetch_data(self.inst_id, self.begin, self.end, table='indicators')
        # sort
        data = data.sort_values('ts')
        indicators = indicators.sort_values('ts')

        data = data.merge(indicators, on='ts', how='left')

        return data

    def run(self):
        logger.info(f"[Running] {str(self)}")

        data = self.fetch_data()
        holding_groups = self.open_module.open_position(data)
        holding_groups = self.close_module.close_position(holding_groups)
        df = self.backtest.run(holding_groups)
        print(df.to_string())
        self.backtest.plot_all(save=True, begin=self.begin, end=self.end, inst_id=self.inst_id)


if __name__ == '__main__':
    begin = datetime(2024, 2, 4)
    end = datetime(2025, 2, 4)
    inst_id = 'DOGE-USDT-SWAP'
    bar = '5m'

    ps = PrintSystem(bar, inst_id, begin, end)
    ps.run()