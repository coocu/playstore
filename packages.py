import subprocess
import tkinter as tk
from tkinter import messagebox, scrolledtext

# ---------------------------------------------
# ADB 실행 함수 (콘솔 창 안 뜨게 수정)
# ---------------------------------------------
CREATE_NO_WINDOW = 0x08000000  # Windows only

def run_adb(cmd):
    try:
        result = subprocess.run(
            ["adb"] + cmd,
            capture_output=True,
            text=True,
            encoding="utf-8",
            creationflags=CREATE_NO_WINDOW
        )
        return result.stdout.strip()
    except Exception as e:
        return str(e)

# ---------------------------------------------
# 스마트폰 연결 확인
# ---------------------------------------------
def check_device():
    output = run_adb(["devices"])

    connected = False
    for line in output.splitlines():
        if "\tdevice" in line:
            connected = True
            break

    if connected:
        messagebox.showinfo("연결됨", "스마트폰 연결이 정상적으로 감지되었습니다.")
    else:
        messagebox.showerror("연결 실패", "스마트폰이 감지되지 않았습니다.\nUSB 연결 및 USB 디버깅을 확인하세요.")

# ---------------------------------------------
# packages.txt 기반 앱 삭제 (진행 상태 팝업 개선)
# ---------------------------------------------
def remove_packages():
    try:
        with open("packages.txt", "r", encoding="utf-8") as f:
            packages = [p.strip() for p in f.readlines() if p.strip()]
    except FileNotFoundError:
        messagebox.showerror("Error", "packages.txt 파일이 없습니다.")
        return

    devices = run_adb(["devices"]).splitlines()
    target = ""

    for line in devices:
        if "\tdevice" in line:
            target = line.split("\t")[0]

    if not target:
        messagebox.showerror("연결 실패", "디바이스가 연결되지 않았습니다.")
        return

    # 진행 상태 창
    progress_window = tk.Toplevel(root)
    progress_window.title("삭제 진행 중...")
    progress_window.geometry("450x300")
    progress_window.configure(bg="#1e1e1e")
    
    tk.Label(progress_window, text="삭제 진행 상태", fg="white", bg="#1e1e1e", font=("맑은 고딕", 12)).pack(pady=10)

    progress_text = scrolledtext.ScrolledText(progress_window, width=55, height=12, bg="#2b2b2b", fg="white", font=("맑은 고딕", 11))
    progress_text.pack(pady=5)
    progress_text.insert(tk.END, "삭제 시작...\n")
    progress_text.update()

    for pkg in packages:
        check = run_adb(["-s", target, "shell", "pm", "path", pkg])

        if not check:
            progress_text.insert(tk.END, f"{pkg} - 건너뛰기\n")
            progress_text.see(tk.END)  # 스크롤 자동 이동
            progress_text.update()
            continue

        result = run_adb(["-s", target, "shell", "pm", "uninstall", "--user", "0", pkg])

        if "Success" in result:
            progress_text.insert(tk.END, f"{pkg} - 제거 완료 (user 0)\n")
        else:
            run_adb(["-s", target, "uninstall", pkg])
            progress_text.insert(tk.END, f"{pkg} - 제거 완료\n")
        progress_text.see(tk.END)  # 스크롤 자동 이동
        progress_text.update()

    progress_text.insert(tk.END, "모든 패키지 삭제 완료!\n")
    progress_text.update()
    messagebox.showinfo("삭제 완료", "packages.txt에 있는 모든 패키지 삭제 완료!")

# ---------------------------------------------
# 현재 앱 패키지명 확인
# ---------------------------------------------
def check_current_package():
    output = run_adb(["shell", "dumpsys", "window"])

    pkg = "Package Not Found"
    for line in output.splitlines():
        if "mCurrentFocus" in line:
            import re
            match = re.search(r"u0\s+([a-zA-Z0-9_.]+)/", line)
            if match:
                pkg = match.group(1)
            else:
                match2 = re.search(r"\s([a-zA-Z0-9_.]+?)/", line)
                if match2:
                    pkg = match2.group(1)

    pkg_var.set(pkg)
    messagebox.showinfo("패키지 확인", f"현재 실행 중 앱 패키지명:\n\n{pkg}")

# ---------------------------------------------
# ---------------------------------------------
# 패키지명 packages.txt에 추가 (Play Store 차단)
# ---------------------------------------------

BLOCKED_PACKAGES = {
    "com.android.vending",     # Play Store
    "com.google.android.gms",  # Google Play Services
    "com.google.android.gsf",  # Google Services Framework
}

def add_package():
    pkg = pkg_var.get().strip()
    if not pkg:
        messagebox.showerror("Error", "패키지명이 비어 있습니다.")
        return

    # 🔒 차단 패키지 검사
    if pkg in BLOCKED_PACKAGES:
        messagebox.showwarning(
            "차단됨",
            f"{pkg}\n\n시스템 핵심 앱이므로 추가할 수 없습니다."
        )
        return

    try:
        # 기존 내용 읽기
        try:
            with open("packages.txt", "r", encoding="utf-8") as f:
                lines = f.readlines()
        except FileNotFoundError:
            lines = []

        # 🔁 중복 방지
        if any(pkg == line.strip() for line in lines):
            messagebox.showinfo("이미 존재", f"{pkg}\n이미 packages.txt에 존재합니다.")
            return

        # ⬆️ 맨 위에 추가
        lines.insert(0, pkg + "\n")

        # 저장
        with open("packages.txt", "w", encoding="utf-8") as f:
            f.writelines(lines)

        messagebox.showinfo("추가 완료", f"{pkg}\npackages.txt 맨 위에 추가되었습니다.")

    except Exception as e:
        messagebox.showerror("Error", f"패키지 추가 실패\n{e}")
        
# ---------------------------------------------
# 개발자 옵션 종료
# ---------------------------------------------
def disable_developer_options():
    cmds = [
        ["shell", "settings", "put", "global", "development_settings_enabled", "0"],
        ["shell", "settings", "put", "global", "adb_enabled", "0"],
        ["shell", "settings", "put", "global", "usb_debugging_enabled", "0"]
    ]

    for cmd in cmds:
        run_adb(cmd)

    messagebox.showinfo("완료", "개발자 옵션이 비활성화되었습니다.")

# ---------------------------------------------
# 프로그램 종료
# ---------------------------------------------
def exit_program():
    root.destroy()

# ---------------------------------------------
# UI (다크테마 / 2열 버튼)
# ---------------------------------------------
root = tk.Tk()
root.title("앱 제거 프로그램")
root.geometry("450x300")
root.configure(bg="#1e1e1e")

pkg_var = tk.StringVar()

tk.Label(root, text="현재 앱 패키지명", fg="white", bg="#1e1e1e", font=("맑은 고딕", 12)).pack(pady=3)

pkg_entry = tk.Entry(root, textvariable=pkg_var, width=40,
                     font=("맑은 고딕", 12), bg="#2b2b2b", fg="white", bd=1)
pkg_entry.pack(pady=3)

def make_button(text, cmd):
    return tk.Button(
        frame,
        text=text,
        command=cmd,
        width=18,
        height=2,
        bg="#323232",
        fg="white",
        activebackground="#4e4e4e",
        activeforeground="white",
        bd=0,
        font=("맑은 고딕", 11)
    )

frame = tk.Frame(root, bg="#1e1e1e")
frame.pack(pady=10)

buttons = [
    ("스마트폰 연결 확인", check_device),
    ("앱 삭제하기", remove_packages),
    ("현재 앱 패키지 확인", check_current_package),
    ("패키지명 추가", add_package),
    ("개발자 옵션 종료", disable_developer_options),
    ("프로그램 종료", exit_program)
]

row = 0
col = 0
for text, func in buttons:
    btn = make_button(text, func)
    btn.grid(row=row, column=col, padx=6, pady=6)
    col += 1
    if col == 2:
        col = 0
        row += 1

root.mainloop()
