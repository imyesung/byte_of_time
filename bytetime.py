import curses
import time
import threading
from plyer import notification
from datetime import datetime

class ByteTimeManager:
    def __init__(self, stdscr):
        self.stdscr = stdscr
        self.tasks = []
        self.current_task = None
        self.start_time = None
        self.selected_index = 0
        self.total_time = 0  # 전체 예상 작업 시간
        self.log = []  # 로그 기록

    def add_task(self, task, estimated_time):
        self.tasks.append({
            "name": task,
            "duration": 0,
            "status": "Pending",
            "estimated_time": estimated_time * 60  # 분 단위를 초 단위로 변환
        })
        self.total_time += estimated_time * 60  # 분 단위를 초 단위로 변환
        self.log_event(f"작업 추가: {task}, 예상 시간: {estimated_time}분")

    def start_task(self, index):
        if 0 <= index < len(self.tasks):
            if self.current_task is not None:
                self.pause_task()  # Pause the current task if any
            self.current_task = self.tasks[index]
            self.current_task["status"] = "In Progress"
            self.start_time = time.time()
            self.start_timer()
            self.log_event(f"작업 시작: {self.current_task['name']}")

    def pause_task(self):
        if self.current_task is not None:
            elapsed_time = time.time() - self.start_time
            self.current_task["duration"] += elapsed_time
            self.current_task["status"] = "Paused"
            self.log_event(f"작업 일시정지: {self.current_task['name']}")
            self.current_task = None
            self.start_time = None

    def cancel_task(self, index):
        if 0 <= index < len(self.tasks):
            task = self.tasks.pop(index)
            self.total_time -= task["estimated_time"]
            self.log_event(f"작업 취소: {task['name']}")

    def stop_task(self):
        if self.current_task is not None:
            elapsed_time = time.time() - self.start_time
            self.current_task["duration"] += elapsed_time
            self.current_task["status"] = "Completed"
            self.log_event(f"작업 완료: {self.current_task['name']}")
            self.current_task = None
            self.start_time = None

    def start_timer(self):
        def timer_thread():
            while self.current_task and self.start_time:
                time.sleep(60)  # Check every minute
                if self.current_task and self.start_time:
                    elapsed = time.time() - self.start_time
                    if elapsed >= 25 * 60:  # 25 minutes
                        self.show_notification("휴식 시간!", "25분 작업 완료. 5분간 휴식하세요.")
                        self.pause_task()

        threading.Thread(target=timer_thread, daemon=True).start()

    def show_notification(self, title, message):
        notification.notify(
            title=title,
            message=message,
            app_name="ByteTime",
        )

    def draw_progress_bar(self, y, x, width, percentage):
        filled_width = int(width * percentage)
        self.stdscr.addstr(y, x, "[" + "#" * filled_width + "-" * (width - filled_width) + "]")

    def draw_ui(self):
        self.stdscr.clear()
        height, width = self.stdscr.getmaxyx()

        # Draw title
        title = "ByteTime: Byte of Task management"
        self.stdscr.addstr(0, (width - len(title)) // 2, title, curses.A_BOLD)

        # Draw overall progress
        total_duration = sum(task["duration"] for task in self.tasks)
        overall_progress = min(total_duration / self.total_time if self.total_time else 0, 1)
        self.stdscr.addstr(2, 2, f"전체 진행률: {overall_progress:.1%}")
        self.draw_progress_bar(3, 2, width - 4, overall_progress)

        # Draw tasks
        for i, task in enumerate(self.tasks):
            if i == self.selected_index:
                mode = curses.A_REVERSE
            else:
                mode = curses.A_NORMAL

            status_icon = {
                "Pending": "[ ]",
                "In Progress": "[>]",
                "Paused": "[||]",
                "Completed": "[✓]"
            }.get(task["status"], "[ ]")

            task_progress = min(task["duration"] / task["estimated_time"], 1) if task["estimated_time"] != 0 else 0
            task_str = f"{status_icon} {task['name']} ({task['duration'] / 60:.0f}분 / {task['estimated_time'] / 60:.0f}분)"
            self.stdscr.addstr(i + 5, 2, task_str, mode)
            self.draw_progress_bar(i + 6, 4, width - 8, task_progress)

        # Draw menu
        menu_items = [
            "A: 작업 추가",
            "S: 작업 시작/일시정지",
            "D: 작업 완료",
            "X: 작업 취소",
            "Q: 종료"
        ]
        for i, item in enumerate(menu_items):
            self.stdscr.addstr(height - len(menu_items) - 1 + i, 2, item)

        self.stdscr.refresh()

    def log_event(self, event):
        self.log.append(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - {event}")

    def run(self):
        curses.curs_set(0)  # Hide cursor
        while True:
            self.draw_ui()
            key = self.stdscr.getch()

            if key == ord('q'):
                break
            elif key == ord('a'):
                curses.echo()
                self.stdscr.addstr(curses.LINES - 1, 0, "새 작업 이름: ")
                task = ""
                while True:
                    char = self.stdscr.get_wch()
                    if char == '\n':
                        break
                    elif char == '\b' or char == curses.KEY_BACKSPACE:
                        task = task[:-1]
                        self.stdscr.addstr(curses.LINES - 1, len("새 작업 이름: ") + len(task), ' ')
                        self.stdscr.move(curses.LINES - 1, len("새 작업 이름: ") + len(task))
                    else:
                        task += char
                    self.stdscr.addstr(curses.LINES - 1, len("새 작업 이름: "), task)
                    self.stdscr.refresh()
                self.stdscr.addstr(curses.LINES - 1, 0, "예상 소요 시간(분): ")
                estimated_time_str = ""
                while True:
                    char = self.stdscr.get_wch()
                    if char == '\n':
                        break
                    elif char == '\b' or char == curses.KEY_BACKSPACE:
                        estimated_time_str = estimated_time_str[:-1]
                        self.stdscr.addstr(curses.LINES - 1, len("예상 소요 시간(분): ") + len(estimated_time_str), ' ')
                        self.stdscr.move(curses.LINES - 1, len("예상 소요 시간(분): ") + len(estimated_time_str))
                    else:
                        estimated_time_str += char
                    self.stdscr.addstr(curses.LINES - 1, len("예상 소요 시간(분): "), estimated_time_str)
                    self.stdscr.refresh()
                try:
                    estimated_time = int(estimated_time_str)
                except ValueError:
                    estimated_time = 0
                curses.noecho()
                if task and estimated_time > 0:
                    self.add_task(task, estimated_time)
            elif key == ord('s'):
                if self.current_task:
                    self.pause_task()
                else:
                    self.start_task(self.selected_index)
            elif key == ord('d'):
                self.stop_task()
            elif key == ord('x'):
                self.cancel_task(self.selected_index)
            elif key == curses.KEY_UP:
                self.selected_index = max(0, self.selected_index - 1)
            elif key == curses.KEY_DOWN:
                self.selected_index = min(len(self.tasks) - 1, self.selected_index + 1)

def main(stdscr):
    manager = ByteTimeManager(stdscr)
    manager.run()

if __name__ == "__main__":
    curses.wrapper(main)