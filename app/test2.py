import ttkbootstrap as ttk
from ttkbootstrap.dialogs import Messagebox
root = ttk.Window()
print("ok: ",Messagebox.ok(
    message="要在消息框中显示的消息",
    title="消息框的标题",
    alert=False, #指定是否响铃，默认False
))
print("okcancel: ",Messagebox.okcancel(message="确定取消"))
print("retrycancel: ",Messagebox.retrycancel(message="重试取消"))
print("retrycancel: ",Messagebox.show_error(message="显示错误"))
print("retrycancel: ",Messagebox.show_info(message="显示信息"))
print("retrycancel: ",Messagebox.show_question(message="显示问题"))
print("retrycancel: ",Messagebox.show_warning(message="显示警告"))
print("retrycancel: ",Messagebox.yesno(message="是的"))
print("retrycancel: ",Messagebox.yesnocancel(message="是的取消"))
root.mainloop()