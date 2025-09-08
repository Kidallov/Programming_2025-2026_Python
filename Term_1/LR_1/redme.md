# Отчет по лабораторной работе №1 "Реализация удаленного импорта"

1. Запустил файл myremotemodule.py, находясь в каталоге этого файла командой 
    ```python3 -m http.server```

2. После запуска сервера открываем второй терминал, переходим в нашу папку и запускаем команду 
```python3 -i activation_script.py```
После запуска команды прописываем уже в редакторе Python команду ```sys.path.append("http://localhost:8000")```
И команду ```import название_файла```, в моем случае было myremotemodule.
После этого если нет ошибок, вводим команду myremotemodule.myfoo() (название_файла.название_функции) и получаем вывод: ```Kidalov Aleksandr's module is imported
Kidalov Aleksandr```
2. Далее с помощью replit я протестировал все тоже самое:
```
~/workspace$ cd LR_ 1/ ~/workspace/LR_1$ ls activation_script.py
rootserver
~/workspace/LR_1$ python3 -i activation_script.py
[‹class 'zipimport zipimporter'>, ‹function FileFinder.path_ _hook. <locals>.path_hook _for_FileFinder at 0x7f8ff4e3c2c0>, <function url_hook at 0x7f8ff4adfe20>]
>> import myremotemodule
Traceback (most recent call last):
File "<stdin>"
, line 1, in ‹module>
ModuleNotFoundError: No module named 'myremotemodule'
>>> sys. path. append ("http://localhost:8000" )
>>› sys. path.append( "https://replit.com/@kidallovv/LL")
>> import myremotemodule
>> myremotemodule.myfoo()
Kidalov Aleksandr's module is imported 
>>> 
```
И вот пример ошибки ```ModuleNotFoundError```, когда, например, забываете сначала запустить сервер.

Переписал содержимое функции url_hook, класса URLLoader с помощью модуля requests (см. код)

### Задание со звездочкой (*): реализовать обработку исключения в ситуации, когда хост (где лежит модуль) недоступен.

Обработка недоступности хоста происходит в нескольких местах:

В функции url_hook:
```
try:
    response = requests.get(some_str, timeout=10)
    response.raise_for_status()
except RequestException as e:
    raise ImportError(f"Ошибка запроса: {e}")
```

В классе URLLoader:
```
try:
    response = requests.get(module.__spec__.origin, timeout=10)
    response.raise_for_status()
except Exception as e:
    raise ImportError(f"Ошибка при загрузке модуля: {e}")
```

Как работает:
1. requests.get() пытается установить соединение с указанным URL
2. Если соединение не удается установить, выбрасывается ConnectionError
3. Если ответ не получен в течение 10 секунд, выбрасывается Timeout
4. Если сервер вернул код ошибки, response.raise_for_status() выбросит HTTPError

### Задание про-уровня (***): реализовать загрузку пакета, разобравшись с аргументами функции spec_from_loader и внутренним устройством импорта пакетов.

Обновили функция find_spec
```
    def find_spec(self, name, target=None):
        mod_path = name.replace('.', '/')
        if name in self.available:
            origin = f"{self.url}/{mod_path}.py"
            loader = URLLoader()
            return spec_from_loader(name, loader, origin=origin)

        pkg_init = f"{name}/__init__.py"
        if name in self.available:
            origin = f"{self.url}/{pkg_init}"
            loader = URLLoader()
            return spec_from_loader(name, loader, origin=origin, is_package=True)
```

И добавили скрипт, который выполняет все:

```
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
```

Вывод:
```
Kidalov Aleksandr's module is imported
Kidalov Aleksandr
mypackage.__init__ ready
Hello from package!
mypackage.submodule ready
Hello from submodule!
```