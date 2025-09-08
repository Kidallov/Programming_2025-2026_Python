from importlib.abc import PathEntryFinder
from importlib.util import spec_from_loader
import requests
from requests.exceptions import RequestException, HTTPError
import re
import sys
from urllib.parse import urlparse

class URLFinder(PathEntryFinder):
    def __init__(self, url, available):
        self.url = url # по нему будет проводиться поиск
        self.available = available # список доступных пакетов

    def find_spec(self, name, target=None):
        mod_path = name.replace('.', '/')
        if name in self.available:
            origin = f"{self.url}/{mod_path}.py" # Формируем URL до .py-файла модуля
            loader = URLLoader()
            return spec_from_loader(name, loader, origin=origin)

        pkg_init = f"{name}/__init__.py"
        if name in self.available:
            origin = f"{self.url}/{pkg_init}"
            loader = URLLoader()
            return spec_from_loader(name, loader, origin=origin, is_package=True)

        return None


def url_hook(some_str):
    try:
        # Проверяем корректность URL
        if not some_str.startswith(("http", "https")):
            raise ImportError("URL должен начинаться с http или https")

        # Проверка корректности URL
        parsed_url = urlparse(some_str)
        if not parsed_url.netloc:
            raise ImportError("Некорректный URL")

        # Отправляем GET-запрос
        response = requests.get(some_str, timeout=10)
        response.raise_for_status()  # Вызывает HTTPError при ошибке статуса

        # Находим все файлы .py
        filenames = re.findall(r'[\w_/]+\.py', response.text)
        modnames = set()
        for filename in filenames:
            if filename.endswith("__init__.py"):
                modnames.add(filename[:-12].replace("/", "."))
            else:
                modnames.add(filename[:-3].replace("/", "."))

        return URLFinder(some_str, modnames)

    except HTTPError as e:
        raise ImportError(f"HTTP ошибка: {e}")
    except RequestException as e:
        raise ImportError(f"Ошибка запроса: {e}")
    except Exception as e:
        raise ImportError(f"Произошла ошибка: {e}")


sys.path_hooks.append(url_hook)

class URLLoader:
    def create_module(self):
        return None

    def exec_module(self, module):
        try:
            response = requests.get(module.__spec__.origin, timeout=10)
            response.raise_for_status()
            source = response.text
            code = compile(source, module.__spec__.origin, mode="exec")
            exec(code, module.__dict__)
        except Exception as e:
            raise ImportError(f"Ошибка при загрузке модуля: {e}")


def main():
    try:
        sys.path.append("http://localhost:8000/rootserver")
        import myremotemodule
        print(myremotemodule.myfoo())

        import mypackage
        print(mypackage.greet())

        sys.path.append("http://localhost:8000/rootserver/mypackage")
        import submodule
        print(submodule.hello())

    except ModuleNotFoundError:
        print("Модуль не найден, проверьте URL и доступность сервера")

    except ImportError as e:
        print(f"Ошибка импорта: {e}")

    except Exception as e:
        print(f"Непредвиденная ошибка: {e}")

if __name__ == "__main__":
    main()