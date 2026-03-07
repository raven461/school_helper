
import os
import shutil
import argparse
import sys

def copy_files_with_extension(source_dir, target_dir, extension):

    if not os.path.exists(source_dir):
        print(f"Ошибка: Исходная директория '{source_dir}' не существует.")
        sys.exit(1)

    # Создаём целевую директорию, если её нет
    if not os.path.exists(target_dir):
        try:
            os.makedirs(target_dir)
            print("Целевая директория не существует")
            print(f"Создана целевая директория: {target_dir}")
        except Exception as e:
            print(f"Ошибка при создании целевой директории: {e}")
            sys.exit(1)

    # Нормализуем расширение: добавляем точку, если её нет
    if not extension.startswith('.'):
        extension = '.' + extension

    files_to_copy = [
        f for f in os.listdir(source_dir)
        if os.path.isfile(os.path.join(source_dir, f)) and f.endswith(extension)
    ]

    if not files_to_copy:
        print(f"Файлы с расширением '{extension}' в директории '{source_dir}' не найдены.")
        return

    copied_count = 0
    for filename in files_to_copy:
        source_path = os.path.join(source_dir, filename)
        target_path = os.path.join(target_dir, filename)

        try:
            shutil.copy2(source_path, target_path)  # copy2 сохраняет метаданные
            print(f"Скопирован: {filename}")
            copied_count += 1
        except Exception as e:
            print(f"Ошибка при копировании {filename}: {e}")

    print(f"\nВсего скопировано файлов: {copied_count}")

def main():
    parser = argparse.ArgumentParser(
        description="Копирование файлов с задаваемым расширением из одной директории в другую"
    )
    parser.add_argument(
        "source",
        type=str,
        help="Исходная директория"
    )
    parser.add_argument(
        "target",
        type=str,
        help="Целевая директория"
    )
    parser.add_argument(
        "-e", "--extension",
        type=str,
        required=True,
        help="Расширение файлов для копирования (например: .txt, .pdf). Расширение можно записывать без точки в начале"
    )