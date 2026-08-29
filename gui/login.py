"""
Login window — shown before the main app.
On very first run (no users exist yet), it lets you create the
initial Admin account instead of showing a plain login form.
"""

import customtkinter as ctk
from tkinter import messagebox

from services.database import Database
from services.auth import AuthManager, AuthError

ctk.set_appearance_mode("System")
ctk.set_default_color_theme("blue")


class LoginWindow(ctk.CTk):
    def __init__(self, on_success):
        """on_success(role: str, db: Database) is called after a valid login."""
        super().__init__()
        self.on_success = on_success

        self.title("Student Management System — Login")
        self.geometry("380x420")
        self.resizable(False, False)

        self.db = Database()
        self.auth = AuthManager(self.db)

        self.first_run = not self.auth.has_any_user()
        self._build_ui()

    def _build_ui(self):
        title = "Create Admin Account" if self.first_run else "Login"
        ctk.CTkLabel(self, text=title, font=ctk.CTkFont(size=20, weight="bold")).pack(pady=(30, 15))

        if self.first_run:
            ctk.CTkLabel(
                self, text="No accounts exist yet.\nSet up the first Admin account.",
                text_color="gray", justify="center"
            ).pack(pady=(0, 15))

        self.username_entry = ctk.CTkEntry(self, width=260, placeholder_text="Username")
        self.username_entry.pack(pady=8)

        self.password_entry = ctk.CTkEntry(self, width=260, placeholder_text="Password", show="*")
        self.password_entry.pack(pady=8)

        if self.first_run:
            self.role_menu = None  # first account is always Admin
            ctk.CTkButton(self, text="Create Admin Account", width=260,
                           command=self._create_admin).pack(pady=20)
        else:
            ctk.CTkButton(self, text="Login", width=260, command=self._login).pack(pady=20)
            ctk.CTkButton(self, text="Register New Account", width=260,
                           fg_color="transparent", border_width=1,
                           command=self._show_register).pack()

        self.password_entry.bind("<Return>", lambda e: self._login() if not self.first_run else self._create_admin())

    def _create_admin(self):
        username = self.username_entry.get().strip()
        password = self.password_entry.get()
        try:
            self.auth.register(username, password, "Admin")
            messagebox.showinfo("Success", "Admin account created. Please log in.")
            self.first_run = False
            for widget in self.winfo_children():
                widget.destroy()
            self._build_ui()
        except AuthError as e:
            messagebox.showerror("Error", str(e))

    def _login(self):
        username = self.username_entry.get().strip()
        password = self.password_entry.get()
        try:
            role = self.auth.login(username, password)
            self.db.close()
            self.destroy()
            self.on_success(role, username)
        except AuthError as e:
            messagebox.showerror("Login Failed", str(e))

    def _show_register(self):
        RegisterDialog(self, self.auth)


class RegisterDialog(ctk.CTkToplevel):
    def __init__(self, parent, auth: AuthManager):
        super().__init__(parent)
        self.auth = auth
        self.title("Register")
        self.geometry("300x320")
        self.grab_set()

        ctk.CTkLabel(self, text="New Account", font=ctk.CTkFont(size=16, weight="bold")).pack(pady=15)

        self.username_entry = ctk.CTkEntry(self, width=220, placeholder_text="Username")
        self.username_entry.pack(pady=8)

        self.password_entry = ctk.CTkEntry(self, width=220, placeholder_text="Password", show="*")
        self.password_entry.pack(pady=8)

        self.role_menu = ctk.CTkOptionMenu(self, values=["Teacher", "Student"])
        self.role_menu.pack(pady=8)

        ctk.CTkButton(self, text="Register", width=220, command=self._register).pack(pady=15)

    def _register(self):
        try:
            self.auth.register(
                self.username_entry.get().strip(),
                self.password_entry.get(),
                self.role_menu.get(),
            )
            messagebox.showinfo("Success", "Account created. You can now log in.")
            self.destroy()
        except AuthError as e:
            messagebox.showerror("Error", str(e))
