import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from libgen_api import LibgenSearch
import requests
from bs4 import BeautifulSoup
import re
#FALLBACK_URL = "https://libgen.is"
FALLBACK_URL = "https://libgen.st"
#FALLBACK_URL = "https://librarygenesis.net"
#FALLBACK_URL = "https://libgen.rs"
#FALLBACK_URL = "https://libgen.li"
#FALLBACK_URL = "https://libgen.gs"
#FALLBACK_URL = "https://libgen.vg"
#FALLBACK_URL = "https://libgen.la"
#FALLBACK_URL = "https://libgen.bz"
class BookDownloader:
    def __init__(self, root):
        self.root = root
        self.root.title("Book Downloader")
        self.root.geometry("900x700")
        self.results = []
        self.searcher = LibgenSearch()

        self.root.configure(bg="#2e2e2e")
        style = ttk.Style(root)
        style.theme_use("clam")
        style.configure(".", background="#2e2e2e", foreground="white", font=("Segoe UI", 10))
        style.configure("TEntry", fieldbackground="#444", insertcolor="white")
        style.configure("TButton", background="#00b894", foreground="white", padding=6, font=("Segoe UI", 10, "bold"))
        style.map("TButton", background=[("active", "#00997a")])

        tk.Label(root, text="Enter Book Title / Author:", bg="#2e2e2e", fg="white").pack(pady=5)
        self.query = tk.StringVar()
        ttk.Entry(root, textvariable=self.query, width=90).pack(pady=5)

        self.source_choice = tk.StringVar(value="api")
        radio_frame = tk.Frame(root, bg="#2e2e2e")
        radio_frame.pack(pady=5)
        tk.Label(radio_frame, text="Select Source:", bg="#2e2e2e", fg="white").pack(side="left", padx=(0, 10))
        ttk.Radiobutton(radio_frame, text="libgen-api", variable=self.source_choice, value="api").pack(side="left", padx=10)
        ttk.Radiobutton(radio_frame, text="libgen (Scrape)", variable=self.source_choice, value="url").pack(side="left", padx=10)
        ttk.Button(root, text="Search", command=self.search).pack(pady=5)#
        frame = tk.Frame(root, bg="#2e2e2e")
        frame.pack(expand=True, fill="both", pady=10)
        self.listbox = tk.Listbox(frame, bg="#1e1e1e", fg="white", selectbackground="#555", width=120, height=25)
        self.listbox.pack(side="left", fill="both", expand=True)
        self.listbox.bind("<<ListboxSelect>>", lambda e: self.btn.config(state="normal"))
        sb = tk.Scrollbar(frame, command=self.listbox.yview)
        sb.pack(side="right", fill="y")
        self.listbox.config(yscrollcommand=sb.set)

        tk.Label(root, text="Select a book and click Download", bg="#2e2e2e", fg="white", font=("Segoe UI", 9, "italic")).pack()
        self.btn = ttk.Button(root, text="Download", command=self.download, state="disabled")
        self.btn.pack(pady=10)

    def search(self):
        q = self.query.get().strip()
        self.listbox.delete(0, tk.END)
        self.results.clear()
        self.btn.config(state="disabled")
        if not q:
            return messagebox.showwarning("Input Error", "Enter a search query.")

        source = self.source_choice.get()
        if source == "api":
            try:
                results = self.searcher.search_title(q)
                for book in results:
                    if book.get("Extension", "").lower() != "pdf":
                        continue
                    title = book.get("Title", "Unknown")
                    author = book.get("Author", "Unknown")
                    size = book.get("Filesize", "N/A")
                    mirrors = self.searcher.resolve_download_links(book)
                    if mirrors.get("GET"):
                        self.results.append((f"{title} - {author}.pdf", mirrors["GET"]))
                        self.listbox.insert(tk.END, f"▶ {title} by {author} [{size}]")
            except Exception as e:
                messagebox.showerror("API Error", str(e))
        else:
            try:
                url = f"{FALLBACK_URL}/search.php?req={q.replace(' ', '+')}&res=100&view=simple&phrase=1&column=def"
                r = requests.get(url, timeout=15)
                soup = BeautifulSoup(r.text, "html.parser")
                table = soup.find("table", class_="c")
                if not table:
                    return self.listbox.insert(tk.END, "No results found.")

                for row in table.find_all("tr")[1:]:
                    cols = row.find_all("td")
                    if len(cols) < 10 or cols[8].text.lower() != "pdf":
                        continue
                    title = cols[2].text.strip()
                    author = cols[1].text.strip()
                    size = cols[7].text.strip()
                    href = cols[9].find("a").get("href")
                    self.results.append((f"{title} - {author}.pdf", href))
                    self.listbox.insert(tk.END, f"▶ {title} by {author} [{size}]")
            except Exception as e:
                messagebox.showerror("Web Error", str(e))
        if not self.results:
            self.listbox.insert(tk.END, "No results found.")
    def download(self):
        idx = self.listbox.curselection()
        if not idx:
            return
        name, url = self.results[idx[0]]
        safe_name = re.sub(r'[<>:"/\\|?*]', '', name)[:100]
        path = filedialog.asksaveasfilename(initialfile=safe_name, defaultextension=".pdf")
        if not path:
            return
        try:
            if "libgen.rs" in url:
                soup = BeautifulSoup(requests.get(url, timeout=15).text, "html.parser")
                get_link = soup.find("a", text="GET")
                if not get_link:
                    return messagebox.showerror("Error", "GET link not found.")
                url = get_link.get("href")
                if not url.startswith("http"):
                    url = FALLBACK_URL + "/" + url.lstrip("/")
            with requests.get(url, stream=True, timeout=30) as r, open(path, "wb") as f:
                for chunk in r.iter_content(8192):
                    f.write(chunk)
            messagebox.showinfo("Success", f"Saved to:\n{path}")
        except Exception as e:
            messagebox.showerror("Download Error", str(e))
if __name__ == "__main__":
    root = tk.Tk()
    BookDownloader(root)
    root.mainloop()