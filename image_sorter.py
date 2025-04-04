import os
import sys
import json
import shutil
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
from PIL import Image, ImageTk
import threading
import time
import subprocess  # Добавляем импорт для запуска проводника

class HotkeyDialog(tk.Toplevel):
    def __init__(self, parent, folder_name, current_hotkey=None):
        super().__init__(parent)
        self.parent = parent
        self.folder_name = folder_name
        self.result = None
        self.current_key = current_hotkey
        
        # Настройка окна
        self.title("Select Hotkey")
        self.geometry("300x150")
        self.resizable(False, False)
        self.transient(parent)  # Делаем окно модальным
        self.grab_set()  # Захватываем фокус
        
        # Центрируем окно
        self.update_idletasks()
        width = self.winfo_width()
        height = self.winfo_height()
        x = (self.winfo_screenwidth() // 2) - (width // 2)
        y = (self.winfo_screenheight() // 2) - (height // 2)
        self.geometry('{}x{}+{}+{}'.format(width, height, x, y))
        
        # Гарантируем, что окно получит фокус
        self.focus_force()
        self.lift()
        self.attributes('-topmost', True)
        self.after(10, lambda: self.attributes('-topmost', False))
        
        # Создаем виджеты
        ttk.Label(self, text=f"Press any key for folder '{folder_name}'").pack(pady=10)
        
        # Поле для отображения текущей клавиши
        self.key_var = tk.StringVar(value="Press a key..." if not current_hotkey else current_hotkey)
        self.key_label = ttk.Label(self, textvariable=self.key_var, font=("Arial", 12, "bold"))
        self.key_label.pack(pady=10)
        
        # Кнопка отмены
        button_frame = ttk.Frame(self)
        button_frame.pack(pady=10, fill=tk.X)
        
        ttk.Button(button_frame, text="Cancel", command=self.cancel).pack(side=tk.BOTTOM, padx=10, expand=True)
        
        # Привязываем обработчик нажатий клавиш
        self.bind("<KeyPress>", self.on_key_press)
        
        # Ждем закрытия окна
        self.wait_window()
    
    def on_key_press(self, event):
        """Обрабатывает нажатие клавиши"""
        # Получаем имя клавиши
        key_name = self.get_key_name(event)
        
        # Обновляем отображение и сразу сохраняем
        if key_name:
            self.key_var.set(key_name)
            self.current_key = key_name
            # Сразу сохраняем и закрываем окно
            self.after(200, self.save)  # Небольшая задержка, чтобы пользователь увидел клавишу
    
    def get_key_name(self, event):
        """Получает имя клавиши из события"""
        # Игнорируем служебные клавиши
        if event.keysym in ('Shift_L', 'Shift_R', 'Control_L', 'Control_R', 
                           'Alt_L', 'Alt_R', 'Caps_Lock', 'Tab'):
            return None
        
        # Для специальных клавиш используем их имена
        if event.keysym in ('space', 'Return', 'BackSpace', 'Delete', 'Escape',
                          'Up', 'Down', 'Left', 'Right', 'Home', 'End', 'Page_Up', 'Page_Down',
                          'F1', 'F2', 'F3', 'F4', 'F5', 'F6', 'F7', 'F8', 'F9', 'F10', 'F11', 'F12'):
            return event.keysym
        
        # Для обычных клавиш используем символ
        if len(event.char) > 0:
            return event.char
        
        # Если не удалось определить, используем keysym
        return event.keysym
    
    def save(self):
        """Сохраняет выбранную клавишу и закрывает окно"""
        if self.current_key:
            self.result = self.current_key
            self.destroy()
    
    def cancel(self):
        """Отменяет выбор и закрывает окно"""
        self.result = None
        self.destroy()

class ToolTip(object):
    def __init__(self, widget, text):
        self.widget = widget
        self.text = text
        self.tipwindow = None
        self.id = None
        self.x = self.y = 0

    def showtip(self, text):
        "Display text in tooltip window"
        self.text = text
        if self.tipwindow or not self.text:
            return
        
        # Получаем координаты курсора мыши вместо виджета
        x = self.widget.winfo_pointerx()
        y = self.widget.winfo_pointery()
        
        # Создаем всплывающее окно
        self.tipwindow = tw = tk.Toplevel(self.widget)
        tw.overrideredirect(True)
        tw.wm_overrideredirect(True)
        
        # Создаем метку с текстом
        label = tk.Label(tw, text=self.text, justify=tk.LEFT,
                      background="#ffffe0", relief=tk.SOLID, borderwidth=1,
                      font=("tahoma", "8", "normal"))
        label.pack(ipadx=1)
        
        # Размещаем окно слева от курсора
        tw.update_idletasks()  # Обновляем, чтобы получить размеры окна
        width = tw.winfo_width()
        
        # Размещаем окно слева от курсора, но проверяем, чтобы не выйти за левый край экрана
        if x - width - 10 > 0:
            x = x - width - 10  # Смещаем влево от курсора
        else:
            x = 0  # Если выходит за левый край, прижимаем к левому краю
            
        tw.wm_geometry("+%d+%d" % (x, y))

    def hidetip(self):
        tw = self.tipwindow
        self.tipwindow = None
        if tw:
            tw.destroy()

def createToolTip(widget, text):
    toolTip = ToolTip(widget, text)
    def enter(event):
        toolTip.showtip(text)
    def leave(event):
        toolTip.hidetip()
    widget.bind('<Enter>', enter)
    widget.bind('<Leave>', leave)

class ImageSorter:
    def __init__(self, root):
        self.root = root
        self.root.title("Image Sorter")
        self.root.geometry("1200x800")  # Фиксированный начальный размер окна
        self.root.minsize(800, 600)
        
        # Инициализируем переменные
        self.current_image = None
        self.current_photo = None  # Сохраняем ссылку на PhotoImage
        self.image_files = []
        self.current_index = -1
        self.folders = []
        self.folder_hotkeys = {}  # Словарь для хранения горячих клавиш папок
        self.processed_images = 0  # Счетчик обработанных изображений
        self.total_images = 0  # Общее количество изображений
        self.resize_timer = None  # Таймер для отложенного обновления размера
        self.is_processing = False  # Флаг для защиты от двойного клика
        self.folder_buttons = {}  # Словарь для хранения кнопок папок
        self.current_file = None  # Текущий обрабатываемый файл
        self.processing_lock = False  # Блокировка обработки
        self.animation_frames = []  # Кадры анимации
        self.animation_timer = None  # Таймер для анимации
        self.move_history = []  # История перемещений для функции Undo
        self.hotkey_to_index = {}  # Словарь для быстрого поиска индекса папки по горячей клавише
        self.settings_file = "image_sorter_settings.json"  # Имя файла настроек
        
        # Получаем путь к папке, в которой находится скрипт
        if getattr(sys, 'frozen', False):
            self.app_path = os.path.dirname(sys.executable)
        else:
            self.app_path = os.path.dirname(os.path.abspath(__file__))
        
        # Поддерживаемые форматы изображений
        self.image_extensions = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp'}
        
        # Создаем интерфейс
        self.create_ui()
        
        # Привязываем обработчик закрытия окна
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        
        # Запускаем загрузку в фоне после создания интерфейса
        self.root.after(100, self.initialize_app)
    
    def save_settings(self):
        """Сохраняет настройки в JSON-файл"""
        try:
            # Создаем словарь с настройками
            settings = {
                "folder_hotkeys": self.folder_hotkeys
            }
            
            # Полный путь к файлу настроек
            settings_path = os.path.join(self.app_path, self.settings_file)
            
            # Сохраняем в JSON
            with open(settings_path, 'w', encoding='utf-8') as f:
                json.dump(settings, f, ensure_ascii=False, indent=4)
                
            self.status_var.set("Settings saved")
        except Exception as e:
            self.status_var.set(f"Error saving settings: {str(e)}")
    
    def load_settings(self):
        """Загружает настройки из JSON-файла"""
        try:
            # Полный путь к файлу настроек
            settings_path = os.path.join(self.app_path, self.settings_file)
            
            # Проверяем, существует ли файл
            if os.path.exists(settings_path):
                # Загружаем из JSON
                with open(settings_path, 'r', encoding='utf-8') as f:
                    settings = json.load(f)
                
                # Загружаем хоткеи
                if "folder_hotkeys" in settings:
                    self.folder_hotkeys = settings["folder_hotkeys"]
                    self.status_var.set("Settings loaded")
        except Exception as e:
            self.status_var.set(f"Error loading settings: {str(e)}")
            # Если произошла ошибка, используем пустые настройки
            self.folder_hotkeys = {}
    
    def initialize_app(self):
        """Инициализация приложения после создания интерфейса"""
        # Загружаем настройки
        self.load_settings()
        
        # Загружаем список папок
        self.folders = self.get_existing_folders()
        self.create_folder_buttons()
        
        # Загружаем изображения
        self.load_images()
        
        # Привязываем горячие клавиши
        self.bind_keys()
        
        # Добавляем обработчики изменения размера окна
        self.root.bind("<Configure>", self.on_window_resize)
        self.root.bind("<F11>", self.on_fullscreen)  # Для F11
        self.root.bind("<Escape>", self.on_fullscreen)  # Для выхода из полноэкранного режима
        
        # Отслеживаем состояние полноэкранного режима
        self.is_fullscreen = False
    
    def on_closing(self):
        """Обработчик закрытия окна"""
        # Сохраняем настройки перед закрытием
        self.save_settings()
        
        # Очищаем ссылки на изображения
        self.current_image = None
        self.current_photo = None
        self.image_label.configure(image='')
        
        # Закрываем окно
        self.root.quit()
        self.root.destroy()
    
    def get_existing_folders(self):
        """Получает список существующих папок в директории"""
        folders = []
        for item in os.listdir(self.app_path):
            item_path = os.path.join(self.app_path, item)
            if os.path.isdir(item_path) and not item.startswith('.'):
                folders.append(item)
        return sorted(folders)
    
    def create_ui(self):
        """Создает пользовательский интерфейс"""
        # Главный контейнер
        main_container = ttk.Frame(self.root)
        main_container.pack(fill=tk.BOTH, expand=True)
        
        # Боковая панель
        sidebar = ttk.Frame(main_container, padding=(10, 10), width=300)  # Фиксированная ширина
        sidebar.pack(side=tk.RIGHT, fill=tk.Y)
        sidebar.pack_propagate(False)  # Запрещаем изменение размера
        
        # Кнопка "Пропустить"
        skip_frame = ttk.Frame(sidebar)
        skip_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Кнопка "Отменить" (Undo)
        undo_btn = ttk.Button(
            skip_frame,
            text="Undo",
            command=self.undo_last_action
        )
        undo_btn.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        
        # Метка с хоткеем для отмены
        undo_hotkey = ttk.Label(skip_frame, text="[Ctrl+Z]", padding=(5, 0))
        undo_hotkey.pack(side=tk.LEFT)
        
        skip_btn = ttk.Button(
            skip_frame,
            text="Skip",
            command=self.show_next_image
        )
        skip_btn.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        # Метка с хоткеем для пропуска
        skip_hotkey = ttk.Label(skip_frame, text="[Space]", padding=(5, 0))
        skip_hotkey.pack(side=tk.LEFT)
        
        # Создаем фрейм для списка папок
        self.folders_frame = ttk.Frame(sidebar)
        self.folders_frame.pack(fill=tk.BOTH, expand=True)
        
        # Фрейм для кнопок папок
        self.buttons_frame = ttk.Frame(self.folders_frame)
        self.buttons_frame.pack(fill=tk.BOTH, expand=True)
        
        # Создаем кнопки для папок
        self.create_folder_buttons()
        
        # Кнопка добавления новой папки
        add_btn = ttk.Button(sidebar, text="+ Add Folder", command=self.add_folder)
        add_btn.pack(fill=tk.X, pady=(10, 0))
        
        # Информация
        info_frame = ttk.LabelFrame(sidebar, text="Information", padding=(5, 5))
        info_frame.pack(fill=tk.X, pady=10)
        
        # Текущий файл
        self.filename_var = tk.StringVar()
        filename_label = ttk.Label(info_frame, textvariable=self.filename_var, wraplength=250)  # Ограничиваем ширину текста
        filename_label.pack(anchor=tk.W, pady=(0, 5), fill=tk.X)
        
        # Кнопка "Открыть в проводнике"
        self.explorer_btn = ttk.Button(
            info_frame,
            text="Open in Explorer",
            command=self.open_in_explorer,
            state='disabled'  # Изначально кнопка неактивна
        )
        self.explorer_btn.pack(fill=tk.X, pady=(0, 5))
        
        # Счетчик обработанных
        self.images_count_var = tk.StringVar(value="Processed: 0")
        ttk.Label(info_frame, textvariable=self.images_count_var).pack(anchor=tk.W)
        
        # Статус
        self.status_var = tk.StringVar(value="Loading images...")
        ttk.Label(sidebar, textvariable=self.status_var).pack(anchor=tk.W, pady=10)
        
        # Контейнер для изображения
        self.image_frame = ttk.Frame(main_container)
        self.image_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # Метка для отображения изображения
        self.image_label = ttk.Label(self.image_frame)
        self.image_label.pack(fill=tk.BOTH, expand=True)
    
    def create_folder_buttons(self):
        """Создает кнопки для каждой папки"""
        # Очищаем словарь кнопок
        self.folder_buttons.clear()
        
        # Удаляем старые кнопки
        for widget in self.buttons_frame.winfo_children():
            widget.destroy()
        
        # Создаем новые кнопки для каждой папки
        for i, folder in enumerate(self.folders):
            frame = ttk.Frame(self.buttons_frame)
            frame.pack(fill=tk.X, pady=2)
            
            # Создаем кнопку
            btn = ttk.Button(
                frame,
                text=folder,
            )
            # Привязываем обработчик через bind вместо command
            btn.bind('<Button-1>', lambda e, idx=i: self.handle_folder_click(e, idx))
            btn.pack(side=tk.LEFT, fill=tk.X, expand=True)
            
            # Сохраняем кнопку в словарь
            self.folder_buttons[folder] = btn
            
            # Кнопка выбора горячей клавиши
            if folder in self.folder_hotkeys:
                hotkey = self.folder_hotkeys[folder]
                hotkey_text = hotkey
                # Для специальных клавиш делаем более понятные надписи
                special_keys = {
                    'space': 'Space',
                    'Return': 'Enter',
                    'BackSpace': 'Back',
                    'Delete': 'Del',
                    'Escape': 'Esc',
                    'Page_Up': 'PgUp',
                    'Page_Down': 'PgDn'
                }
                if hotkey in special_keys:
                    hotkey_text = special_keys[hotkey]
                
                hotkey_btn = ttk.Button(
                    frame,
                    text=f"[{hotkey_text}]",
                    width=6,
                    command=lambda f=folder: self.show_hotkey_menu(f)
                )
            else:
                # Пустая кнопка, если нет горячей клавиши
                hotkey_btn = ttk.Button(
                    frame,
                    text="[ ]",
                    width=6,
                    command=lambda f=folder: self.show_hotkey_menu(f)
                )
            hotkey_btn.pack(side=tk.LEFT, padx=2)
            createToolTip(hotkey_btn, "Click to set hotkey")
            
            # Кнопка редактирования
            edit_btn = ttk.Button(
                frame,
                text="R",  # Латинская буква R (Rename)
                width=3,
                command=lambda f=folder: self.rename_folder(f)
            )
            edit_btn.pack(side=tk.LEFT, padx=2)
            createToolTip(edit_btn, "Rename folder")
            
            # Кнопка удаления
            del_btn = ttk.Button(
                frame,
                text="X",  # Латинская буква X (Delete/Remove)
                width=3,
                command=lambda f=folder: self.delete_folder(f)
            )
            del_btn.pack(side=tk.LEFT)
            createToolTip(del_btn, "Delete folder")
    
    def handle_folder_click(self, event, folder_index):
        """Обработчик клика по кнопке папки"""
        # Получаем кнопку, на которую нажали
        btn = event.widget
        
        # Проверяем блокировки
        if self.processing_lock or str(btn['state']) == 'disabled':
            return
            
        # Проверяем базовые условия
        if not self.current_image or folder_index >= len(self.folders):
            return
            
        try:
            # Устанавливаем блокировку
            self.processing_lock = True
            
            # Проверяем, что текущий файл существует и не изменился
            if not self.current_file or self.current_file != self.image_files[self.current_index]:
                return
                
            # Проверяем, существует ли исходный файл
            src = self.image_files[self.current_index]
            if not os.path.exists(src):
                return
                
            # Блокируем все кнопки папок
            for btn in self.folder_buttons.values():
                btn.configure(state='disabled')
            
            # Создаем папку, если её нет
            folder_name = self.folders[folder_index]
            folder_path = os.path.join(self.app_path, folder_name)
            if not os.path.exists(folder_path):
                os.makedirs(folder_path)
            
            # Получаем путь назначения
            dst = os.path.join(folder_path, os.path.basename(src))
            
            # Закрываем текущее изображение и очищаем память
            if self.current_image:
                self.current_image.close()
            self.current_image = None
            self.current_photo = None
            self.image_label.configure(image='')
            
            # Даем время на освобождение файла
            self.root.update()
            time.sleep(0.1)
            
            # Пробуем разные способы перемещения файла
            success = False
            try:
                # Сначала пробуем просто переместить
                shutil.move(src, dst)
                success = True
                # Сохраняем информацию о перемещении для функции Undo
                self.move_history.append((src, dst))
            except:
                try:
                    # Если не получилось, пробуем копировать и удалить
                    shutil.copy2(src, dst)
                    os.remove(src)
                    success = True
                    # Сохраняем информацию о перемещении для функции Undo
                    self.move_history.append((src, dst))
                except:
                    pass
            
            if success:
                # Удаляем файл из списка и показываем следующий
                self.image_files.pop(self.current_index)
                if self.image_files:
                    if self.current_index >= len(self.image_files):
                        self.current_index = 0
                    self.show_image(self.current_index)
                else:
                    self.current_image = None
                    self.current_file = None
                    self.image_label.configure(image='')
                    self.status_var.set("All images processed")
                
                # Увеличиваем счетчик обработанных изображений
                self.processed_images += 1
                self.update_counter()
                
                # Обновляем статус с информацией о последнем действии
                self.status_var.set(f"Moved to: {folder_name}")
            else:
                # Если не удалось переместить, просто пропускаем файл
                self.show_next_image()
            
        finally:
            # Разблокируем кнопки и снимаем блокировку
            self.processing_lock = False
            for btn in self.folder_buttons.values():
                btn.configure(state='normal')
    
    def show_hotkey_menu(self, folder):
        """Открывает диалог выбора горячей клавиши"""
        current_hotkey = self.folder_hotkeys.get(folder)
        dialog = HotkeyDialog(self.root, folder, current_hotkey)
        
        # Если пользователь выбрал клавишу
        if dialog.result:
            # Проверяем, не занята ли эта клавиша другой папкой
            used_by = None
            for f, h in self.folder_hotkeys.items():
                if h == dialog.result and f != folder:
                    used_by = f
                    break
            
            if used_by:
                # Если клавиша занята, спрашиваем подтверждение
                if messagebox.askyesno("Confirmation", 
                                      f"Key '{dialog.result}' is already assigned to folder '{used_by}'.\n\n" +
                                      "Reassign it to the current folder?"):
                    # Удаляем старую привязку
                    del self.folder_hotkeys[used_by]
                    # Устанавливаем новую
                    self.folder_hotkeys[folder] = dialog.result
                    self.create_folder_buttons()
                    self.bind_keys()
                    # Сохраняем настройки
                    self.save_settings()
            else:
                # Если клавиша свободна, просто назначаем её
                self.folder_hotkeys[folder] = dialog.result
                self.create_folder_buttons()
                self.bind_keys()
                # Сохраняем настройки
                self.save_settings()
    
    def reassign_hotkey(self, new_folder, hotkey, old_folder):
        """Переназначает горячую клавишу с одной папки на другую"""
        # Удаляем горячую клавишу у старой папки
        if old_folder in self.folder_hotkeys:
            del self.folder_hotkeys[old_folder]
        
        # Устанавливаем горячую клавишу для новой папки
        self.folder_hotkeys[new_folder] = hotkey
        self.create_folder_buttons()
        self.bind_keys()
    
    def set_folder_hotkey(self, folder, hotkey):
        """Устанавливает горячую клавишу для папки"""
        self.folder_hotkeys[folder] = hotkey
        self.create_folder_buttons()
        self.bind_keys()
    
    def add_folder(self):
        """Добавляет новую папку"""
        name = simpledialog.askstring("New Folder", "Enter folder name:")
        if name:
            if name in self.folders:
                messagebox.showerror("Error", "Folder with this name already exists")
                return
            
            try:
                # Создаем папку
                folder_path = os.path.join(self.app_path, name)
                os.makedirs(folder_path)
                
                # Добавляем в список
                self.folders.append(name)
                self.folders.sort()  # Сортируем список папок
                
                # Обновляем интерфейс
                self.create_folder_buttons()
                self.status_var.set(f"Folder added: {name}")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to create folder: {str(e)}")
    
    def rename_folder(self, old_name):
        """Переименовывает существующую папку"""
        new_name = simpledialog.askstring("Rename Folder", 
                                        "Enter new folder name:", 
                                        initialvalue=old_name)
        if new_name and new_name != old_name:
            if new_name in self.folders:
                messagebox.showerror("Error", "Folder with this name already exists")
                return
            
            try:
                # Переименовываем папку
                old_path = os.path.join(self.app_path, old_name)
                new_path = os.path.join(self.app_path, new_name)
                os.rename(old_path, new_path)
                
                # Обновляем список
                idx = self.folders.index(old_name)
                self.folders[idx] = new_name
                self.folders.sort()  # Сортируем список папок
                
                # Обновляем интерфейс
                self.create_folder_buttons()
                self.status_var.set(f"Folder renamed: {old_name} → {new_name}")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to rename folder: {str(e)}")
    
    def delete_folder(self, folder_name):
        """Удаляет папку"""
        if len(self.folders) <= 1:
            messagebox.showerror("Error", "Cannot delete the last folder")
            return
        
        if messagebox.askyesno("Confirmation", 
                              f"Delete folder '{folder_name}'?\n\n" +
                              "Warning: all files in the folder will also be deleted!"):
            try:
                # Удаляем папку
                folder_path = os.path.join(self.app_path, folder_name)
                shutil.rmtree(folder_path)
                
                # Обновляем список
                self.folders.remove(folder_name)
                
                # Обновляем интерфейс
                self.create_folder_buttons()
                self.status_var.set(f"Folder deleted: {folder_name}")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to delete folder: {str(e)}")
    
    def bind_keys(self):
        """Привязка горячих клавиш"""
        # Навигация
        self.root.bind("<Right>", lambda event: self.show_next_image())
        self.root.bind("<Left>", lambda event: self.show_prev_image())
        self.root.bind("<space>", lambda event: self.show_next_image())  # Пропуск изображения
        self.root.bind("<Control-z>", lambda event: self.undo_last_action())  # Отмена последнего действия
        
        # Добавляем обработчик всех клавиш для работы независимо от раскладки
        self.root.bind("<KeyPress>", self.handle_keypress)
        
        # Создаем словарь для быстрого поиска индекса папки по горячей клавише
        self.hotkey_to_index = {}
        for i, folder in enumerate(self.folders):
            if folder in self.folder_hotkeys:
                hotkey = self.folder_hotkeys[folder]
                self.hotkey_to_index[hotkey] = i
    
    def handle_keypress(self, event):
        """Обрабатывает нажатия клавиш независимо от раскладки"""
        # Получаем код клавиши
        key_code = event.keycode
        
        # Обработка Ctrl+Z (отмена) по коду
        # Z обычно имеет код 90
        if key_code == 90 and event.state & 0x4:  # 0x4 - это Ctrl
            self.undo_last_action()
            return
        
        # Обработка пробела (пропуск) по коду
        # Пробел обычно имеет код 32
        if key_code == 32:
            self.show_next_image()
            return
        
        # Обработка стрелок по коду
        # Стрелка влево обычно имеет код 37, вправо - 39
        if key_code == 37:  # Стрелка влево
            self.show_prev_image()
            return
        elif key_code == 39:  # Стрелка вправо
            self.show_next_image()
            return
        
        # Получаем имя клавиши
        key_name = None
        
        # Для специальных клавиш используем их имена
        if event.keysym in ('space', 'Return', 'BackSpace', 'Delete', 'Escape',
                          'Up', 'Down', 'Left', 'Right', 'Home', 'End', 'Page_Up', 'Page_Down',
                          'F1', 'F2', 'F3', 'F4', 'F5', 'F6', 'F7', 'F8', 'F9', 'F10', 'F11', 'F12'):
            key_name = event.keysym
        # Для обычных клавиш используем символ
        elif len(event.char) > 0:
            key_name = event.char
        # Если не удалось определить, используем keysym
        else:
            key_name = event.keysym
        
        # Проверяем, есть ли такая горячая клавиша
        if key_name in self.hotkey_to_index:
            folder_index = self.hotkey_to_index[key_name]
            self.move_to_folder(folder_index)
            return
        
        # Обработка цифровых клавиш (0-9) по их коду
        # Коды клавиш 0-9 обычно 48-57 (верхний ряд) или 96-105 (цифровая клавиатура)
        digit_keys = {
            # Верхний ряд цифр
            48: '0', 49: '1', 50: '2', 51: '3', 52: '4',
            53: '5', 54: '6', 55: '7', 56: '8', 57: '9',
            # Цифровая клавиатура
            96: '0', 97: '1', 98: '2', 99: '3', 100: '4',
            101: '5', 102: '6', 103: '7', 104: '8', 105: '9'
        }
        
        # Поддержка старого поведения с цифрами
        if key_code in digit_keys:
            digit = digit_keys[key_code]
            
            # Если нет папки с такой горячей клавишей, используем индекс
            digit_index = int(digit)
            if digit_index < len(self.folders):
                self.move_to_folder(digit_index)
    
    def load_images(self):
        """Загружает список изображений из текущей директории"""
        try:
            # Получаем список всех файлов с изображениями
            self.image_files = [
                os.path.join(self.app_path, f) for f in os.listdir(self.app_path)
                if os.path.isfile(os.path.join(self.app_path, f)) and  # Проверяем что это файл
                os.path.splitext(f)[1].lower() in self.image_extensions
            ]
            
            if self.image_files:
                # Сортируем файлы по имени
                self.image_files.sort()
                # Обновляем общее количество изображений
                self.total_images = len(self.image_files)
                # Обновляем счетчик
                self.update_counter()
                # Показываем первое изображение
                self.show_image(0)
                self.status_var.set("Ready to work")
            else:
                self.status_var.set("No images found in the current folder")
                
        except Exception as e:
            self.status_var.set(f"Error scanning: {str(e)}")
    
    def update_counter(self):
        """Обновляет счетчик обработанных изображений"""
        self.images_count_var.set(f"Processed: {self.processed_images}/{self.total_images}")
    
    def on_window_resize(self, event):
        """Обработчик изменения размера окна"""
        # Проверяем, что событие пришло от главного окна
        if event.widget == self.root:
            # Отменяем предыдущий отложенный вызов
            if self.resize_timer:
                self.root.after_cancel(self.resize_timer)
            # Создаем новый отложенный вызов
            self.resize_timer = self.root.after(100, self.update_image_size)
    
    def update_image_size(self):
        """Обновляет размер изображения в соответствии с размером окна"""
        if not self.current_image:
            return
            
        # Получаем размеры области отображения
        frame_width = self.image_frame.winfo_width()
        frame_height = self.image_frame.winfo_height()
        
        if frame_width <= 1 or frame_height <= 1:  # Окно еще не отрисовано
            self.resize_timer = self.image_frame.after(100, self.update_image_size)
            return
            
        # Получаем размеры изображения
        img_width, img_height = self.current_image.size
        
        # Вычисляем соотношение сторон
        frame_ratio = frame_width / frame_height
        img_ratio = img_width / img_height
        
        # Определяем новые размеры
        if frame_ratio > img_ratio:
            # Ограничение по высоте
            new_height = frame_height
            new_width = int(new_height * img_ratio)
        else:
            # Ограничение по ширине
            new_width = frame_width
            new_height = int(new_width / img_ratio)
        
        # Масштабируем изображение
        resized_image = self.current_image.resize((new_width, new_height), Image.Resampling.LANCZOS)
        
        # Создаем новый PhotoImage и сохраняем ссылку
        self.current_photo = ImageTk.PhotoImage(resized_image)
        self.image_label.configure(image=self.current_photo)
    
    def show_image(self, index):
        """Показывает изображение с указанным индексом"""
        if not self.image_files or index < 0 or index >= len(self.image_files):
            return
        
        try:
            # Останавливаем предыдущую анимацию если была
            if self.animation_timer:
                self.root.after_cancel(self.animation_timer)
                self.animation_timer = None
            self.animation_frames.clear()
            
            # Сохраняем текущий файл
            self.current_file = self.image_files[index]
            
            # Загружаем и отображаем изображение
            self.current_index = index
            self.current_image = Image.open(self.image_files[index])
            
            # Проверяем, является ли изображение анимированным GIF
            is_animated = False
            try:
                # Более надежный способ определения анимированного GIF
                if self.current_image.format == 'GIF':
                    # Пробуем перейти ко второму кадру - если это возможно, значит GIF анимированный
                    self.current_image.seek(1)
                    is_animated = True
                    # Возвращаемся к первому кадру
                    self.current_image.seek(0)
            except (EOFError, AttributeError):
                # Если возникла ошибка EOFError, значит в GIF только один кадр
                is_animated = False
                
            if is_animated:
                # Загружаем все кадры анимации
                try:
                    frame_count = 0
                    durations = []
                    
                    while True:
                        # Сохраняем длительность текущего кадра
                        duration = self.current_image.info.get('duration', 100)
                        durations.append(duration)
                        
                        # Копируем текущий кадр
                        frame = self.current_image.copy()
                        # Масштабируем кадр
                        scaled_frame = self.scale_image(frame)
                        # Конвертируем в PhotoImage
                        photo = ImageTk.PhotoImage(scaled_frame)
                        self.animation_frames.append((photo, duration))
                        
                        # Переходим к следующему кадру
                        frame_count += 1
                        self.current_image.seek(frame_count)
                except EOFError:
                    pass  # Достигнут конец файла (все кадры загружены)
                
                # Показываем первый кадр
                if self.animation_frames:
                    self.current_photo = self.animation_frames[0][0]
                    self.image_label.configure(image=self.animation_frames[0][0])
                    # Запускаем анимацию
                    self.animate_gif(0)
            else:
                # Обычное изображение
                self.update_image_size()
            
            # Обновляем информацию о файле
            filename = os.path.basename(self.image_files[index])
            filesize = os.path.getsize(self.image_files[index])
            self.filename_var.set(f"File: {filename}\nSize: {self.format_file_size(filesize)}")
            
            # Активируем кнопку "Открыть в проводнике"
            self.explorer_btn.configure(state='normal')
            
            # Разблокируем все кнопки папок
            for btn in self.folder_buttons.values():
                btn.configure(state='normal')
            
        except Exception as e:
            self.status_var.set(f"Error loading image: {str(e)}")
    
    def animate_gif(self, frame_index):
        """Показывает следующий кадр анимированного GIF"""
        if not self.animation_frames:
            return
            
        # Показываем текущий кадр
        frame, duration = self.animation_frames[frame_index]
        self.current_photo = frame
        self.image_label.configure(image=frame)
        
        # Определяем следующий кадр
        next_frame = (frame_index + 1) % len(self.animation_frames)
        
        # Используем сохраненную длительность для текущего кадра
        # Минимальная длительность - 20 мс, чтобы избежать слишком быстрой анимации
        duration = max(duration, 20)
        
        # Планируем показ следующего кадра
        self.animation_timer = self.root.after(duration, lambda: self.animate_gif(next_frame))
    
    def scale_image(self, image):
        """Масштабирует изображение под размер окна"""
        # Получаем размеры окна и изображения
        window_width = self.image_frame.winfo_width()
        window_height = self.image_frame.winfo_height()
        image_width, image_height = image.size
        
        if window_width <= 1 or window_height <= 1:
            return image
            
        # Вычисляем новые размеры с сохранением пропорций
        scale_width = window_width / image_width
        scale_height = window_height / image_height
        scale = min(scale_width, scale_height)
        
        new_width = int(image_width * scale)
        new_height = int(image_height * scale)
        
        # Масштабируем изображение
        if new_width != image_width or new_height != image_height:
            return image.resize((new_width, new_height), Image.Resampling.LANCZOS)
        return image
    
    def show_next_image(self):
        self.show_image(self.current_index + 1)
        self.status_var.set("Skipped")
    
    def show_prev_image(self):
        self.show_image(self.current_index - 1)
    
    def move_to_folder(self, folder_index):
        """Перемещает текущее изображение в выбранную папку"""
        if not self.current_image or folder_index >= len(self.folders):
            return
            
        try:
            # Проверяем, что текущий файл не изменился
            if self.current_file != self.image_files[self.current_index]:
                return
                
            # Блокируем все кнопки папок
            for btn in self.folder_buttons.values():
                btn.configure(state='disabled')
            
            # Создаем папку, если её нет
            folder_name = self.folders[folder_index]
            folder_path = os.path.join(self.app_path, folder_name)
            if not os.path.exists(folder_path):
                os.makedirs(folder_path)
            
            src = self.image_files[self.current_index]
            
            # Проверяем, существует ли исходный файл
            if not os.path.exists(src):
                raise FileNotFoundError("Source file not found")
                
            dst = os.path.join(folder_path, os.path.basename(src))
            
            # Проверяем существование файла
            if os.path.exists(dst):
                base, ext = os.path.splitext(dst)
                counter = 1
                while os.path.exists(f"{base}_{counter}{ext}"):
                    counter += 1
                dst = f"{base}_{counter}{ext}"
            
            # Перемещаем файл
            shutil.move(src, dst)
            
            # Сохраняем информацию о перемещении для функции Undo
            self.move_history.append((src, dst))
            
            # Обновляем статус с информацией о последнем действии
            self.status_var.set(f"Moved to: {folder_name}")
            
            # Удаляем файл из списка и показываем следующий
            self.image_files.pop(self.current_index)
            if self.image_files:
                if self.current_index >= len(self.image_files):
                    self.current_index = 0
                self.show_image(self.current_index)
            else:
                self.current_image = None
                self.current_file = None
                self.image_label.configure(image='')
                self.status_var.set("All images processed")
            
            # Увеличиваем счетчик обработанных изображений
            self.processed_images += 1
            self.update_counter()
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to move file: {str(e)}")
            # Разблокируем кнопки в случае ошибки
            for btn in self.folder_buttons.values():
                btn.configure(state='normal')
    
    def format_file_size(self, bytes):
        """Форматирует размер файла в читаемый вид"""
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if bytes < 1024.0:
                return f"{bytes:.1f} {unit}"
            bytes /= 1024.0
        return f"{bytes:.1f} PB"
    
    def open_in_explorer(self):
        """Открывает текущий файл в проводнике Windows"""
        if not self.current_file or not os.path.exists(self.current_file):
            messagebox.showinfo("Information", "No current file to display")
            return
        
        try:
            # Используем explorer для открытия папки и выделения файла
            subprocess.run(['explorer', '/select,', os.path.normpath(self.current_file)])
        except Exception as e:
            messagebox.showerror("Error", f"Failed to open file in explorer: {str(e)}")
    
    def on_window_map(self, event):
        """Обработчик изменения состояния окна (максимизация/восстановление)"""
        # Используем after, чтобы дать окну время обновить свои размеры
        self.root.after(100, self.update_image_size)
    
    def on_fullscreen(self, event=None):
        """Обработчик переключения полноэкранного режима"""
        self.is_fullscreen = not self.is_fullscreen
        self.root.attributes('-fullscreen', self.is_fullscreen)
        # Используем after, чтобы дать окну время обновить свои размеры
        self.root.after(100, self.update_image_size)
    
    def undo_last_action(self):
        """Отменяет последнее действие"""
        if not self.move_history:
            return
        
        # Восстанавливаем последнее действие
        last_action = self.move_history.pop()
        src, dst = last_action
        
        # Проверяем, существует ли файл в текущем местоположении
        if not os.path.exists(dst):
            messagebox.showerror("Error", "File not found in destination")
            return
        
        # Проверяем, существует ли исходная папка
        src_dir = os.path.dirname(src)
        if not os.path.exists(src_dir):
            os.makedirs(src_dir)
        
        # Перемещаем файл обратно
        try:
            shutil.move(dst, src)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to undo action: {str(e)}")
            return
        
        # Обновляем статус
        self.status_var.set("Action undone")
        
        # Обновляем счетчик
        self.processed_images -= 1
        self.update_counter()
        
        # Добавляем файл обратно в список изображений
        self.image_files.append(src)
        # Сортируем список файлов, чтобы сохранить порядок
        self.image_files.sort()
        
        # Показываем возвращенное изображение
        new_index = self.image_files.index(src)
        self.show_image(new_index)

if __name__ == "__main__":
    root = tk.Tk()
    app = ImageSorter(root)
    root.mainloop()
