# Conflict-identificaton

1. Сначала нужно запустить projects_collector: ```python3.12 projects_collector.py```
2. Когда скрипт отработает, появится файл ```github_repos.txt```
3. Перед запуском нижеупомянутого скрипта должна быть создана директория ```materials_for_dataset```
4. В процессе получения датасета был запущен ```conflicts_identification.py```, но в функцию analyze_all_repos был передан параметр "github_repos.txt"
5. Работа скрипта периодически прерывалась (проблемы описаны в файле ```problems.txt```)
6. Для воспроизведения результата нужно запустить ```conflicts_identification.py```
7. После того, как скрипт отработал, в ```materials_for_dataset``` появилась директория ```!https:/github.com```, внутри которой находятся директории вида ```<author>/<repo_name>```. В ```materials_for_dataset``` были добавлены директории вида ```!<author>:<repo_name>``` для всех соответствующих из ```!https:/github.com```, после чего ```!https:/github.com``` была удалена.

Архив с получившимся датасетом: https://disk.yandex.ru/d/RUji7kNCYz9YkQ