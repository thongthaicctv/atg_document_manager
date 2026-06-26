from __future__ import annotations

import argparse
import getpass
import hashlib
import json
import os
import sys
import uuid
from datetime import date
from pathlib import Path

from app.services.license_service import (
    APP_LICENSE_CODE,
    build_license_token,
    get_machine_code,
    install_license_key,
    rsa_sign_payload,
)

DEFAULT_PRIVATE_KEY_PATH = Path("D:/ATG_DOCUMENT/license/atg_license_private.json")
TOOL_PASSWORD_HASH = "f7f249d5ad63f9b3e5d8c97977044528ed18010ca18a5e35ed190c06f71121cf"


def _configure_console_encoding() -> None:
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")
        except (AttributeError, ValueError):
            pass


def _is_password_valid(password: str) -> bool:
    password_hash = hashlib.sha256(password.encode("utf-8")).hexdigest()
    return password_hash == TOOL_PASSWORD_HASH


def _require_cli_password() -> None:
    password = os.environ.get("ATG_LICENSE_TOOL_PASSWORD")
    if password is None:
        password = getpass.getpass("Nhập mật khẩu mở license_tool: ")
    if not _is_password_valid(password):
        raise SystemExit("Sai mật khẩu mở license_tool.")


def _load_private_key(path: Path) -> dict:
    if not path.exists():
        raise ValueError(
            f"Không tìm thấy private key: {path}\n"
            "Private key chỉ nên lưu trên máy quản trị phát hành license, không copy sang máy người dùng."
        )
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"Private key không phải JSON hợp lệ: {exc}") from exc
    required = {"n", "e", "d"}
    if not required.issubset(data):
        raise ValueError("Private key thiếu n/e/d.")
    return data


def create_license_token(machine_code: str, customer: str, expires: str, private_key_path: str | Path) -> str:
    machine_code = machine_code.strip().upper()
    customer = customer.strip()
    expires = expires.strip()
    if not machine_code:
        raise ValueError("Chưa có mã máy.")
    if not customer:
        raise ValueError("Chưa nhập tên đơn vị/khách hàng.")
    if expires:
        try:
            date.fromisoformat(expires)
        except ValueError as exc:
            raise ValueError("Ngày hết hạn phải có dạng YYYY-MM-DD, ví dụ 2036-12-31.") from exc

    private_key = _load_private_key(Path(private_key_path))
    payload = {
        "app": APP_LICENSE_CODE,
        "license_id": str(uuid.uuid4()),
        "machine_code": machine_code,
        "customer": customer,
        "issued_at": date.today().isoformat(),
        "expires_at": expires,
    }
    signature = rsa_sign_payload(payload, private_key)
    return build_license_token(payload, signature)


def install_license(raw_license: str) -> str:
    raw_license = raw_license.strip()
    if not raw_license:
        raise ValueError("Chưa có mã kích hoạt/license để cài.")
    status = install_license_key(raw_license)
    return f"{status.message}\nMã máy: {status.machine_code}\nFile license: {status.license_file}"


def _issue(args: argparse.Namespace) -> None:
    token = create_license_token(
        machine_code=args.machine_code,
        customer=args.customer,
        expires=args.expires or "",
        private_key_path=args.private_key,
    )
    if args.output:
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(token + "\n", encoding="utf-8")
        print(f"Đã tạo license: {output_path}")
    else:
        print(token)


def _install(args: argparse.Namespace) -> None:
    if args.file:
        raw_license = Path(args.file).read_text(encoding="utf-8")
    else:
        raw_license = args.license_key
    print(install_license(raw_license))


def _start_gui_app() -> None:
    import tkinter as tk
    from tkinter import filedialog, messagebox, simpledialog, ttk

    root = tk.Tk()
    root.withdraw()

    env_password = os.environ.get("ATG_LICENSE_TOOL_PASSWORD")
    password = env_password
    if password is None:
        password = simpledialog.askstring("Mở ATG License Tool", "Nhập mật khẩu mở license_tool:", show="*", parent=root)
    if not password:
        root.destroy()
        return
    if not _is_password_valid(password):
        messagebox.showerror("Sai mật khẩu", "Sai mật khẩu mở license_tool.", parent=root)
        root.destroy()
        return

    root.title("ATG License Tool")
    root.geometry("980x720")
    root.minsize(860, 620)

    style = ttk.Style(root)
    try:
        style.theme_use("clam")
    except tk.TclError:
        pass
    style.configure("Title.TLabel", font=("Segoe UI", 16, "bold"))
    style.configure("Section.TLabelframe.Label", font=("Segoe UI", 10, "bold"))

    machine_code_var = tk.StringVar(value=get_machine_code())
    customer_var = tk.StringVar(value="")
    expires_var = tk.StringVar(value="2036-12-31")
    private_key_var = tk.StringVar(value=str(DEFAULT_PRIVATE_KEY_PATH))
    install_file_var = tk.StringVar(value="")
    status_var = tk.StringVar(value="Sẵn sàng.")

    def set_status(message: str) -> None:
        status_var.set(message)

    def copy_to_clipboard(text: str, success_message: str) -> None:
        text = text.strip()
        if not text:
            messagebox.showwarning("Chưa có dữ liệu", "Không có nội dung để copy.", parent=root)
            return
        root.clipboard_clear()
        root.clipboard_append(text)
        set_status(success_message)

    def paste_entry(entry: ttk.Entry) -> None:
        try:
            text = root.clipboard_get().strip()
        except tk.TclError:
            text = ""
        if text:
            entry.delete(0, tk.END)
            entry.insert(0, text)

    def paste_text(text_widget: tk.Text) -> None:
        try:
            text = root.clipboard_get().strip()
        except tk.TclError:
            text = ""
        if text:
            text_widget.delete("1.0", tk.END)
            text_widget.insert("1.0", text)

    def browse_private_key() -> None:
        path = filedialog.askopenfilename(
            title="Chọn atg_license_private.json",
            initialdir=str(DEFAULT_PRIVATE_KEY_PATH.parent),
            filetypes=[("JSON private key", "*.json"), ("All files", "*.*")],
            parent=root,
        )
        if path:
            private_key_var.set(path)

    def browse_license_file() -> None:
        path = filedialog.askopenfilename(
            title="Chọn file license",
            filetypes=[("License files", "*.key *.txt"), ("All files", "*.*")],
            parent=root,
        )
        if not path:
            return
        install_file_var.set(path)
        try:
            install_text.delete("1.0", tk.END)
            install_text.insert("1.0", Path(path).read_text(encoding="utf-8").strip())
        except OSError as exc:
            messagebox.showerror("Không đọc được file", str(exc), parent=root)

    def refresh_machine_code() -> None:
        machine_code_var.set(get_machine_code())
        set_status("Đã lấy mã máy hiện tại.")

    def issue_license() -> None:
        try:
            token = create_license_token(
                machine_code=machine_code_var.get(),
                customer=customer_var.get(),
                expires=expires_var.get(),
                private_key_path=private_key_var.get(),
            )
        except Exception as exc:
            messagebox.showerror("Không tạo được mã kích hoạt", str(exc), parent=root)
            return
        output_text.delete("1.0", tk.END)
        output_text.insert("1.0", token)
        set_status("Đã tạo mã kích hoạt. Có thể copy hoặc lưu thành file license.key.")

    def save_license() -> None:
        token = output_text.get("1.0", tk.END).strip()
        if not token:
            messagebox.showwarning("Chưa có mã kích hoạt", "Hãy tạo mã kích hoạt trước khi lưu file.", parent=root)
            return
        path = filedialog.asksaveasfilename(
            title="Lưu license.key",
            defaultextension=".key",
            initialfile="license.key",
            filetypes=[("License key", "*.key"), ("Text files", "*.txt"), ("All files", "*.*")],
            parent=root,
        )
        if not path:
            return
        Path(path).write_text(token + "\n", encoding="utf-8")
        set_status(f"Đã lưu license: {path}")

    def install_license_from_text() -> None:
        try:
            message = install_license(install_text.get("1.0", tk.END))
        except Exception as exc:
            messagebox.showerror("Không cài được license", str(exc), parent=root)
            return
        messagebox.showinfo("Cài license thành công", message, parent=root)
        set_status("Đã cài license vào máy hiện tại.")

    root.deiconify()

    main = ttk.Frame(root, padding=18)
    main.pack(fill=tk.BOTH, expand=True)

    ttk.Label(main, text="ATG License Tool", style="Title.TLabel").pack(anchor=tk.W)
    ttk.Label(
        main,
        text="Mini app phát hành license theo mã máy. Private key chỉ lưu trên máy quản trị.",
    ).pack(anchor=tk.W, pady=(4, 16))

    issuer = ttk.LabelFrame(main, text="Tạo mã kích hoạt", padding=14, style="Section.TLabelframe")
    issuer.pack(fill=tk.BOTH, expand=True)
    issuer.columnconfigure(1, weight=1)
    issuer.columnconfigure(3, weight=1)

    ttk.Label(issuer, text="Mã máy").grid(row=0, column=0, sticky=tk.W, padx=(0, 8), pady=5)
    machine_entry = ttk.Entry(issuer, textvariable=machine_code_var)
    machine_entry.grid(row=0, column=1, columnspan=3, sticky=tk.EW, pady=5)
    ttk.Button(issuer, text="Lấy mã máy hiện tại", command=refresh_machine_code).grid(row=0, column=4, padx=(8, 0), pady=5)
    ttk.Button(issuer, text="Copy", command=lambda: copy_to_clipboard(machine_code_var.get(), "Đã copy mã máy.")).grid(
        row=0, column=5, padx=(8, 0), pady=5
    )
    ttk.Button(issuer, text="Dán", command=lambda: paste_entry(machine_entry)).grid(row=0, column=6, padx=(8, 0), pady=5)

    ttk.Label(issuer, text="Tên đơn vị/khách hàng").grid(row=1, column=0, sticky=tk.W, padx=(0, 8), pady=5)
    ttk.Entry(issuer, textvariable=customer_var).grid(row=1, column=1, sticky=tk.EW, pady=5)
    ttk.Label(issuer, text="Hết hạn").grid(row=1, column=2, sticky=tk.W, padx=(14, 8), pady=5)
    ttk.Entry(issuer, textvariable=expires_var).grid(row=1, column=3, sticky=tk.EW, pady=5)
    ttk.Label(issuer, text="YYYY-MM-DD; bỏ trống nếu vĩnh viễn").grid(row=1, column=4, columnspan=3, sticky=tk.W, padx=(8, 0), pady=5)

    ttk.Label(issuer, text="Private key").grid(row=2, column=0, sticky=tk.W, padx=(0, 8), pady=5)
    ttk.Entry(issuer, textvariable=private_key_var).grid(row=2, column=1, columnspan=5, sticky=tk.EW, pady=5)
    ttk.Button(issuer, text="Chọn...", command=browse_private_key).grid(row=2, column=6, padx=(8, 0), pady=5)

    ttk.Button(issuer, text="Tạo mã kích hoạt", command=issue_license).grid(row=3, column=0, sticky=tk.W, pady=(12, 8))
    ttk.Button(
        issuer,
        text="Copy mã kích hoạt",
        command=lambda: copy_to_clipboard(output_text.get("1.0", tk.END), "Đã copy mã kích hoạt."),
    ).grid(row=3, column=1, sticky=tk.W, pady=(12, 8))
    ttk.Button(issuer, text="Lưu license.key", command=save_license).grid(row=3, column=2, sticky=tk.W, pady=(12, 8))

    output_text = tk.Text(issuer, height=7, wrap=tk.WORD)
    output_text.grid(row=4, column=0, columnspan=7, sticky=tk.NSEW, pady=(4, 0))
    issuer.rowconfigure(4, weight=1)

    installer = ttk.LabelFrame(main, text="Cài mã kích hoạt vào máy hiện tại", padding=14, style="Section.TLabelframe")
    installer.pack(fill=tk.BOTH, expand=True, pady=(16, 0))
    installer.columnconfigure(1, weight=1)

    ttk.Label(installer, text="File license").grid(row=0, column=0, sticky=tk.W, padx=(0, 8), pady=5)
    ttk.Entry(installer, textvariable=install_file_var).grid(row=0, column=1, sticky=tk.EW, pady=5)
    ttk.Button(installer, text="Chọn file...", command=browse_license_file).grid(row=0, column=2, padx=(8, 0), pady=5)

    install_text = tk.Text(installer, height=5, wrap=tk.WORD)
    install_text.grid(row=1, column=0, columnspan=3, sticky=tk.NSEW, pady=(4, 8))
    installer.rowconfigure(1, weight=1)

    ttk.Button(installer, text="Dán mã kích hoạt", command=lambda: paste_text(install_text)).grid(row=2, column=0, sticky=tk.W)
    ttk.Button(installer, text="Cài license", command=install_license_from_text).grid(row=2, column=1, sticky=tk.W)

    footer = ttk.Frame(main)
    footer.pack(fill=tk.X, pady=(12, 0))
    ttk.Label(footer, textvariable=status_var).pack(side=tk.LEFT)
    ttk.Button(footer, text="Đóng", command=root.destroy).pack(side=tk.RIGHT)

    root.mainloop()


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Công cụ license theo máy cho ATG Document Manager.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    machine_parser = subparsers.add_parser("machine", help="Hiển thị mã máy của server hiện tại.")
    machine_parser.set_defaults(func=lambda _args: print(get_machine_code()))

    issue_parser = subparsers.add_parser("issue", help="Phát hành license cho một mã máy.")
    issue_parser.add_argument("--machine-code", required=True, help="Mã máy lấy từ màn hình cấu hình hoặc lệnh machine.")
    issue_parser.add_argument("--customer", required=True, help="Tên đơn vị/khách hàng.")
    issue_parser.add_argument("--expires", default="", help="Ngày hết hạn dạng YYYY-MM-DD; bỏ trống nếu vĩnh viễn.")
    issue_parser.add_argument("--private-key", default=str(DEFAULT_PRIVATE_KEY_PATH), help="Đường dẫn private key phát hành license.")
    issue_parser.add_argument("--output", help="File xuất license. Nếu bỏ trống, in license ra màn hình.")
    issue_parser.set_defaults(func=_issue)

    install_parser = subparsers.add_parser("install", help="Cài license vào server hiện tại từ file hoặc chuỗi license.")
    install_source = install_parser.add_mutually_exclusive_group(required=True)
    install_source.add_argument("--file", help="Đường dẫn file license.")
    install_source.add_argument("--license-key", help="Chuỗi license.")
    install_parser.set_defaults(func=_install)
    return parser


def main() -> None:
    _configure_console_encoding()
    if len(sys.argv) == 1:
        _start_gui_app()
        return

    parser = _build_parser()
    args = parser.parse_args()
    _require_cli_password()
    try:
        args.func(args)
    except ValueError as exc:
        raise SystemExit(str(exc)) from exc


if __name__ == "__main__":
    main()
