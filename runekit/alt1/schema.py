import typing


class AppManifest(typing.TypedDict):
    appName: str
    description: str
    """app startup url relative to current domain"""
    appUrl: str
    """link to a json file which contains this object"""
    configUrl: str
    iconUrl: typing.Optional[str]
    defaultWidth: int
    defaultHeight: int
    minWidth: int
    minHeight: int
    maxWidth: int
    maxHeight: int
    """used to signal alt1 that this app can handle certain requests like a player lookup when the user presses alt+1 over a player name."""
    requestHandlers: typing.List["RequestHandler"]
    activators: typing.List[str]
    permissions: str


class RequestHandler(typing.TypedDict):
    handlerName: str
    handlerUrl: str
    handlerScript: str


UnblendModes = typing.Literal["raw", "removebg", "blackbg"]


class FontMeta(typing.TypedDict):
    basey: int
    spacewidth: int
    treshold: float
    color: typing.Tuple[int, int, int]
    unblendmode: UnblendModes
    shadow: bool
    chars: str
    seconds: str
    img: typing.Optional[str]
    bonus: typing.Optional[typing.Dict[str, int]]
