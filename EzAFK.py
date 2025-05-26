

import ctypes
from ctypes import wintypes



MOUSEEVENTF_MOVE        = 0b0000000000000001
MOUSEEVENTF_ABSOLUTE    = 0b1000000000000000
MOUSEEVENTF_LEFTDOWN    = 0b0000000000000010
MOUSEEVENTF_LEFTUP      = 0b0000000000000100
MOUSEEVENTF_KEYUP = 0b10
INPUT_KEYBOARD = 1
TH32CS_SNAPPROCESS = 0x00000002



class PROCESSENTRY32(ctypes.Structure):
    _fields_ = [
        ("dwSize", wintypes.DWORD),
        ("cntUsage", wintypes.DWORD),
        ("th32ProcessID", wintypes.DWORD),
        ("th32DefaultHeapID", ctypes.POINTER(wintypes.ULONG)),
        ("th32ModuleID", wintypes.DWORD),
        ("cntThreads", wintypes.DWORD),
        ("th32ParentProcessID", wintypes.DWORD),
        ("pcPriClassBase", wintypes.LONG),
        ("dwFlags", wintypes.DWORD),
        ("szExeFile", wintypes.CHAR * 260)
    ]




def char_to_vk(c):
    return ctypes.windll.user32.VkKeyScanW(ord(c)) & 0xff


class AFK:
    pid = 0

    @staticmethod
    def log(message):
        print(f"[DEBUG] {message}")


    def sleep(ms):
        ctypes.windll.kernel32.Sleep(int(ms))

    def click(self, x=None, y=None):
        screen_width = ctypes.windll.user32.GetSystemMetrics(0)
        screen_height = ctypes.windll.user32.GetSystemMetrics(1)

        if x is None or y is None:
            class POINT(ctypes.Structure):
                _fields_ = [("x", ctypes.c_long), ("y", ctypes.c_long)]

            pt = POINT()
            ctypes.windll.user32.GetCursorPos(ctypes.byref(pt))
            x, y = pt.x, pt.y

        abs_x = int(x * 65535 / screen_width)
        abs_y = int(y * 65535 / screen_height)

        AFK.log(f"Clicking at screen coords: ({x}, {y}) → abs: ({abs_x}, {abs_y})")

        if x is not None and y is not None:
            ctypes.windll.user32.mouse_event(MOUSEEVENTF_MOVE | MOUSEEVENTF_ABSOLUTE, abs_x, abs_y, 0, 0)

        ctypes.windll.user32.mouse_event(MOUSEEVENTF_LEFTDOWN, abs_x, abs_y, 0, 0)
        AFK.sleep(10)
        ctypes.windll.user32.mouse_event(MOUSEEVENTF_LEFTUP, abs_x, abs_y, 0, 0)


    def mouse_wheel(self, delta=120):
        MOUSEEVENTF_WHEEL = 0b0000100000000000
        ctypes.windll.user32.mouse_event(MOUSEEVENTF_WHEEL, 0, 0, delta, 0)



    def type(self, *chars):
        if len(chars) == 1 and len(chars[0]) > 1:
            print(chars[0])
            return
        
        class KI(ctypes.Structure):
            _fields_ = [("wVk", wintypes.WORD), ("wScan", wintypes.WORD), ("dwFlags", wintypes.DWORD), ("time", wintypes.DWORD), ("dwExtraInfo", ctypes.POINTER(ctypes.c_ulong))]
        class INPUT(ctypes.Structure):
            class U(ctypes.Union):
                _fields_ = [("ki", KI)]
            _anonymous_ = ("u",)
            _fields_ = [("type", wintypes.DWORD), ("u", U)]

        for ch in chars:
            vk = char_to_vk(ch)
            down = INPUT(type=INPUT_KEYBOARD, ki=KI(wVk=vk, wScan=0, dwFlags=0, time=0, dwExtraInfo=None))
            up = INPUT(type=INPUT_KEYBOARD, ki=KI(wVk=vk, wScan=0, dwFlags=MOUSEEVENTF_KEYUP, time=0, dwExtraInfo=None))
            ctypes.windll.user32.SendInput(1, ctypes.byref(down), ctypes.sizeof(down))
            ctypes.windll.user32.SendInput(1, ctypes.byref(up), ctypes.sizeof(up))


    def move(self, x, y):
        screen_w = ctypes.windll.user32.GetSystemMetrics(0)
        screen_h = ctypes.windll.user32.GetSystemMetrics(1)
        abs_x = int(x * 65535 / screen_w)
        abs_y = int(y * 65535 / screen_h)
        ctypes.windll.user32.mouse_event(0b1000000000000001, abs_x, abs_y, 0, 0)


    def double_click(self, x, y):
        self.click(x, y)
        AFK.sleep(0.05)
        self.click(x, y)

    def get_pid(self, proc_name):
        CreateToolhelp32Snapshot = ctypes.windll.kernel32.CreateToolhelp32Snapshot
        Process32First = ctypes.windll.kernel32.Process32First
        Process32Next = ctypes.windll.kernel32.Process32Next
        CloseHandle = ctypes.windll.kernel32.CloseHandle

        hSnapshot = CreateToolhelp32Snapshot(TH32CS_SNAPPROCESS, 0)
        entry = PROCESSENTRY32()
        entry.dwSize = ctypes.sizeof(PROCESSENTRY32)

        has_process = Process32First(hSnapshot, ctypes.byref(entry))
        while has_process:
            if entry.szExeFile.decode().lower() == proc_name.lower():
                self.pid = entry.th32ProcessID
                CloseHandle(hSnapshot)
                return
            has_process = Process32Next(hSnapshot, ctypes.byref(entry))
        self.pid = 0
        CloseHandle(hSnapshot)


    def kill(self):
        if not self.pid:
            return
        handle = ctypes.windll.kernel32.OpenProcess(1, False, self.pid)
        if handle:
            ctypes.windll.kernel32.TerminateProcess(handle, 0)
            ctypes.windll.kernel32.CloseHandle(handle)
            self.pid = 0



    def is_running(self):
        if not self.pid:
            return False
        handle = ctypes.windll.kernel32.OpenProcess(0x1000, False, self.pid)
        if not handle:
            return False
        ctypes.windll.kernel32.CloseHandle(handle)
        return True


    def bring_to_front(self):
        hwnd = self.window_handle()
        if hwnd:
            ctypes.windll.user32.ShowWindow(hwnd, 5)  
            ctypes.windll.user32.SetForegroundWindow(hwnd)


    def get_screen_resolution(self):
        w = ctypes.windll.user32.GetSystemMetrics(0)
        h = ctypes.windll.user32.GetSystemMetrics(1)
        return w, h


    def show_cursor(self, show=True):
        ctypes.windll.user32.ShowCursor(show)


    def set_window_state(self, hwnd, state):
        # state: 6=maximize, 9=restore, 6=minimize
        ctypes.windll.user32.ShowWindow(hwnd, state)

def main():
    afk = AFK()
    print("Welcome....")
    afk.get_pid("notepad.exe")
    print(afk.pid)  # prints PID or 0 if not found

if __name__ == "__main__":
    main()
