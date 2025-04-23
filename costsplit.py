import tkinter as tk
from tkinter import ttk, messagebox
import numpy as np
import configparser
import os
from datetime import datetime
import sys
import tkinter.filedialog as filedialog

CONFIG_FILE = "splitter_settings.ini"

class BillSplitterApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Bill Splitter")
        self.root.geometry("800x700")
        self.root.configure(bg="#f0f0f0")
        self.receipt_path = None
        self.people = []
        self.codes = {}
        self.bills = []
        self.selected_line = None

        self.load_config()
        self.setup_ui()
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("TButton", font=("Segoe UI", 10, "bold"), padding=6)
        style.configure("TLabel", font=("Segoe UI", 10), foreground="#000", background="#f0f0f0")
        style.configure("TEntry", font=("Segoe UI", 10), foreground="#000", fieldbackground="#ffffff",
                        background="#ffffff")
        style.map("TEntry", foreground=[('focus', '#000')], fieldbackground=[('!disabled', '#ffffff')])

    def setup_ui(self):
        title = ttk.Label(self.root, text="💸 Bill Splitter", font=("Segoe UI", 18, "bold"), foreground="#333")
        title.grid(row=0, column=0, columnspan=2, pady=(5, 2), sticky="w", padx=15)

        self.root.grid_rowconfigure(1, weight=1)
        self.root.grid_columnconfigure(0, weight=1)

        self.canvas = tk.Canvas(self.root, bg="#f0f0f0", highlightthickness=0)
        scrollbar = ttk.Scrollbar(self.root, orient="vertical", command=self.canvas.yview)
        self.bill_container = tk.Frame(self.canvas, bg="#f0f0f0")

        self.bill_container.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        )

        self.canvas.create_window((0, 0), window=self.bill_container, anchor="nw")
        self.canvas.configure(yscrollcommand=scrollbar.set)

        def resize_canvas(event):
            self.canvas.itemconfig("bill_window", width=event.width)

        self.canvas.bind("<Configure>", resize_canvas)
        self.canvas.create_window((0, 0), window=self.bill_container, anchor="nw", tags="bill_window")

        self.canvas.grid(row=1, column=0, sticky="nsew", padx=(10, 0))
        scrollbar.grid(row=1, column=1, sticky="ns", padx=(0, 10))
        btn_frame = tk.Frame(self.root, bg="#f0f0f0")
        btn_frame.grid(row=2, column=0, columnspan=2, sticky="ew")
        btn_frame.columnconfigure(tuple(range(6)), weight=1)
        ttk.Button(btn_frame, text="+ Add Bill \n(Enter)", command=self.add_bill).grid(row=0, column=0, padx=5, pady=10)
        ttk.Button(btn_frame, text="Delete Selected Line\n(Del)", command=self.delete_selected_line).grid(row=0, column=1,
                                                                                                   padx=5)
        ttk.Button(btn_frame, text="Delete Last Bill\n(Ctrl-Del)", command=self.delete_last_bill).grid(row=0, column=2, padx=5)
        ttk.Button(btn_frame, text="Calculate", command=self.calculate).grid(row=0, column=3, padx=5)
        ttk.Button(btn_frame, text="Settings", command=self.open_settings).grid(row=0, column=4, padx=5)
        ttk.Button(btn_frame, text="Print Receipt", command=self.print_receipt).grid(row=0, column=5, padx=5)
        ttk.Button(btn_frame, text="Import Bills", command=self.import_bills).grid(row=0, column=6, padx=5)

        def _on_mousewheel(event):
            direction = int(-1 * (event.delta / 120))
            current = self.canvas.yview()
            if direction < 0 and current[0] <= 0.0:
                return
            if direction > 0 and current[1] >= 1.0:
                return
            self.canvas.yview_scroll(direction, "units")

        self.canvas.bind_all("<MouseWheel>", _on_mousewheel)
        self.add_bill()
        self.root.bind_all("<Return>", lambda event: self.add_bill().focus_set())
        self.root.bind_all("<Delete>", lambda event: self.delete_selected_line())
        self.root.bind_all("<Control-Delete>", lambda event: self.delete_last_bill())

    def import_bills(self):
        file_paths = filedialog.askopenfilenames(filetypes=[("Text Files", "*.txt")])
        if not file_paths:
            return

        self.remove_empty_bills()

        for file_path in file_paths:
            with open(file_path, 'r') as f:
                lines = [line.strip() for line in f if line.strip()]

            current = []
            for line in lines:
                if line.lower().startswith("end"):
                    self._add_bill_from_lines(current)
                    current = []
                else:
                    current.append(line)

    def _add_bill_from_lines(self, lines):
        if not lines:
            return

        bill_name = lines[0].lstrip("#").strip()
        total_line = lines[1].split()
        total_value = float(total_line[1])
        payer = total_line[2]

        tax = 0
        idx = 2
        if lines[2].lower().startswith("tax"):
            tax = float(lines[2].split()[1])
            idx = 3

        wrapper = tk.LabelFrame(self.bill_container, text=f"{bill_name}", padx=10, pady=10, bg="#f0f0f0")
        wrapper.pack(padx=10, pady=5, fill=tk.X)

        name_entry = ttk.Entry(wrapper, width=30)
        name_entry.insert(0, bill_name)
        name_entry.pack(pady=2)

        tax_entry = ttk.Entry(wrapper, width=10)
        tax_entry.insert(0, str(tax))
        tax_entry.pack(pady=2)

        payer_entry = ttk.Entry(wrapper, width=10)
        payer_entry.insert(0, payer)
        payer_entry.pack(pady=2)

        line_items = []

        for line in lines[idx:]:
            try:
                val, code = line.split()
                val = float(val)
            except:
                continue

            line_frame = tk.Frame(wrapper, bg="#f0f0f0", relief="solid", borderwidth=1)
            line_frame.pack(fill=tk.X, pady=2)

            amount = ttk.Entry(line_frame, width=10)
            code_entry = ttk.Entry(line_frame, width=10)

            amount.insert(0, str(val))
            code_entry.insert(0, code)

            amount.pack(side=tk.LEFT, padx=5)
            code_entry.pack(side=tk.LEFT, padx=5)

            def on_select(event, line=(amount, code_entry), lf=line_frame):
                self.selected_line = (lf, line)
                for b in self.bills:
                    for frame, _ in b["lines"]:
                        frame.config(bg="#f0f0f0", highlightbackground="#f0f0f0", highlightthickness=1)
                lf.config(highlightbackground="#4A90E2", highlightthickness=2)

            line_frame.bind("<Button-1>", on_select)
            amount.bind("<FocusIn>", on_select)
            code_entry.bind("<FocusIn>", on_select)

            line_items.append((line_frame, (amount, code_entry)))

        self.bills.append({
            "name": name_entry,
            "tax": tax_entry,
            "payer": payer_entry,
            "lines": line_items,
            "frame": wrapper
        })

    def remove_empty_bills(self):
        to_remove = []
        for bill in self.bills:
            is_empty = (
                    not bill["name"].get().strip()
                    and not bill["tax"].get().strip()
                    and not bill["payer"].get().strip()
                    and all(not line[1][0].get().strip() and not line[1][1].get().strip() for line in bill["lines"])
            )
            if is_empty:
                bill["frame"].destroy()
                to_remove.append(bill)
        for b in to_remove:
            self.bills.remove(b)

    def add_bill(self):
        wrapper = tk.LabelFrame(self.bill_container, text=f"Bill {len(self.bills)+1}", padx=10, pady=10, bg="#f0f0f0")
        wrapper.pack(padx=10, pady=5, fill=tk.X)

        name_frame = tk.Frame(wrapper, bg="#f0f0f0")
        name_frame.pack(pady=2, fill=tk.X)
        ttk.Label(name_frame, text="Bill Name").grid(row=0, column=0)
        name_entry = ttk.Entry(name_frame, width=30)
        name_entry.grid(row=0, column=1, columnspan=2)
        tax_frame = tk.Frame(wrapper, bg="#f0f0f0")
        tax_frame.pack(pady=2, fill=tk.X)

        ttk.Label(tax_frame, text="Tax").grid(row=0, column=0)
        tax_entry = ttk.Entry(tax_frame, width=10)
        tax_entry.grid(row=0, column=1)

        ttk.Label(tax_frame, text="Payer Initial").grid(row=0, column=2)
        payer_entry = ttk.Entry(tax_frame, width=10)
        payer_entry.grid(row=0, column=3)

        line_items = []
        ttk.Label(wrapper, text="⏎ Press Enter to add a new bill", font=("Segoe UI", 9, "italic"), foreground="#888", background="#f0f0f0").pack(pady=(4, 0), anchor="w", padx=5)

        def add_line(event=None):
            line_frame = tk.Frame(wrapper, bg="#f0f0f0", relief="solid", borderwidth=1)
            line_frame.pack(fill=tk.X, pady=2)

            amount = ttk.Entry(line_frame, width=10)
            code = ttk.Entry(line_frame, width=10)

            amount.pack(side=tk.LEFT, padx=5)
            code.pack(side=tk.LEFT, padx=5)

            def on_select(event, line=(amount, code)):
                self.selected_line = (line_frame, line)
                for b in self.bills:
                    for lf, _ in b['lines']:
                        lf.config(bg="#f0f0f0", highlightbackground="#f0f0f0", highlightthickness=1)
                line_frame.config(highlightbackground="#4A90E2", highlightthickness=2)

            line_frame.bind("<Button-1>", on_select)
            amount.bind("<FocusIn>", on_select)
            code.bind("<FocusIn>", on_select)

            def on_tab(event):
                new_amount, _ = add_line()
                new_amount.focus_set()
                return "break"

            code.bind("<Tab>", on_tab)
            self.root.update_idletasks()
            scroll_region = self.canvas.bbox("all")
            view_height = self.canvas.winfo_height()

            if scroll_region and scroll_region[3] > view_height:
                self.canvas.yview_moveto(1.0)
            line_items.append((line_frame, (amount, code)))
            return amount, code

        ttk.Label(wrapper, text="↹ Press Tab to add a new line", font=("Segoe UI", 9, "italic"), foreground="#888", background="#f0f0f0").pack(pady=(2, 0), anchor="w", padx=5)
        add_line()
        self.bills.append(
            {"name": name_entry, "tax": tax_entry, "payer": payer_entry, "lines": line_items, "frame": wrapper})
        return name_entry

    def delete_selected_line(self):
        if self.selected_line:
            frame, line = self.selected_line
            for bill in self.bills:
                if (frame, line) in bill["lines"]:
                    bill["lines"].remove((frame, line))
                    frame.destroy()
                    self.selected_line = None
                    if not bill["lines"]:
                        bill["frame"].destroy()
                        self.bills.remove(bill)
                    break

    def delete_last_bill(self):
        if self.bills:
            last_bill = self.bills.pop()
            last_bill["frame"].destroy()

    def calculate(self):
        self.total_owings = np.zeros((len(self.people), len(self.people)))
        self.receipt_data = []

        for bill in self.bills:
            payer_initial = bill["payer"].get().strip().lower()
            payer_matches = [p for p in self.people if p.lower().startswith(payer_initial)]
            if not payer_matches:
                continue
            payer = payer_matches[0]
            payer_idx = self.people.index(payer)
            bill_name = bill["name"].get().strip()

            self.receipt_data.append(f"--- {bill_name} ---\nPayer: {payer}\n")

            line_owings = np.zeros(len(self.people))
            for frame, (amount_entry, code_entry) in bill["lines"]:
                try:
                    val = float(amount_entry.get())
                    code = code_entry.get().strip()
                    split = self.codes.get(code, [0] * len(self.people))
                    line_owings += np.array(split) * val
                    self.receipt_data.append(f"{val:.2f} split as {code}\n")
                except ValueError:
                    continue

            try:
                tax = float(bill["tax"].get())
                line_owings += tax / len(self.people)
                self.receipt_data.append(f"Tax: {tax:.2f}\n")
            except ValueError:
                pass

            for i in range(len(self.people)):
                if i != payer_idx:
                    self.total_owings[payer_idx][i] += line_owings[i]

        result = ""
        for i in range(len(self.people)):
            for j in range(len(self.people)):
                if i != j and self.total_owings[i][j] > 0:
                    line = f"{self.people[j]} owes {self.people[i]} ${self.total_owings[i][j]:.2f}\n"
                    self.receipt_data.append(line)
                    result += line

        result += "\nNet Owing Matrix:\n"
        header = "{:>10}".format("") + "".join(["{:>10}".format(p) for p in self.people]) + "\n"
        result += header
        self.receipt_data.append("\nNet Owing Matrix:\n")
        self.receipt_data.append(header)
        for i in range(len(self.people)):
            row = "{:>10}".format(self.people[i])
            for j in range(len(self.people)):
                value = self.total_owings[j][i] - self.total_owings[i][j]
                row += "{:>10.2f}".format(value)
            result += row + "\n"
            self.receipt_data.append(row + "\n")
        result += "\nFinal Settlement Summary (Net Payments):\n"
        self.receipt_data.append("\nFinal Settlement Summary (Net Payments):\n")

        net = np.zeros((len(self.people), len(self.people)))
        for i in range(len(self.people)):
            for j in range(len(self.people)):
                net[i][j] = self.total_owings[i][j] - self.total_owings[j][i]

        for i in range(len(self.people)):
            for j in range(len(self.people)):
                if net[j][i] > 1e-2:
                    result += f"{self.people[i]} pays {self.people[j]} ${net[j][i]:.2f}\n"
                    self.receipt_data.append(f"{self.people[i]} pays {self.people[j]} ${net[j][i]:.2f}\n")

        messagebox.showinfo("Result", result.strip())


    def print_receipt(self):
        if not hasattr(self, 'receipt_data') or not self.receipt_data:
            messagebox.showwarning("No Data", "Please run Calculate first.")
            return
        filename = os.path.join(self.receipt_path, f"receipt_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt")
        with open(filename, 'w') as f:
            f.writelines(self.receipt_data)
        messagebox.showinfo("Receipt Saved", f"Receipt saved to {filename}")

    def open_settings(self):
        self.selected_code_row = None
        settings_window = tk.Toplevel(self.root)
        settings_window.title("Settings")
        settings_window.geometry("500x700")

        people_frame = tk.LabelFrame(settings_window, text="People")
        people_frame.pack(padx=10, pady=10, fill=tk.X)

        people_listbox = tk.Listbox(people_frame, selectmode=tk.SINGLE, height=5)
        for person in self.people:
            people_listbox.insert(tk.END, person)
        people_listbox.pack(side=tk.LEFT, padx=5)

        person_entry = ttk.Entry(people_frame)
        person_entry.pack(side=tk.LEFT, padx=5)

        def add_person():
            new_person = person_entry.get().strip()
            if new_person and new_person not in self.people:
                self.people.append(new_person)
                people_listbox.insert(tk.END, new_person)
                for code in self.codes:
                    self.codes[code].append(0)

        def remove_person():
            selected = people_listbox.curselection()
            if selected:
                idx = selected[0]
                person = self.people.pop(idx)
                people_listbox.delete(idx)
                for code in self.codes:
                    del self.codes[code][idx]

        ttk.Button(people_frame, text="Add", command=add_person).pack(side=tk.LEFT, padx=5)
        ttk.Button(people_frame, text="Remove", command=remove_person).pack(side=tk.LEFT, padx=5)

        self.code_entries = {}
        code_frame = tk.LabelFrame(settings_window, text="Splitting Codes")
        code_frame.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)

        def refresh_code_entries():
            for widget in code_frame.winfo_children():
                widget.destroy()

            self.selected_code_row = None
            row = 1
            for code in self.codes:
                row_frame = tk.Frame(code_frame, bg="#f0f0f0", highlightbackground="#f0f0f0", highlightthickness=2)
                row_frame.grid(row=row, column=0, columnspan=len(self.people) + 1, sticky="ew", pady=1)

                def on_select(event, selected_code=code, row_widget=row_frame):
                    self.selected_code_row = selected_code
                    for w in code_frame.winfo_children():
                        w.configure(bg="#f0f0f0", highlightbackground="#f0f0f0")
                    row_widget.configure(bg="#cce5ff", highlightbackground="#4A90E2")

                row_frame.bind("<Button-1>", on_select)

                label = ttk.Label(row_frame, text=code, width=8)
                label.grid(row=0, column=0, padx=5)
                label.bind("<Button-1>", on_select)

                for jdx in range(len(self.people)):
                    e = ttk.Entry(row_frame, width=5)
                    e.grid(row=0, column=jdx + 1, padx=2)
                    e.insert(0, str(self.codes[code][jdx]))
                    self.code_entries[(code, jdx)] = e
                    e.bind("<Button-1>", on_select)

                row += 1

        def add_code():
            code_name = code_entry.get().strip()
            if code_name and code_name not in self.codes:
                self.codes[code_name] = [0] * len(self.people)
                refresh_code_entries()

        code_entry = ttk.Entry(settings_window)
        code_entry.pack(pady=5)
        ttk.Button(settings_window, text="Add Code", command=add_code).pack(pady=5)

        refresh_code_entries()

        code_remove_frame = tk.Frame(settings_window)
        code_remove_frame.pack(pady=5)
        ttk.Button(settings_window, text="Delete Selected Code", command=lambda: remove_selected_code()).pack(pady=5)

        def remove_selected_code():
            if self.selected_code_row and self.selected_code_row in self.codes:
                del self.codes[self.selected_code_row]
                self.selected_code_row = None
                refresh_code_entries()


        def save_settings():
            config = configparser.ConfigParser()
            config['People'] = {'names': ",".join(self.people)}
            config['Codes'] = {}
            config['Settings'] = {'receipt_path': receipt_path_var.get()}
            for code in self.codes:
                split_values = []
                for j in range(len(self.people)):
                    entry = self.code_entries.get((code, j))
                    split_values.append(entry.get() if entry else "0")
                config['Codes'][code] = ",".join(split_values)
            with open(CONFIG_FILE, 'w') as f:
                config.write(f)

            messagebox.showinfo("Restart Required", "Settings saved. The app will now restart.")
            settings_window.destroy()
            self.root.destroy()

            python = sys.executable
            os.execl(python, python, *sys.argv)

        receipt_path_frame = tk.LabelFrame(settings_window, text="Receipt Save Path")
        receipt_path_frame.pack(padx=10, pady=10, fill=tk.X)

        receipt_path_var = tk.StringVar(value=self.receipt_path)
        receipt_entry = ttk.Entry(receipt_path_frame, textvariable=receipt_path_var, width=50)
        receipt_entry.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)

        def browse_folder():
            path = filedialog.askdirectory(initialdir=self.receipt_path)
            if path:
                receipt_path_var.set(path)

        ttk.Button(receipt_path_frame, text="Browse", command=browse_folder).pack(side=tk.LEFT, padx=5)

        ttk.Button(settings_window, text="Save", command=save_settings).pack(pady=10)

    def load_config(self):
        config = configparser.ConfigParser()
        config.read(CONFIG_FILE)
        if 'People' in config:
            self.people = config['People']['names'].split(',')
        if 'Codes' in config:
            for code in config['Codes']:
                values = list(map(float, config['Codes'][code].split(",")))
                self.codes[code] = values
        if 'Settings' in config:
            self.receipt_path = config['Settings'].get('receipt_path', os.getcwd())

if __name__ == '__main__':
    root = tk.Tk()
    app = BillSplitterApp(root)
    root.mainloop()