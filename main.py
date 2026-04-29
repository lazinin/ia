import json
import os
import copy
from enum import Enum
from collections import deque

class TaskPriority(Enum):
    LOW = "Низкий"
    MEDIUM = "Средний"
    HIGH = "Высокий"

class TaskStatus(Enum):
    TO_DO = "К выполнению"
    IN_PROGRESS = "В процессе"
    DONE = "Выполнено"

class Task:
    def __init__(self, task_id, title, description, priority, status):
        self._id = task_id
        self.title = title
        self.description = description
        self.priority = priority
        self.status = status

    @property
    def id(self): return self._id

    @property
    def title(self): return self._title
    
    @title.setter
    def title(self, value):
        if not value or not value.strip(): raise ValueError("Название не может быть пустым.")
        self._title = value.strip()

    @property
    def description(self): return self._description
    
    @description.setter
    def description(self, value):
        self._description = value.strip() if value else ""

    @property
    def priority(self): return self._priority
    
    @priority.setter
    def priority(self, value):
        if not isinstance(value, TaskPriority): raise ValueError("Неверный приоритет.")
        self._priority = value

    @property
    def status(self): return self._status
    
    @status.setter
    def status(self, value):
        if not isinstance(value, TaskStatus): raise ValueError("Неверный статус.")
        self._status = value

    def to_dict(self):
        return {
            "type": "Task",
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "priority": self.priority.value,
            "status": self.status.value
        }

    def __str__(self):
        return f"[{self.id}] {self.title} | Приоритет: {self.priority.value} | Статус: {self.status.value}"

class UrgentTask(Task):
    def __init__(self, task_id, title, description, status, deadline):
        super().__init__(task_id, title, description, TaskPriority.HIGH, status)
        self.deadline = deadline

    @property
    def deadline(self): return self._deadline
    
    @deadline.setter
    def deadline(self, value):
        if not value or not value.strip(): raise ValueError("Срок не может быть пустым.")
        self._deadline = value.strip()

    def to_dict(self):
        data = super().to_dict()
        data["type"] = "UrgentTask"
        data["deadline"] = self.deadline
        return data

    def __str__(self):
        return f"СРОЧНО: [{self.id}] {self.title} (До: {self.deadline}) | Статус: {self.status.value}"

class TaskManager:
    def __init__(self, filepath="tasks.json"):
        self.filepath = filepath
        self.tasks = []
        self.undo_stack = []
        self.load_data()

    def _save_state(self):
        self.undo_stack.append(copy.deepcopy(self.tasks))

    def undo(self):
        if not self.undo_stack:
            return False
        self.tasks = self.undo_stack.pop()
        self._save_to_file()
        return True

    def add_task(self, task):
        self._save_state()
        self.tasks.append(task)
        self._save_to_file()

    def update_task(self, task_id, title=None, desc=None, priority=None, status=None):
        task = self.get_task(task_id)
        if task:
            self._save_state()
            if title: task.title = title
            if desc is not None: task.description = desc
            if priority: task.priority = priority
            if status: task.status = status
            self._save_to_file()
            return True
        return False

    def delete_task(self, task_id):
        initial_count = len(self.tasks)
        self._save_state()
        self.tasks = [t for t in self.tasks if t.id != task_id]
        if len(self.tasks) < initial_count:
            self._save_to_file()
            return True
        self.undo_stack.pop()
        return False

    def get_task(self, task_id):
        return next((t for t in self.tasks if t.id == task_id), None)

    def filter_by_status(self, status):
        return [t for t in self.tasks if t.status == status]

    def filter_by_priority(self, priority):
        return [t for t in self.tasks if t.priority == priority]

    def get_priority_queue(self):
        order = {TaskPriority.HIGH: 3, TaskPriority.MEDIUM: 2, TaskPriority.LOW: 1}
        sorted_tasks = sorted(self.tasks, key=lambda t: order[t.priority], reverse=True)
        return deque(sorted_tasks)

    def _save_to_file(self):
        with open(self.filepath, 'w', encoding='utf-8') as f:
            json.dump([t.to_dict() for t in self.tasks], f, ensure_ascii=False, indent=4)

    def load_data(self):
        if not os.path.exists(self.filepath): return
        try:
            with open(self.filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
                self.tasks = []
                for item in data:
                    status = TaskStatus(item["status"])
                    if item.get("type") == "UrgentTask":
                        task = UrgentTask(item["id"], item["title"], item["description"], status, item["deadline"])
                    else:
                        priority = TaskPriority(item["priority"])
                        task = Task(item["id"], item["title"], item["description"], priority, status)
                    self.tasks.append(task)
        except (json.JSONDecodeError, ValueError) as e:
            print(f"Ошибка загрузки JSON: {e}")
            self.tasks = []

    def get_next_id(self):
        return max([t.id for t in self.tasks], default=0) + 1

class ConsoleView:
    @staticmethod
    def display_menu():
        print("\n=== МЕНЕДЖЕР ЗАДАЧ ===")
        print("1. Просмотреть все задачи")
        print("2. Добавить задачу")
        print("3. Добавить СРОЧНУЮ задачу")
        print("4. Редактировать задачу")
        print("5. Удалить задачу")
        print("6. Фильтровать задачи")
        print("7. Просмотреть очередь по приоритету")
        print("8. Отменить последнее действие")
        print("0. Выход")
        return input("Выберите опцию: ")

    @staticmethod
    def display_tasks(tasks, title="Задачи"):
        print(f"\n--- {title} ---")
        if not tasks: print("Задачи не найдены.")
        for task in tasks: print(task)

    @staticmethod
    def get_string(prompt, required=True):
        while True:
            val = input(prompt).strip()
            if required and not val:
                print("Ошибка: Это поле не может быть пустым.")
            else: return val

    @staticmethod
    def get_enum(enum_class, prompt):
        options = [e.value for e in enum_class]
        while True:
            print(f"{prompt} ({', '.join(options)}): ", end="")
            val = input().strip()
            try:
                return enum_class(val)
            except ValueError:
                print("Ошибка: Неверный выбор. Пожалуйста, введите точно так, как показано.")

    @staticmethod
    def get_int(prompt):
        while True:
            try: return int(input(prompt).strip())
            except ValueError: print("Ошибка: Пожалуйста, введите корректное целое число.")

    @staticmethod
    def show_message(msg):
        print(f"> {msg}")

class MenuController:
    def __init__(self):
        self.model = TaskManager()
        self.view = ConsoleView()

    def run(self):
        while True:
            choice = self.view.display_menu()
            if choice == '1': self.view.display_tasks(self.model.tasks, "Все задачи")
            elif choice == '2': self._add_task(urgent=False)
            elif choice == '3': self._add_task(urgent=True)
            elif choice == '4': self._edit_task()
            elif choice == '5': self._delete_task()
            elif choice == '6': self._filter_tasks()
            elif choice == '7': self._process_queue()
            elif choice == '8': self._undo()
            elif choice == '0':
                self.view.show_message("Выход...")
                break
            else: self.view.show_message("Неверная опция.")

    def _add_task(self, urgent):
        title = self.view.get_string("Название: ", required=True)
        desc = self.view.get_string("Описание (необязательно): ", required=False)
        status = self.view.get_enum(TaskStatus, "Статус")
        task_id = self.model.get_next_id()

        if urgent:
            deadline = self.view.get_string("Срок: ", required=True)
            task = UrgentTask(task_id, title, desc, status, deadline)
        else:
            priority = self.view.get_enum(TaskPriority, "Приоритет")
            task = Task(task_id, title, desc, priority, status)

        self.model.add_task(task)
        self.view.show_message("Задача успешно добавлена.")

    def _edit_task(self):
        task_id = self.view.get_int("Введите ID задачи для редактирования: ")
        task = self.model.get_task(task_id)
        if not task:
            self.view.show_message("Задача не найдена.")
            return

        self.view.show_message(f"Редактирование задачи: {task.title} (Оставьте пустым, чтобы не менять)")
        title = self.view.get_string(f"Новое название [{task.title}]: ", required=False) or task.title
        desc = self.view.get_string(f"Новое описание [{task.description}]: ", required=False) or task.description

        print("Изменить статус? (д/н): ", end="")
        status = self.view.get_enum(TaskStatus, "Новый статус") if input().strip().lower() == 'д' else task.status

        priority = task.priority
        if not isinstance(task, UrgentTask):
            print("Изменить приоритет? (д/н): ", end="")
            if input().strip().lower() == 'д':
                priority = self.view.get_enum(TaskPriority, "Новый приоритет")

        self.model.update_task(task_id, title, desc, priority, status)
        self.view.show_message("Задача обновлена.")

    def _delete_task(self):
        task_id = self.view.get_int("Введите ID задачи для удаления: ")
        if self.model.delete_task(task_id):
            self.view.show_message("Задача удалена.")
        else:
            self.view.show_message("Задача не найдена.")

    def _filter_tasks(self):
        print("1. По статусу\n2. По приоритету")
        choice = input("Выбор: ").strip()
        if choice == '1':
            status = self.view.get_enum(TaskStatus, "Выберите статус")
            self.view.display_tasks(self.model.filter_by_status(status), f"Отфильтровано по: {status.value}")
        elif choice == '2':
            priority = self.view.get_enum(TaskPriority, "Выберите приоритет")
            self.view.display_tasks(self.model.filter_by_priority(priority), f"Отфильтровано по: {priority.value}")
        else:
            self.view.show_message("Неверный выбор.")

    def _process_queue(self):
        queue = self.model.get_priority_queue()
        self.view.display_tasks(queue, "Очередь приоритетов (Высокий -> Низкий)")
        if queue:
            self.view.show_message(f"Следующая задача с наивысшим приоритетом: {queue[0].title}")

    def _undo(self):
        if self.model.undo(): self.view.show_message("Последнее действие отменено.")
        else: self.view.show_message("Нет действий для отмены.")

if __name__ == "__main__":
    app = MenuController()
    app.run()