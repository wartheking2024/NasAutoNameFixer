import os
import re
import tkinter as tk
from tkinter import filedialog, messagebox, ttk


def extract_episode(file_name):
    name = os.path.splitext(file_name)[0]

    patterns = [
        # S02E03 / S2E3
        r"[Ss]\d{1,2}[Ee](\d{1,4})",

        # E03 / EP03（独立单词）
        r"\b[Ee][Pp]?(\d{1,4})\b",

        # 第03集
        r"第\s*(\d{1,4})\s*集",

        # 被分隔符包围 .03. _03_ -03- 空格03空格
        r"(?:^|[.\-_ ])(\d{1,4})(?=[.\-_ ]|$)",

        # 文件名开头是数字
        r"^\s*(\d{1,4})\b",
    ]

    for pattern in patterns:
        match = re.search(pattern, name)
        if match:
            return int(match.group(1))

    return None

def show_preview_window(preview_list):
    win = tk.Toplevel()
    win.title("重命名预览（确认后才执行）")
    win.geometry("800x500")

    text = tk.Text(win, wrap="none")
    text.pack(fill=tk.BOTH, expand=True)

    scrollbar_y = tk.Scrollbar(text, orient=tk.VERTICAL, command=text.yview)
    scrollbar_y.pack(side=tk.RIGHT, fill=tk.Y)
    text.config(yscrollcommand=scrollbar_y.set)

    scrollbar_x = tk.Scrollbar(text, orient=tk.HORIZONTAL, command=text.xview)
    scrollbar_x.pack(side=tk.BOTTOM, fill=tk.X)
    text.config(xscrollcommand=scrollbar_x.set)

    # 写入内容
    for old, new in preview_list:
        text.insert(tk.END, f"{old:<50} → {new}\n")

    text.config(state=tk.DISABLED)

    result = {"confirmed": False}

    def confirm():
        result["confirmed"] = True
        win.destroy()

    def cancel():
        win.destroy()

    btn_frame = tk.Frame(win)
    btn_frame.pack(fill=tk.X)

    tk.Button(btn_frame, text="确认执行", command=confirm, bg="green", fg="white").pack(side=tk.LEFT, padx=20, pady=10)
    tk.Button(btn_frame, text="取消", command=cancel, bg="red", fg="white").pack(side=tk.RIGHT, padx=20, pady=10)

    win.wait_window()

    return result["confirmed"]


def rename_files(folder_path, show_name, season, resolution, year,
                 folder_entry, name_entry, season_entry, resolution_combo, year_combo, offset_entry):

    file_list = [f for f in os.listdir(folder_path)
                 if os.path.isfile(os.path.join(folder_path, f))]

    if year:
        year = "." + str(year)

    if resolution:
        if resolution == "4k":
            resolution = "2160p"
        elif resolution == "2k":
            resolution = "1440p"
        resolution = "." + resolution

    season_prefix = "S" + season.zfill(2)

    # 获取起始集
    try:
        start_episode = int(offset_entry.get())
    except:
        start_episode = 1

    # 收集所有集数
    episodes = []

    for file_name in file_list:
        ep = extract_episode(file_name)
        if ep is not None:
            episodes.append(ep)

    if not episodes:
        messagebox.showerror("错误", "没有识别到集数")
        return

    min_episode = min(episodes)

    preview_list = []

    for file_name in file_list:
        filepureName = os.path.splitext(file_name)[0]


        episode = extract_episode(file_name)

        if episode is None:
            continue

        extension = os.path.splitext(file_name)[1]

        new_episode = episode - min_episode + start_episode
        extension = os.path.splitext(file_name)[1].lower()
        new_file_name = "{}.{}E{}{}{}{}".format(
            show_name,
            season_prefix,
            str(new_episode).zfill(2),
            year,
            resolution,
            extension
        )

        preview_list.append((file_name, new_file_name))

    if not preview_list:
        messagebox.showwarning("提示", "没有可处理的文件")
        return

    # 🔥 排序（按集数）
    preview_list = sorted(preview_list, key=lambda x: extract_episode(x[0]))

    # 🔥 打开高级预览窗口
    confirmed = show_preview_window(preview_list)

    if not confirmed:
        return

    # ✅ 执行重命名
    for old, new in preview_list:
        old_path = os.path.join(folder_path, old)
        new_path = os.path.join(folder_path, new)

        print("Renaming:", old_path, "→", new_path)
        os.rename(old_path, new_path)

    messagebox.showinfo("完成", "文件重命名完成！")

    # 清空UI
    folder_entry.delete(0, tk.END)
    name_entry.delete(0, tk.END)
    season_entry.delete(0, tk.END)
    resolution_combo.set("")
    year_combo.set("")


def select_folder():

    def handle_select_folder():
        folder_path = filedialog.askdirectory()
        if folder_path:
            folder_entry.delete(0, tk.END)
            folder_entry.insert(tk.END, folder_path)

            show_name = os.path.basename(folder_path)

            resolutions = ["2160p", "1440p", "1080p", "720p", "480p"]
            for r in resolutions:
                if r in show_name:
                    resolution_combo.set(r)
                    break

            for y in range(1900, 2031):
                if str(y) in show_name:
                    year_combo.set(y)
                    break

            show_name = show_name.replace("中文版", "")
            show_name = re.sub(r'\d+|\.', '', show_name)

            name_entry.delete(0, tk.END)
            name_entry.insert(tk.END, show_name)

    def handle_rename_files():
        folder_path = folder_entry.get()
        show_name = name_entry.get()
        season = season_entry.get()
        resolution = resolution_combo.get()
        year = year_combo.get()

        if folder_path and show_name and season and show_name != "必填" and season != "必填":
            rename_files(folder_path, show_name, season, resolution, year,
                folder_entry, name_entry, season_entry, resolution_combo, year_combo, offset_entry)
        else:
            messagebox.showwarning("输入错误", "请填写完整的信息！")

    root = tk.Tk()
    root.title("文件重命名工具")

    tk.Label(root, text="选择文件夹：").pack()
    folder_entry = tk.Entry(root, width=50)
    folder_entry.pack()

    tk.Button(root, text="选择", command=handle_select_folder).pack()

    tk.Label(root, text="电视剧名称：").pack()
    name_entry = tk.Entry(root, width=50)
    name_entry.insert(tk.END, "必填")
    name_entry.pack()

    tk.Label(root, text="第几季：").pack()
    season_entry = tk.Entry(root, width=50)
    season_entry.insert(tk.END, "必填")
    season_entry.pack()

    tk.Label(root, text="分辨率：").pack()
    resolution_combo = ttk.Combobox(root, values=["4k", "2k", "1080p", "720p", "480p"])
    resolution_combo.pack()

    tk.Label(root, text="年份：").pack()
    year_combo = ttk.Combobox(root, values=list(range(1900, 2031)))
    year_combo.pack()

    tk.Label(root, text="起始集（可选）：").pack()

    offset_entry = tk.Entry(root, width=50)
    offset_entry.insert(tk.END, "1")  # 默认从1开始
    offset_entry.pack()

    tk.Button(root, text="开始重命名", command=handle_rename_files).pack()

    root.mainloop()


select_folder()