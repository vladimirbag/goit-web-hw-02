import pickle
from collections import UserDict
from datetime import datetime, timedelta
from abc import ABC, abstractmethod


# Класи для роботи з контактами
class Field:
    def __init__(self, value):
        self.value = value

    def __str__(self):
        return str(self.value)


class Name(Field):
    pass


class Phone(Field):
    def __init__(self, number):
        self.value = self.validate_number(number)

    def validate_number(self, number):
        if len(number) == 10 and number.isdigit():
            return number
        raise ValueError("Phone number must contain exactly 10 digits")


class Birthday(Field):
    def __init__(self, value):
        self.value = self.validate_birthday(value)

    def validate_birthday(self, value):
        try:
            # Перевіряємо формат і коректність дати
            datetime.strptime(value, "%d.%m.%Y")
            return value  # Зберігаємо рядок, якщо дата валідна
        except ValueError:
            raise ValueError("Invalid date format. Use DD.MM.YYYY")


class Record:
    def __init__(self, name):
        self.name = Name(name)
        self.phones = []
        self.birthday = None

    def add_phone(self, phone_number):
        self.phones.append(Phone(phone_number))

    def remove_phone(self, phone_number):
        for phone in self.phones:
            if phone.value == phone_number:
                self.phones.remove(phone)
                return
        raise ValueError("Phone number not found")

    def edit_phone(self, old_number, new_number):
        for phone in self.phones:
            if phone.value == old_number:
                phone.value = Phone(new_number).value
                return
        raise ValueError("Old phone number not found")

    def add_birthday(self, birthday):
        self.birthday = Birthday(birthday)

    def show_birthday(self):
        return self.birthday.value if self.birthday else "No birthday set"

    def __str__(self):
        phones = "; ".join(p.value for p in self.phones)
        birthday = f", birthday: {self.show_birthday()}" if self.birthday else ""
        return f"Contact name: {self.name.value}, phones: {phones}{birthday}"


class AddressBook(UserDict):
    def add_record(self, record):
        self.data[record.name.value] = record

    def find(self, name):
        return self.data.get(name, None)

    def delete(self, name):
        if name in self.data:
            del self.data[name]

    def get_upcoming_birthdays(self):
        today = datetime.now().date()
        next_week = today + timedelta(days=7)
        results = []

        for record in self.data.values():
            if record.birthday:
                birthday_date = datetime.strptime(record.birthday.value, "%d.%m.%Y").date()
                next_birthday = birthday_date.replace(year=today.year)

                if next_birthday < today:
                    next_birthday = next_birthday.replace(year=today.year + 1)

                if today <= next_birthday <= next_week:
                    if next_birthday.weekday() >= 5:  # 5 = субота, 6 = неділя
                        next_birthday += timedelta(days=(7 - next_birthday.weekday()))

                    results.append({
                        "name": record.name.value,
                        "birthday": next_birthday.strftime("%d.%m.%Y")
                    })

        return results

    def __str__(self):
        contacts = "\n".join(str(record) for record in self.data.values())
        return f"AddressBook:\n{contacts}"

    # Збереження даних у файл
    def save_to_file(self, filename="address_book.pkl"):
        with open(filename, "wb") as file:
            pickle.dump(self.data, file)

    # Завантаження даних із файлу
    def load_from_file(self, filename="address_book.pkl"):
        try:
            with open(filename, "rb") as file:
                self.data = pickle.load(file)
        except FileNotFoundError:
            pass  # Якщо файл не знайдено то починаємо з порожньої адресної книги


# Абстрактний клас для користувацьких уявлень
class View(ABC):
    @abstractmethod
    def show_contact(self, record):
        pass

    @abstractmethod
    def show_all_contacts(self, contacts):
        pass

    @abstractmethod
    def show_command_list(self, commands):
        pass

    @abstractmethod
    def show_message(self, message):
        pass


# Реалізація консольного інтерфейсу
class ConsoleView(View):
    def show_contact(self, record):
        print(f"Contact name: {record.name.value}, phones: {', '.join([phone.value for phone in record.phones])}")
        if record.birthday:
            print(f"Birthday: {record.show_birthday()}")

    def show_all_contacts(self, contacts):
        if not contacts:
            print("No contacts found.")
        else:
            for record in contacts:
                self.show_contact(record)

    def show_command_list(self, commands):
        print("Available commands:")
        for command, description in commands.items():
            print(f"{command}: {description}")

    def show_message(self, message):
        print(message)


# Обробники помилок
def input_error(func):
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except KeyError:
            return "This user does not exist. Enter a valid user name."
        except ValueError as e:
            return str(e)
        except IndexError:
            return "Not enough information provided. Try again."
        except Exception as e:
            return f"An unexpected error occurred: {e}"
    return wrapper


# Команди для взаємодії
@input_error
def add_contact(args, book):
    name, phone = args
    record = book.find(name)
    if record:
        record.add_phone(phone)
    else:
        record = Record(name)
        record.add_phone(phone)
        book.add_record(record)
    return f"Contact {name} added or updated."


@input_error
def change_contact(args, book):
    name, old_phone, new_phone = args
    record = book.find(name)
    if record:
        record.edit_phone(old_phone, new_phone)
        return f"Phone for {name} changed."
    return "Contact not found."


@input_error
def show_phone(args, book):
    name = args[0]
    record = book.find(name)
    if record:
        return str(record)
    return "Contact not found."


def show_all(book):
    return str(book) if book.data else "No contacts found."


@input_error
def add_birthday(args, book):
    name, birthday = args
    record = book.find(name)
    if record:
        record.add_birthday(birthday)
        return f"Birthday added for {name}."
    return "Contact not found."


@input_error
def show_birthday(args, book):
    name = args[0]
    record = book.find(name)
    if record:
        return f"{name}'s birthday is {record.show_birthday()}."
    return "Contact not found."


def upcoming_birthdays(book):
    birthdays = book.get_upcoming_birthdays()
    if not birthdays:
        return "No birthdays in the next 7 days."
    return "\n".join(f"{b['name']} - {b['birthday']}" for b in birthdays)


# Парсер вводу
def parse_input(user_input):
    cmd, *args = user_input.split()
    return cmd.strip().lower(), args


# Головна функція
def main():
    book = AddressBook()
    book.load_from_file()  # Завантажуємо дані з файлу при старті програми
    view = ConsoleView()

    commands = {
        "hello": "Greet the bot",
        "add": "Add a new contact",
        "change": "Change a contact's phone number",
        "phone": "Show contact's phone number",
        "all": "Show all contacts",
        "add-birthday": "Add a birthday to a contact",
        "show-birthday": "Show a contact's birthday",
        "birthdays": "Show upcoming birthdays",
        "exit": "Exit the program"
    }

    print("Welcome to the assistant bot!")
    while True:
        user_input = input("Enter a command: ")
        command, args = parse_input(user_input)

        if command in ["close", "exit"]:
            book.save_to_file()  # Зберігаємо дані у файл при виході
            view.show_message("Good bye!")
            break
        elif command == "hello":
            view.show_message("How can I help you?")
        elif command == "add":
            message = add_contact(args, book)
            view.show_message(message)
        elif command == "change":
            message = change_contact(args, book)
            view.show_message(message)
        elif command == "phone":
            message = show_phone(args, book)
            view.show_message(message)
        elif command == "all":
            view.show_all_contacts(book.data.values())
        elif command == "add-birthday":
            message = add_birthday(args, book)
            view.show_message(message)
        elif command == "show-birthday":
            message = show_birthday(args, book)
            view.show_message(message)
        elif command == "birthdays":
            message = upcoming_birthdays(book)
            view.show_message(message)
        else:
            view.show_message("Invalid command.")


if __name__ == "__main__":
    main()
