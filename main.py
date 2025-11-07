from tkinter import *
from tkinter import messagebox
import pyodbc
import time
import hashlib

def connect_db():
    try:
        conn = pyodbc.connect(
            "DRIVER={SQL Server};"
            "SERVER=408-05\\SQLEXPRESS;"
            "DATABASE=Hotel;"
            "Trusted_Connection=yes;"
        )
        return conn
    except Exception as e:
        print(f"Ошибка подключения: {e}")
        return None

def hash_password(password):
    """Хеширование пароля в SHA-256"""
    return hashlib.sha256(password.encode()).hexdigest()


def authenticate_user():
    username = entry_username.get()
    password = entry_password.get()
    
    if not username or not password:
        label_status.config(text="Введите логин и пароль")
        return
    
    conn = connect_db()
    if conn:
        try:
            cursor = conn.cursor()
            # Хешируем введенный пароль для сравнения с базой
            hashed_password = hash_password(password)
            
            # Сравниваем логин и хешированный пароль с базой данных
            cursor.execute("SELECT user_type FROM users WHERE username=? AND password=?", (username, hashed_password))
            result = cursor.fetchone()

            if result:
                user_type = result[0]
                label_status.config(text=f"Успешный вход! Роль: {user_type}")
                open_main_window(user_type, username)
            else:
                label_status.config(text="Неверный логин или пароль")
        except Exception as e:
            label_status.config(text=f"Ошибка: {e}")
        finally:
            conn.close()
    else:
        label_status.config(text="Нет подключения к БД")

def register_user():
    def submit_registration():
        new_username = entry_new_username.get()
        new_password = entry_new_password.get()
        
        if not new_username or not new_password:
            label_register_status.config(text="Заполните все поля")
            return
            
        conn = connect_db()
        if conn:
            try:
                cursor = conn.cursor()
                # Проверяем, есть ли уже такой пользователь
                cursor.execute("SELECT username FROM users WHERE username=?", (new_username,))
                if cursor.fetchone():
                    label_register_status.config(text="Пользователь уже существует")
                else:
                    # Создаем гостя
                    cursor.execute(
                        "INSERT INTO Guests (FirstName, LastName, Phone, Email) VALUES (?, ?, ?, ?)",
                        "Guest", new_username, "+7-000-000-00-00", f"{new_username}@hotel.com"
                    )
                    conn.commit()
                    
                    # Получаем ID созданного гостя
                    cursor.execute("SELECT @@IDENTITY")
                    person_id = cursor.fetchone()[0]
                    
                    # Хешируем пароль перед сохранением
                    hashed_password = hash_password(new_password)
                    
                    # Все новые пользователи становятся гостями (user)
                    cursor.execute(
                        "INSERT INTO users (username, password, user_type, person_id) VALUES (?, ?, 'user', ?)",
                        (new_username, hashed_password, person_id)
                    )
                    conn.commit()
                    label_register_status.config(text="Регистрация успешна! Вы стали гостем.")
                    
                    # Автоматически заполняем поля входа
                    entry_username.delete(0, END)
                    entry_password.delete(0, END)
                    entry_username.insert(0, new_username)
                    entry_password.insert(0, new_password)
                    
                    # Закрываем окно регистрации через 1 секунду
                    registration.after(1000, registration.destroy)
                    label_status.config(text="Теперь можете войти!")
                    
            except Exception as e:
                label_register_status.config(text=f"Ошибка: {e}")
            finally:
                conn.close()
        else:
            label_register_status.config(text="Нет подключения к БД")

    registration = Toplevel(root)
    registration.title("Регистрация")
    registration.configure(bg='lightblue')
    registration.geometry('400x300')
    registration.iconbitmap('user_identification_pass_id_personal_card_student_icon_266902.ico')

    Label(registration, text="Регистрация", font=('Arial', 20, 'bold'), fg='black', bg='lightblue').pack(pady=5)

    registration_frame = Frame(registration, bg='lightblue')
    registration_frame.pack(pady=10)


    Label(registration_frame, text="Новое имя пользователя:",bg='lightblue').grid(row=0, column=0, sticky=W, pady=1)
    entry_new_username = Entry(registration_frame, )
    entry_new_username.pack(pady=5)

    Label(registration_frame, text="Новый пароль:", bg='lightblue').grid(row=1, column=0, sticky=W, pady=1)
    entry_new_password = Entry(registration_frame, show='*',  width=50)
    entry_new_password.grid(row=1, column=1, pady=5, padx=5)

    registration_frame2 = Frame(registration_frame, bg='lightblue')

    Button(registration_frame2, text="Зарегистрироваться", command=submit_registration, bg='lightgreen').pack(pady=10)

    label_register_status = Label(registration, text="", bg='lightblue')
    label_register_status.pack(pady=5)
    

def open_main_window(user_type, username):
    """Открывает главное окно после успешного входа с учетом роли"""
    main_window = Toplevel(root)
    main_window.title(f"Главное окно - {username} ({user_type})")
    
    # Скрываем окно авторизации
    root.withdraw()
    
    def logout():
        main_window.destroy()
        root.deiconify()  # Показываем окно авторизации
        entry_password.delete(0, END)  # Очищаем пароль
        label_status.config(text="Вы вышли из системы")
    
    
    
    # Фрейм для кнопок
    button_frame = Frame(main_window)
    button_frame.pack(pady=20)
    
    # Базовые функции для всех гостей
    Button(button_frame, text="🏨 Просмотр всех комнат", width=25, height=2,
           command=view_all_rooms).pack(pady=5)
    
    Button(button_frame, text="📋 Мои бронирования", width=25, height=2,
           command=lambda: view_my_bookings(username)).pack(pady=5)
    
    # Кнопка выхода
    Button(main_window, text="Выйти", command=logout, bg='lightcoral', width=15).pack(pady=20)

# Функции для гостей
def view_all_rooms():
    """Просмотр всех комнат с возможностью бронирования"""
    rooms_window = Toplevel()
    rooms_window.title("Список всех комнат")
   
    
    # Заголовок
    Label(rooms_window, text="Список всех комнат", 
          font=('Arial', 16, 'bold'), fg='darkblue').pack(pady=10)
    
    # Фрейм для списка комнат
    list_frame = Frame(rooms_window)
    list_frame.pack(fill=BOTH, expand=True, padx=10, pady=10)
    
    # Заголовки таблицы
    headers = ["№", "Номер", "Тип", "Цена", "Статус", "Действие"]
    for i, header in enumerate(headers):
        Label(list_frame, text=header, font=('Arial', 10, 'bold'), 
              borderwidth=1, relief="solid", width=12).grid(row=0, column=i, sticky="ew")
    
    # Получаем список комнат из базы
    conn = connect_db()
    if conn:
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT RoomID, Room_number, RoomType, Price, RoomStatus FROM Rooms")
            rooms = cursor.fetchall()
            
            for idx, room in enumerate(rooms, 1):
                room_id, room_number, room_type, price, status = room
                
                # Отображаем информацию о комнате
                Label(list_frame, text=str(idx), borderwidth=1, relief="solid", width=12).grid(row=idx, column=0)
                Label(list_frame, text=room_number, borderwidth=1, relief="solid", width=12).grid(row=idx, column=1)
                Label(list_frame, text=room_type, borderwidth=1, relief="solid", width=12).grid(row=idx, column=2)
                Label(list_frame, text=str(price), borderwidth=1, relief="solid", width=12).grid(row=idx, column=3)
                
                # Статус с цветом
                status_color = 'green' if status == 'Свободна' else 'red'
                Label(list_frame, text=status, fg=status_color, borderwidth=1, 
                      relief="solid", width=12).grid(row=idx, column=4)
                
                # Кнопка действия
                if status == 'Свободна':
                    Button(list_frame, text="Забронировать", bg='lightgreen', width=12,
                           command=lambda rid=room_id, rnum=room_number: book_room(rid, rnum)).grid(row=idx, column=5)
                else:
                    Button(list_frame, text="Занята", bg='lightgray', width=12, state=DISABLED).grid(row=idx, column=5)
                    
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось загрузить список комнат: {e}")
        finally:
            conn.close()
    else:
        messagebox.showerror("Ошибка", "Нет подключения к базе данных")
    
    # Кнопка "Назад"
    Button(rooms_window, text="Назад", command=rooms_window.destroy, 
           bg='lightcoral', width=15).pack(pady=10)

def book_room(room_id, room_number):
    """Бронирование комнаты - упрощенная версия без BookingDate"""
    # Спросим даты заезда и выезда
    booking_window = Toplevel()
    booking_window.title(f"Бронирование комнаты №{room_number}")
   
    
    Label(booking_window, text=f"Комната №{room_number}", font=('Arial', 12, 'bold')).pack(pady=10)
    
    Label(booking_window, text="Дата заезда (ГГГГ-ММ-ДД):").pack()
    entry_checkin = Entry(booking_window)
    entry_checkin.insert(0, "2024-01-15")  # Пример даты
    entry_checkin.pack(pady=5)
    
    Label(booking_window, text="Дата выезда (ГГГГ-ММ-ДД):").pack()
    entry_checkout = Entry(booking_window)
    entry_checkout.insert(0, "2024-01-20")  # Пример даты
    entry_checkout.pack(pady=5)
    
    def confirm_booking():
        checkin = entry_checkin.get()
        checkout = entry_checkout.get()
        
        if not checkin or not checkout:
            messagebox.showerror("Ошибка", "Заполните даты заезда и выезда")
            return
        
        conn = connect_db()
        if conn:
            try:
                cursor = conn.cursor()
                
                # Получаем ID текущего пользователя
                cursor.execute("SELECT person_id FROM users WHERE username = ?", entry_username.get())
                guest_result = cursor.fetchone()
                
                if guest_result:
                    guest_id = guest_result[0]
                    
                    # Упрощенный запрос без BookingDate
                    cursor.execute("""
                        INSERT INTO Bookings (GuestID, RoomID, CheckInDate, CheckOutDate)
                        VALUES (?, ?, ?, ?)
                    """, guest_id, room_id, checkin, checkout)
                    
                    # Обновляем статус комнаты на "Занята" в таблице Rooms
                    cursor.execute("UPDATE Rooms SET RoomStatus = 'Занята' WHERE RoomID = ?", room_id)
                    
                    conn.commit()
                    
                    messagebox.showinfo("Успех", f"Комната №{room_number} успешно забронирована!")
                    booking_window.destroy()
                    
                    # Закрываем окно списка комнат
                    for window in root.winfo_children():
                        if isinstance(window, Toplevel) and "Список всех комнат" in window.title():
                            window.destroy()
                            break
                    # Обновляем список комнат
                    view_all_rooms()
                else:
                    messagebox.showerror("Ошибка", "Не удалось определить пользователя")
                    
            except Exception as e:
                messagebox.showerror("Ошибка", f"Не удалось забронировать комнату: {e}")
                print(f"Ошибка детально: {e}")
            finally:
                conn.close()
    
    # Фрейм для кнопок
    button_frame = Frame(booking_window)
    button_frame.pack(pady=15)
    
    Button(button_frame, text="Подтвердить бронирование", command=confirm_booking, 
           bg='lightgreen', width=20).pack(pady=5)
    
    Button(button_frame, text="Назад", command=booking_window.destroy, 
           bg='lightcoral', width=20).pack(pady=5)

def view_my_bookings(username):
    """Просмотр бронирований текущего пользователя"""
    bookings_window = Toplevel()
    bookings_window.title("Мои бронирования")
    
    
    # Заголовок
    Label(bookings_window, text="Мои бронирования", 
          font=('Arial', 16, 'bold'), fg='darkblue').pack(pady=10)
    
    # Получаем person_id пользователя
    conn = connect_db()
    if conn:
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT person_id FROM users WHERE username = ?", username)
            user_result = cursor.fetchone()
            
            if user_result:
                person_id = user_result[0]
                
                # Получаем бронирования пользователя через GuestID (который равен person_id)
                cursor.execute("""
                    SELECT b.BookingID, r.Room_number, r.RoomType, r.Price, 
                           b.CheckInDate, b.CheckOutDate, r.RoomStatus
                    FROM Bookings b 
                    JOIN Rooms r ON b.RoomID = r.RoomID 
                    WHERE b.GuestID = ?
                """, person_id)
                
                bookings = cursor.fetchall()
                
                if bookings:
                    # Фрейм для таблицы
                    table_frame = Frame(bookings_window)
                    table_frame.pack(fill=BOTH, expand=True, padx=10, pady=10)
                    
                    # Заголовки таблицы
                    headers = ["№", "Комната", "Тип", "Цена", "Заезд", "Выезд", "Статус комнаты", "Действие"]
                    for i, header in enumerate(headers):
                        Label(table_frame, text=header, font=('Arial', 10, 'bold'), 
                              borderwidth=1, relief="solid", width=12, wraplength=80).grid(row=0, column=i, sticky="ew", padx=1, pady=1)
                    
                    # Отображаем бронирования
                    for idx, booking in enumerate(bookings, 1):
                        booking_id, room_number, room_type, price, checkin, checkout, room_status = booking
                        
                        # Определяем цвет статуса комнаты
                        status_color = 'red' if room_status == 'Занята' else 'green' if room_status == 'Свободна' else 'orange'
                        
                        Label(table_frame, text=str(idx), borderwidth=1, relief="solid", width=12).grid(
                            row=idx, column=0, sticky="ew", padx=1, pady=1)
                        Label(table_frame, text=room_number, borderwidth=1, relief="solid", width=12).grid(
                            row=idx, column=1, sticky="ew", padx=1, pady=1)
                        Label(table_frame, text=room_type, borderwidth=1, relief="solid", width=12).grid(
                            row=idx, column=2, sticky="ew", padx=1, pady=1)
                        Label(table_frame, text=str(price), borderwidth=1, relief="solid", width=12).grid(
                            row=idx, column=3, sticky="ew", padx=1, pady=1)
                        Label(table_frame, text=str(checkin), borderwidth=1, relief="solid", width=12).grid(
                            row=idx, column=4, sticky="ew", padx=1, pady=1)
                        Label(table_frame, text=str(checkout), borderwidth=1, relief="solid", width=12).grid(
                            row=idx, column=5, sticky="ew", padx=1, pady=1)
                        Label(table_frame, text=room_status, fg=status_color, borderwidth=1, 
                              relief="solid", width=12).grid(row=idx, column=6, sticky="ew", padx=1, pady=1)
                        
                        # Кнопка отмены (только если комната занята - т.е. бронирование активно)
                        if room_status == 'Занята':
                            Button(table_frame, text="Отменить", bg='lightcoral', width=10,
                                   command=lambda bid=booking_id, rnum=room_number: cancel_booking(bid, rnum)).grid(
                                   row=idx, column=7, padx=2, pady=2)
                        else:
                            Button(table_frame, text="Неактивно", bg='lightgray', width=10, state=DISABLED).grid(
                                   row=idx, column=7, padx=2, pady=2)
                else:
                    # Если бронирований нет
                    Label(bookings_window, text="У вас нет активных бронирований", 
                          font=('Arial', 12), fg='gray').pack(expand=True, pady=50)
                    Label(bookings_window, text="Забронируйте комнату в разделе 'Просмотр всех комнат'", 
                          font=('Arial', 10), fg='darkgray').pack()
                    
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось загрузить бронирования: {e}")
            print(f"Ошибка детально: {e}")  # Для отладки
        finally:
            conn.close()
    else:
        messagebox.showerror("Ошибка", "Нет подключения к базе данных")
    
    # Кнопка "Назад"
    Button(bookings_window, text="Назад", command=bookings_window.destroy, 
           bg='lightcoral', width=15).pack(pady=10)

def cancel_booking(booking_id, room_number):
    """Отмена бронирования с учетом связанных платежей"""
    if messagebox.askyesno("Подтверждение", f"Вы уверены, что хотите отменить бронирование комнаты №{room_number}?"):
        conn = connect_db()
        if conn:
            try:
                cursor = conn.cursor()
                
                # Получаем RoomID из бронирования
                cursor.execute("SELECT RoomID FROM Bookings WHERE BookingID = ?", booking_id)
                room_result = cursor.fetchone()
                
                if room_result:
                    room_id = room_result[0]
                    
                    # Сначала удаляем связанные платежи
                    try:
                        cursor.execute("DELETE FROM Payments WHERE BookingID = ?", booking_id)
                        print(f"Удалены платежи для бронирования {booking_id}")
                    except Exception as e:
                        print(f"Платежи не найдены или не могут быть удалены: {e}")
                    
                    # Затем удаляем бронирование
                    cursor.execute("DELETE FROM Bookings WHERE BookingID = ?", booking_id)
                    
                    # Обновляем статус комнаты на "Свободна" в таблице Rooms
                    cursor.execute("UPDATE Rooms SET RoomStatus = 'Свободна' WHERE RoomID = ?", room_id)
                    
                    conn.commit()
                    
                    messagebox.showinfo("Успех", f"Бронирование комнаты №{room_number} отменено!")
                    
                    # Закрываем окно бронирований
                    for window in root.winfo_children():
                        if isinstance(window, Toplevel) and "Мои бронирования" in window.title():
                            window.destroy()
                            break
                    
            except Exception as e:
                messagebox.showerror("Ошибка", f"Не удалось отменить бронирование: {e}")
                print(f"Детальная ошибка: {e}")
            finally:
                conn.close()




root = Tk()
root.title("Авторизация")
root.configure(bg='lightblue')
root.geometry('400x300')
root.iconbitmap('graduate_boy_avatar_school_student_icon_266880.ico')


Label(root, text="Вход в аккаунт", font=('Arial', 20, 'bold'), fg='black', bg='lightblue').pack(pady=5)



input_frame = Frame(root, bg='lightblue')
input_frame.pack(pady=10)

Label(input_frame, text="Логин:", bg='lightblue').grid(row=0, column=0, sticky=W, pady=5)
entry_username = Entry(input_frame, width=50)
entry_username.grid(row=0, column=1, pady=5, padx=5)

Label(input_frame, text="Пароль:",bg='lightblue').grid(row=1, column=0, sticky=W, pady=5)
entry_password = Entry(input_frame, show='*', width=50)
entry_password.grid(row=1, column=1, pady=5, padx=5)


button_frame = Frame(root, bg='lightblue')
button_frame.pack(pady=15)

Button(button_frame, text="Войти", command=authenticate_user, 
       bg='lightgrey', width=25, height=2).grid(row=0, column=0, padx=5)
Button(button_frame, text="Регистрация", command=register_user, 
       bg='lightgreen', width=25, height=2).grid(row=0, column=1, padx=5)


label_status = Label(root, text="Введите данные для входа", fg='black', bg='lightblue')
label_status.pack(pady=10)

# Запуск
root.mainloop()