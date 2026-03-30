from typing import Any, TypeVar, Protocol, runtime_checkable
from fcbyk.utils.storage import load_json, save_json, get_path

T = TypeVar('T')
APP_NAME = "fcbyk"
CONFIG_FILE_NAME = "config.byk.json"


@runtime_checkable
class JsonStorage(Protocol):    
    def load(self, key: str, default: T | None = None) -> T: 
        """加载数据
        Args: 数据键名, 默认值（当数据不存在时返回）
        Returns: 加载的数据或默认值
        """
        ...
    
    def save(self, key: str | dict[str, Any], value: Any | None = None) -> None:
        """保存数据
        Args: 数据键名或完整数据字典, 数据值（当 key 是字符串时必需）
        """
        ...
    
    def delete(self, key: str) -> None:
        """删除数据
        Args: 要删除的数据键名
        """
        ...
    
    def exists(self, key: str) -> bool:
        """检查数据是否存在
        Args: 数据键名
        Returns: True 如果数据存在，否则 False
        """
        ...



class JsonSectionStorage(JsonStorage):
  
    def __init__(self, section: str, app_name: str = APP_NAME):
        self.section = section
        self.config_file = get_path(CONFIG_FILE_NAME, app_name=app_name)
    
    def _load_root(self) -> dict[str, Any]:
        return load_json(self.config_file, default={}, create_if_missing=True, strict=False)
    
    def _save_root(self, root: dict[str, Any]) -> None:
        save_json(self.config_file, root)

    def load(self, key: str, default: T | None = None) -> T:
        root = self._load_root()
        section_data = root.get(self.section, {})
        
        if not key:
            return section_data if section_data else default
        
        return section_data.get(key, default)
    
    def save(self, key: str | dict[str, Any], value: T | None = None) -> None:
        root = self._load_root()
        
        if self.section not in root:
            root[self.section] = {}
        
        if isinstance(key, dict):
            root[self.section].update(key)
        else:
            if not isinstance(key, str):
                raise TypeError("Key must be a string or dict")
            root[self.section][key] = value
        
        self._save_root(root)
    
    def delete(self, key: str) -> None:
        root = self._load_root()
        
        if self.section in root and key in root[self.section]:
            del root[self.section][key]
            self._save_root(root)
    
    def exists(self, key: str) -> bool:
        root = self._load_root()
        return self.section in root and key in root.get(self.section, {})


class JsonFileStorage(JsonStorage):
    
    def __init__(self, filename: str, app_name: str = APP_NAME, subdir: str | None = None):
        self.path = get_path(filename, app_name=app_name, subdir=subdir)
    
    def _load_data(self) -> dict[str, Any]:
        return load_json(self.path, default={}, create_if_missing=True, strict=False)
    
    def _save_data(self, data: dict[str, Any]) -> None:
        save_json(self.path, data)
    
    def load(self, key: str = "", default: Any = None) -> Any:
        data = self._load_data()
        
        if not key:
            return data if data else (default or {})
        
        return data.get(key, default)
    
    def save(self, key: str | dict[str, Any], value: Any = None) -> None:
        if isinstance(key, dict):
            self._save_data(key)
        else:
            if not isinstance(key, str):
                raise TypeError("Key must be a string or dict")
            data = self._load_data()
            data[key] = value
            self._save_data(data)
    
    def delete(self, key: str) -> None:
        data = self._load_data()
        
        if key in data:
            del data[key]
            self._save_data(data)
    
    def exists(self, key: str) -> bool:
        data = self._load_data()
        return key in data


class JsonStorageContext:
    def __init__(self, section: str | None = None,
                 filename: str | None = None,
                 subdir: str | None = None):
        if not section and not filename:
            raise ValueError("Must specify section or filename")
        
        self.section = section
        self.filename = filename
        self.subdir = subdir
        self.storage: JsonStorage | None = None
    
    def __enter__(self) -> JsonStorage:
        if self.filename:
            self.storage = JsonFileStorage(self.filename, subdir=self.subdir)
        elif self.section:
            self.storage = JsonSectionStorage(self.section)
        
        return self.storage
    
    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> bool:
        self.storage = None
        return False