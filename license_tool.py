from __future__ import annotations

import argparse
import json
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


def _load_private_key(path: Path) -> dict:
    if not path.exists():
        raise SystemExit(
            f"Không tìm thấy private key: {path}\n"
            "Private key chỉ nên lưu trên máy quản trị phát hành license, không copy sang máy người dùng."
        )
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise SystemExit(f"Private key không phải JSON hợp lệ: {exc}") from exc
    required = {"n", "e", "d"}
    if not required.issubset(data):
        raise SystemExit("Private key thiếu n/e/d.")
    return data


def _issue(args: argparse.Namespace) -> None:
    private_key = _load_private_key(Path(args.private_key))
    payload = {
        "app": APP_LICENSE_CODE,
        "license_id": str(uuid.uuid4()),
        "machine_code": args.machine_code.strip().upper(),
        "customer": args.customer.strip(),
        "issued_at": date.today().isoformat(),
        "expires_at": args.expires.strip() if args.expires else "",
    }
    signature = rsa_sign_payload(payload, private_key)
    token = build_license_token(payload, signature)
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
    status = install_license_key(raw_license)
    print(status.message)
    print(f"Mã máy: {status.machine_code}")
    print(f"File license: {status.license_file}")


def main() -> None:
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

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
