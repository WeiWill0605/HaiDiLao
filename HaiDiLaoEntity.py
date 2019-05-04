from Core.EntityBase import EntityBase
import PySQL


@PySQL.table(table_name="haidilao_store", db_name="pri_zwei")
class Store(EntityBase):
    loc_name = None
    store_code = None

    address_raw = None
    longitude = None
    latitude = None
    hours_of_operation = None
    phone_raw = None
    phone_1 = None
    phone_2 = None
    city = None
    city_code = None
    country = None
    RunID = None
    RunDate = None
    InsertUpdateTime = None