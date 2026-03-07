import os
import zipfile
import datetime
import argparse
from pathlib import Path
from datetime import datetime,timedelta

def find_newest_file(directory_path):
    path = Path(directory_path).resolve()
    files = [f for f in path.glob('**/*') if f.is_file()]
    if not files:
        return None
    newest = max(files, key=os.path.getctime)
    creation_time = os.path.getctime(newest)
    return datetime.fromtimestamp(creation_time)

def find_oldest_file(directory_path):
    path = Path(directory_path)
    files = [f for f in path.resolve().glob('**/*') if f.is_file()]
    if not files:
        return None
    oldest = min(files, key=os.path.getmtime)
    creation_time = os.path.getctime(oldest)
    return datetime.fromtimestamp(creation_time)

def archive_logs(log_folder_path:str, days_old:int|None=None, delete_originals:bool=False):
    """
    Args:
        log_folder_path (str): Абсолютный путь к папке с log-файлами.
        days_old (int | None): Архивировать только файлы старше N дней.
        delete_originals (bool): Удалить исходные .log-файлы после архивации.
    """

    folder_path = Path(log_folder_path)

    if not folder_path.exists():
        print(f"Ошибка: папка {folder_path} не существует.")
        return
    log_files = list(folder_path.glob("*.log"))
    if not log_files:
        print("В указанной папке нет .log файлов для архивации.")
        return
    
    filtered_files = []
    if days_old is not None:
        cutoff_date = datetime.now() - timedelta(days=days_old)
        for log_file in log_files:
            file_mtime = datetime.fromtimestamp(log_file.stat().st_mtime)
            if file_mtime < cutoff_date:
                filtered_files.append(log_file)
        if not filtered_files:
            print(f"Нет .log файлов старше {days_old} дней для архивации.")
            return
        log_files = filtered_files
    if (find_newest_file(log_folder_path) is None) or (find_oldest_file(log_folder_path) is None):
        print(f"В папке {log_folder_path} отсутствуют файлы.")
        return
    archive_name = f"log_archive {find_oldest_file(log_folder_path).strftime('%Y-%m-%d %H-%M-%S')}   " + \
        f"{find_newest_file(log_folder_path).strftime('%Y-%m-%d %H-%M-%S')}.zip"
    archive_path = folder_path / archive_name

    with zipfile.ZipFile(archive_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for log_file in log_files:
            zipf.write(log_file, log_file.name)
            print(f"    Добавлен в архив: {log_file.name}")

    print(f"\nАрхив успешно создан: {archive_path}")
    print(f"Всего архивировано файлов: {len(log_files)}")

    if delete_originals:
        for log_file in log_files:
            os.remove(log_file)
            print(f"    Удален исходный файл: {log_file.name}")
        print(f"\nУдалено исходных .log файлов: {len(log_files)}")


def main():
    parser = argparse.ArgumentParser(description="Архиватор .log-файлов")
    parser.add_argument("folder", help="Путь к папке с .log-файлами")
    parser.add_argument(
        "-d", "--days",
        type=int,
        help="Архивировать только файлы старше указанного количества дней"
    )
    parser.add_argument(
        "-D", "--delete",
        action="store_true",
        help="Удалить исходные .log-файлы после архивации"
    )

    args = parser.parse_args()

    archive_logs(
        log_folder_path=args.folder,
        days_old=args.days,
        delete_originals=args.delete
    )

if __name__ == "__main__":
    main()
