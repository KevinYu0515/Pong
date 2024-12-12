import tkinter as tk
from ttkbootstrap import Style, ttk



class ScrollableFrameApp:
    def __init__(self, root):
        # 主樣式
        style = Style(theme="superhero")
        root.geometry("500x400")
        # style = ttk.Style()
        # style.theme_use("default")  # 確保使用支持樣式的主題
        # style.configure(
        #     "Custom.Vertical.TScrollbar",
        #     gripcount=0,
        #     background="#4CAF50",  # 滾動條背景色
        #     darkcolor="#388E3C",   # 滾動條深色部分
        #     lightcolor="#C8E6C9",  # 滾動條淺色部分
        #     troughcolor="#F1F8E9", # 槽的顏色
        #     bordercolor="#2E7D32",
        #     arrowcolor="#FFFFFF",  # 箭頭顏色
        #     relief="flat",
        # )
        
        # 滾動區域
        self.canvas = tk.Canvas(root, highlightthickness=0)
        self.scrollable_frame = ttk.Frame(self.canvas)
        
        # 滾動條
        self.scrollbar = ttk.Scrollbar(root, orient="vertical", command=self.canvas.yview)
        self.scrollbar.pack(side="right", fill="y")
        self.canvas.pack(side="left", fill="both", expand=True)
        
        # 配置滾動功能
        self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=self.scrollbar.set)
        
        # 動態調整滾動範圍
        self.scrollable_frame.bind("<Configure>", self.update_scroll_region)

        # 添加內容
        for i in range(50):
            ttk.Label(self.scrollable_frame, text=f"Label {i*10000}", font=("Arial", 14)).pack(pady=5, padx=10)

    def update_scroll_region(self, event):
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))


if __name__ == "__main__":
    root = tk.Tk()
    app = ScrollableFrameApp(root)
    root.mainloop()
