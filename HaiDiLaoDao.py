from Core.DaoBase import DaoBase
from Util import DateTimeHelper


class HaiDiLaoDao(DaoBase):

    def __init__(self, **kwargs):
        super(self.__class__, self).__init__(kwargs)
        self.choice_conn(self.CONNECTION_pri_zwei)

    def save(self, entity):
        entity.RunDate = self._run_date
        entity.RunID = self._run_id
        entity.InsertUpdateTime = DateTimeHelper.now()
        self.insert(entity)
