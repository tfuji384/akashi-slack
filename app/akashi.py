import logging
from datetime import date, datetime
from typing import Optional

from dateutil.parser import parse
from pydantic import BaseModel, Field, validator
from requests import Response, Session

from .settings import settings

logger = logging.getLogger(__name__)

CLOCK_IN = 11  # 勤務開始
CLOCK_OUT = 12  # 勤務終了
STRAIGHT_TO = 21  # 直行
LEAVE_DIRECTLY = 22  # 直帰
BREAK = 31  # 休憩開始
RESTART = 32  # 休憩終了

STAMP_TYPES = (
    (CLOCK_IN, '勤務を開始:office:'),
    (CLOCK_OUT, '勤務を終了:house:'),
    (STRAIGHT_TO, '直行:train:'),
    (LEAVE_DIRECTLY, '直帰:beer:'),
    (BREAK, '休憩を開始:coffee:'),
    (RESTART, '休憩を終了:computer:'),
)


class StampTypeAnnotator:
    def __init__(self):
        self.stamp_types = dict(STAMP_TYPES)

    def __call__(self, val: int) -> str:
        return self.stamp_types.get(val)


annotate_stamp_type = StampTypeAnnotator()


class AkashiAPIResponse(BaseModel):
    success: bool
    response: Optional[dict]
    code: Optional[str]
    message: Optional[str]


class Stamp(BaseModel):
    stamped_at: datetime
    type: int

    @validator('stamped_at', pre=True)
    @classmethod
    def parse_stamped_at(cls, value):
        return parse(value)


class NewStampResponse(BaseModel):
    stamped_at: datetime = Field(alias='stampedAt')
    type: int

    @validator('stamped_at', pre=True)
    @classmethod
    def parse_stamped_at(cls, value):
        return parse(value)


class FetchedStampResponse(BaseModel):
    count: int
    stamps: list[Stamp]


class ReissuedTokenResponse(BaseModel):
    token: str
    expired_at: datetime

    @validator('expired_at', pre=True)
    @classmethod
    def parse_expired_at(cls, value):
        return parse(value)


class APIError(Exception):
    def __init__(self, response: AkashiAPIResponse, token: str):
        self.code = response.code
        self.message = response.message
        self.token = token

    def __repr__(self):
        return f'{super().__repr__()}[{self.code}]{self.message}(token: {"*"*19}{self.token[23:]})'


class RequestFailedError(Exception):
    def __init__(self, *args, **kwargs):
        self.status_code: int = kwargs.pop('status_code')
        self.url = kwargs.pop('url')
        super().__init__(*args, **kwargs)

    def __repr__(self):
        return f'{super().__repr__()} code:{self.status_code}, url:{self.url}]'


class AkashiRequestClient:
    base_url = 'https://atnd.ak4.jp/api/cooperation'
    company_id = settings.AKASHI_COMPANY_ID

    def __init__(self, user_token: str):
        self.session = Session()
        self.__token = user_token

    def build_url(self, endpoint: str) -> str:
        return f'{self.base_url}{endpoint}'

    def stamp(self, type_: int) -> NewStampResponse:
        endpoint = f'/{self.company_id}/stamps'
        return NewStampResponse(**self.post(endpoint, type=type_))

    def fetch_last_stamp(self) -> Optional[Stamp]:
        current_date = date.today()
        res = self.fetch_stamps(current_date)
        if res.count == 0:
            return None
        return res.stamps[-1]

    def fetch_stamps(self, date_from: date, date_to: date = date.today()) -> FetchedStampResponse:
        endpoint = f'/{self.company_id}/stamps'
        start_date = date_from.strftime('%Y%m%d000000')
        end_date = date_to.strftime('%Y%m%d235959')
        return FetchedStampResponse(**self.get(endpoint=endpoint, start_date=start_date, end_date=end_date))

    def reissue_token(self) -> ReissuedTokenResponse:
        endpoint = f'/token/reissue/{self.company_id}'
        return ReissuedTokenResponse(**self.post(endpoint))

    def get(self, endpoint, **params) -> dict:
        url = self.build_url(endpoint=endpoint)
        params.update(token=self.__token)
        return self.request('get', url, params=params)

    def post(self, endpoint, **data) -> dict:
        url = self.build_url(endpoint=endpoint)
        data.update(token=self.__token)
        return self.request('post', url, data=data)

    def request(self, method: str, url: str, params: Optional[dict] = None, data: Optional[dict] = None) -> dict:
        res = self.request_(method=method, url=url, params=params, data=data)
        if not res.ok:
            raise RequestFailedError(status_code=res.status_code, url=url)
        api_response = AkashiAPIResponse(**res.json())
        if api_response.response:
            return api_response.response
        raise APIError(api_response, self.__token)

    def request_(self, method: str, url: str, params: Optional[dict] = None, data: Optional[dict] = None) -> Response:
        return self.session.request(method=method, url=url, params=params, data=data)
